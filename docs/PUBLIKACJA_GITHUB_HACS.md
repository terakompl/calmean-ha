# Publikacja na GitHub i instalacja przez HACS

Projekt można udostępnić każdemu przez publiczny GitHub. Użytkownicy dodają adres repozytorium ręcznie w HACS; nie wymaga to przyjęcia projektu do domyślnego katalogu HACS.

## 1. Przygotuj dane właściciela

W `custom_components/calmean/manifest.json` zamień `terakompl` w adresach documentation i issue_tracker na swój login GitHub. Ustaw codeowners na `["@terakompl"]`. Dla repozytorium organizacji codeowner powinien wskazywać rzeczywistego opiekuna.

Można zrobić to skryptem z katalogu projektu:

```sh
python scripts/prepare_repository.py terakompl --repository calmean-ha
```

Nie wpisuj do żadnego pliku tokenu CALMEAN. Użytkownicy podają własny token dopiero w HA.

## 2. Utwórz publiczne repozytorium

1. Zaloguj się na https://github.com.
2. Wybierz **+ → New repository**.
3. Nazwa: **calmean-ha**. Widoczność: **Public**.
4. Opis: `Nieoficjalna integracja CALMEAN dla Home Assistant: lokalizacja zegarków, mapa i indywidualne strefy.`
5. Nie generuj dodatkowego README ani licencji — są już w paczce.
6. Kliknij **Create repository**, następnie **uploading an existing file** lub **Add file → Upload files**.
7. Rozpakuj paczkę i wgraj **zawartość katalogu calmean-ha**, nie sam ZIP ani nadrzędny katalog calmean-ha.
8. Zapisz pliki przez **Commit changes**. Sprawdź, że został wgrany także katalog `.github`.

W katalogu głównym repozytorium muszą być od razu widoczne:

```text
README.md
LICENSE
hacs.json
custom_components/calmean/manifest.json
custom_components/calmean/brand/icon.png
custom_components/calmean/frontend/calmean-map.js
.github/workflows/validate.yml
docs/
scripts/
tests/
```

W ustawieniach repozytorium włącz **Issues**. Dodaj tematy: `home-assistant`, `hacs`, `calmean`, `device-tracker`, `custom-integration`. Nie publikuj plików HA .storage, kopii zapasowych, nagłówków Authorization ani rzeczywistych danych lokalizacji.

## 3. Sprawdź walidację i utwórz wydanie

Otwórz **Actions → Validate**. Testy Python i frontend, hassfest oraz HACS powinny przejść. Sprawdź ewentualne błędy przed zaproszeniem użytkowników; nie wyłączaj sprawdzania tylko po to, aby uzyskać zielony wynik.

Następnie **Releases → Draft a new release**:

- Tag: `v0.2.3`, wskazujący sprawdzony commit.
- Tytuł: `CALMEAN 0.2.3 — beta`.
- Opis: funkcje, ograniczenia bety, instrukcja tokenu i wymagania HA.
- Opublikuj pełne wydanie. Załącznik ZIP nie jest wymagany do zwykłej instalacji HACS.

Wydania są zalecane do aktualizacji i wyboru wersji; bez wydania HACS może korzystać z domyślnej gałęzi. Numer w manifest.json powinien odpowiadać wydaniu. Jeśli oznaczysz wydanie jako prerelease, może wymagać od użytkownika włączenia pokazywania wersji beta w HACS.

## 4. Instrukcja dla użytkowników

1. Otwórz **HACS** w Home Assistant.
2. Menu **⋮ → Niestandardowe repozytoria / Custom repositories**.
3. Wpisz `https://github.com/terakompl/calmean-ha`.
4. Typ: **Integracja / Integration**, następnie **Dodaj / Add**.
5. Wróć do HACS, znajdź **CALMEAN** i pobierz integrację.
6. Uruchom ponownie Home Assistant; odśwież przeglądarkę Ctrl + F5.
7. **Ustawienia → Urządzenia i usługi → Dodaj integrację → CALMEAN**.
8. Wklej własny token uzyskany przez panel.calmean.com → F12 → Network → getAllDevice → Headers → Request Headers → authorization.
9. Jako administrator otwórz **Mapa CALMEAN**, wybierz zegarek i ustaw jego strefy.

Przy wcześniejszej instalacji ręcznej wykonaj kopię zapasową i pobierz przez HACS do tego samego katalogu integracji. Nie usuwaj wpisu konta w Urządzeniach i usługach podczas aktualizacji.

## Źródła wymagań

- https://www.hacs.xyz/docs/faq/custom_repositories/
- https://www.hacs.xyz/docs/publish/integration/
- https://www.hacs.xyz/docs/publish/start/
- https://www.hacs.xyz/docs/publish/action/
- https://developers.home-assistant.io/docs/core/integration/brand_images/

Ikona w paczce jest własną ikoną społecznościowego projektu, a nie oficjalnym logo CALMEAN. Lokalne ikony integracji są obsługiwane przez HA od 2026.3; starsza wersja HA może pokazać ikonę ogólną.


## Parser 0.2.3

Odpowiedź deviceView: współrzędne, typ i czas są odczytywane z localization. Bateria jest przeliczana z ułamka 0–1 na procenty. Wpisy DEVICE_PARENT / PARENT_APP są pomijane. Brak localization oznacza brak pozycji; lastActivityDate nie zastępuje czasu lokalizacji. Mapa pokazuje ostatnią pozycję API, bez wymuszania nowego odczytu zegarka.
