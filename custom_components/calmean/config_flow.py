"""UI setup, reauthentication and geofence options."""
try:
    import probatio as vol
except ImportError:
    import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector
from .api import CalmeanClient, InvalidAuth, CannotConnect
from .const import DOMAIN, DEFAULT_INTERVAL
from .models import InvalidResponse, validate_zone

TOKEN_SCHEMA = vol.Schema({vol.Required("token"): selector.TextSelector(selector.TextSelectorConfig(type="password"))})

async def validate_token(hass, token):
    token = token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token or any(c.isspace() for c in token):
        raise InvalidAuth("Invalid token")
    await CalmeanClient(async_get_clientsession(hass), token).devices()
    return token

class CalmeanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                token = await validate_token(self.hass, user_input["token"])
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidResponse:
                errors["base"] = "unsupported_response"
            else:
                # One account per installation until an account identifier is verified.
                if self._async_current_entries():
                    return self.async_abort(reason="single_instance_allowed")
                return self.async_create_entry(title="CALMEAN", data={"token": token})
        return self.async_show_form(step_id="user", data_schema=TOKEN_SCHEMA, errors=errors)

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                token = await validate_token(self.hass, user_input["token"])
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidResponse:
                errors["base"] = "unsupported_response"
            else:
                return self.async_update_reload_and_abort(self._get_reauth_entry(), data_updates={"token": token})
        return self.async_show_form(step_id="reauth_confirm", data_schema=TOKEN_SCHEMA, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CalmeanOptionsFlow()

class CalmeanOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            options = dict(self.config_entry.options)
            options["interval"] = user_input["interval"]
            return self.async_create_entry(title="", data=options)
        return self.async_show_form(step_id="init", data_schema=vol.Schema({
            vol.Required("interval", default=self.config_entry.options.get("interval", DEFAULT_INTERVAL)):
                vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
        }))
