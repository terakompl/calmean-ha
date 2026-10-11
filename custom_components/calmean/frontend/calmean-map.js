/* CALMEAN Map — no CDN scripts; map tiles © OpenStreetMap contributors. */
const TILE = 256, MAX_LAT = 85.05112878;
const PALETTE = ['#176cba', '#ad427e', '#248369', '#af661f', '#6e56ac', '#b44444'];
const project = (lat, lon, zoom) => {
  const size = TILE * 2 ** zoom;
  const clamped = Math.max(-MAX_LAT, Math.min(MAX_LAT, lat));
  const sine = Math.sin(clamped * Math.PI / 180);
  return [(lon + 180) / 360 * size, (0.5 - Math.log((1 + sine) / (1 - sine)) / (4 * Math.PI)) * size];
};
const unproject = (x, y, zoom) => {
  const size = TILE * 2 ** zoom;
  return [Math.max(-MAX_LAT, Math.min(MAX_LAT, Math.atan(Math.sinh(Math.PI * (1 - 2 * y / size))) * 180 / Math.PI)), ((x / size * 360) % 360 + 360) % 360 - 180];
};
const validPosition = d => Number.isFinite(d.latitude) && Number.isFinite(d.longitude);
const keyOf = d => JSON.stringify([d.entry_id, d.id]);
// randomUUID is HTTPS-only; local HA commonly runs over HTTP.
const newZoneId = () => {
  if (typeof globalThis.crypto?.randomUUID === 'function') return globalThis.crypto.randomUUID();
  const bytes = new Uint8Array(16);
  globalThis.crypto.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 15) | 64;
  bytes[8] = (bytes[8] & 63) | 128;
  const hex = Array.from(bytes, value => value.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
};
const svgNode = (name, attributes) => {
  const el = document.createElementNS('http://www.w3.org/2000/svg', name);
  for (const [key, value] of Object.entries(attributes)) el.setAttribute(key, String(value));
  return el;
};

class CalmeanMapPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode: 'open'});
    this.devices = []; this.selected = ''; this.center = [0, 0]; this.zoom = 2;
    this.tiles = new Map(); this.draft = null; this.fitted = false; this.failedTiles = new Set();
    this.shadowRoot.innerHTML = `
      <style>
        :host{display:block;height:100%;color:var(--primary-text-color,#202b38);background:var(--primary-background-color,#f4f6f8);font:15px system-ui,sans-serif}
        *{box-sizing:border-box}button,input,select{font:inherit}button{cursor:pointer}button:disabled{cursor:default;opacity:.55}
        header{display:flex;align-items:center;gap:14px;padding:12px 18px;background:var(--card-background-color,white);border-bottom:1px solid var(--divider-color,#ddd)}
        header h1{font-size:21px;margin:0;flex:1}header button{border:0;background:transparent;padding:8px;color:inherit}
        .layout{display:grid;grid-template-columns:330px 1fr;height:calc(100% - 63px);min-height:550px}
        aside{padding:18px;overflow:auto;background:var(--card-background-color,white);border-right:1px solid var(--divider-color,#ddd)}
        label{display:block;font-size:13px;margin:12px 0 5px}input,select{width:100%;padding:10px;border:1px solid var(--divider-color,#bac6d0);border-radius:8px;background:var(--card-background-color,white);color:inherit}
        h2{font-size:17px;margin:22px 0 10px}.muted{color:var(--secondary-text-color,#647486);font-size:13px;line-height:1.5}.notice{margin:10px 0;color:var(--primary-color,#176cba);font-size:13px;min-height:20px}
        .stats{margin:16px 0;padding:12px;border-radius:10px;background:var(--secondary-background-color,#eef3f7);line-height:1.8;white-space:pre-line}
        .zone{padding:12px 0;border-bottom:1px solid var(--divider-color,#eee)}.zone strong{display:block}.actions{display:flex;gap:8px;margin-top:10px}
        .btn{border:1px solid var(--divider-color,#bbc6d0);background:var(--card-background-color,white);color:inherit;border-radius:8px;padding:9px 12px}
        .primary{background:var(--primary-color,#176cba);color:white;border:0}.danger{color:#be3b3b}.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
        form{margin-top:16px;border-top:2px solid var(--primary-color,#176cba);padding-top:10px}[hidden]{display:none!important}
        .map{position:relative;overflow:hidden;background:#dfe6ed;touch-action:none;min-height:450px;outline:none}
        .tiles,.overlay{position:absolute;inset:0;pointer-events:none}.tiles img{position:absolute;width:256px;height:256px;user-select:none}.overlay{width:100%;height:100%}
        .controls{position:absolute;right:16px;top:16px;display:grid;gap:7px;z-index:2}.controls button{min-width:44px;min-height:44px;border:0;border-radius:8px;background:var(--card-background-color,white);color:var(--primary-text-color,#202b38);box-shadow:0 2px 8px #0002}
        .hint{position:absolute;left:16px;top:16px;max-width:65%;background:var(--card-background-color,white);color:var(--primary-text-color,#202b38);padding:10px 13px;border-radius:8px;pointer-events:none;font-size:13px;box-shadow:0 2px 8px #0002}
        .map-error{position:absolute;bottom:42px;left:16px;right:16px;background:#fff3dc;color:#5b3c0b;padding:10px 12px;border-radius:8px;font-size:13px;pointer-events:none;z-index:3}.attribution{position:absolute;bottom:0;right:0;background:#ffffffe6;color:#222;padding:4px 8px;font-size:11px}.attribution a{color:#176cba}
        .scale{position:absolute;bottom:22px;left:16px;background:#ffffffe6;color:#222;font-size:11px;padding:3px 7px;border-bottom:3px solid #222;pointer-events:none}
        @media(max-width:800px){.layout{display:flex;flex-direction:column;height:auto;min-height:0}aside{order:2;border:0}.map{order:1;height:55vh;min-height:350px}header h1{font-size:18px}:host{overflow:auto}aside{overflow:visible}}
      </style>
      <header><button id="menu" aria-label="Otwórz menu">☰</button><h1>Mapa CALMEAN</h1><button id="refresh">Odśwież</button></header>
      <div class="layout"><aside>
        <label for="device">Urządzenie</label><select id="device"><option value="">Wszystkie zegarki</option></select>
        <div id="stats" class="stats">Ładowanie urządzeń…</div>
        <p class="muted">Ostatnia pozycja z CALMEAN. Promień strefy nie jest dokładnością pomiaru GPS.</p>
        <h2>Strefy urządzenia</h2><div id="zones"></div>
        <button id="add" class="btn primary">+ Dodaj strefę</button>
        <div id="notice" class="notice" role="status" aria-live="polite"></div>
        <form id="editor" hidden>
          <h2 id="editorTitle">Nowa strefa</h2>
          <label for="name">Nazwa strefy</label><input id="name" required maxlength="80" placeholder="np. Dom, Szkoła, Dziadkowie">
          <label for="kind">Typ strefy</label><select id="kind"><option value="custom">Własna lokalizacja</option><option value="home">Dom</option><option value="school">Szkoła</option></select>
          <div class="row"><div><label for="latitude">Szerokość</label><input id="latitude" type="number" step="any" min="-90" max="90" required></div><div><label for="longitude">Długość</label><input id="longitude" type="number" step="any" min="-180" max="180" required></div></div>
          <label for="radius">Promień (metry)</label><input id="radius" type="number" step="1" min="50" max="5000" value="50" required>
          <p class="muted">Kliknij punkt na mapie albo wpisz współrzędne. Przy nakładaniu stref wygrywa pierwsza na liście.</p>
          <div class="actions"><button id="save" class="btn primary" type="submit">Zapisz strefę</button><button id="cancel" class="btn" type="button">Anuluj</button></div>
        </form>
      </aside><div id="map" class="map" tabindex="0" role="region" aria-label="Mapa lokalizacji zegarków; użyj strzałek do przesuwania, plusa i minusa do zmiany powiększenia">
        <div class="tiles"></div><svg class="overlay"></svg>
        <div class="hint" id="hint">Przesuwaj mapę. Wybierz zegarek, aby edytować jego strefy.</div>
        <div class="controls"><button id="plus" aria-label="Powiększ">+</button><button id="minus" aria-label="Pomniejsz">−</button><button id="fit" aria-label="Pokaż wszystkie wybrane lokalizacje">◎</button></div>
        <div id="mapError" class="map-error" role="status" hidden></div><div class="scale" id="scale"></div>
        <div class="attribution">© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors</div>
      </div></div>`;
    this.$('menu').onclick = () => this.dispatchEvent(new Event('hass-toggle-menu', {bubbles:true, composed:true}));
    this.$('refresh').onclick = () => this.refresh();
    this.$('device').onchange = e => {this.selected=e.target.value; this.cancel(); this.renderDetails(); this.fit();};
    this.$('add').onclick = () => this.editZone(null);
    this.$('cancel').onclick = () => this.cancel();
    this.$('editor').onsubmit = e => {e.preventDefault(); this.save();};
    for (const id of ['name','kind','latitude','longitude','radius']) this.$(id).oninput = () => {this.readDraft(); this.draw();};
    this.$('kind').onchange = () => {
      if (!this.$('name').value.trim()) this.$('name').value = {home:'Dom',school:'Szkoła'}[this.$('kind').value] || '';
      this.readDraft(); this.draw();
    };
    this.$('plus').onclick = () => this.changeZoom(1);
    this.$('minus').onclick = () => this.changeZoom(-1);
    this.$('fit').onclick = () => this.fit();
    this.setupMapEvents();
  }
  $(id) {return this.shadowRoot.getElementById(id);}
  set hass(value) {
    this._hass=value;
    if(!this.initialCenterSet) {
      const home=value?.states?.['zone.home']?.attributes;
      if(home && validPosition(home)) {this.center=[home.latitude,home.longitude];this.zoom=14;this.initialCenterSet=true;this.draw();}
    }
    if(this.isConnected && !this.loaded && !this.loading) this.refresh();
  }
  get hass() {return this._hass;}
  connectedCallback() {
    if (this._hass) this.refresh();
    this.timer=setInterval(() => {if(!document.hidden) this.refresh();},15000);
    this.observer=new ResizeObserver(() => this.draw()); this.observer.observe(this.$('map'));
    this.draw();
  }
  disconnectedCallback() {clearInterval(this.timer);this.observer?.disconnect();}
  current() {return this.devices.find(d => keyOf(d)===this.selected);}
  visible() {const current=this.current(); return current ? [current] : this.devices;}
  notice(message) {this.$('notice').textContent=message;}
  async refresh() {
    if(!this._hass || this.loading || this.saving) return;
    this.loading=true; this.$('refresh').disabled=true;
    try {
      const data=await this._hass.callWS({type:'calmean/map'});
      this.devices=data.devices; this.loaded=true;
      // Keep an open editor's revision so simultaneous changes cause a conflict.
      const select=this.$('device'); select.replaceChildren(new Option('Wszystkie zegarki',''));
      for(const d of this.devices) select.add(new Option(d.name,keyOf(d)));
      if(this.selected && !this.current()) {this.selected='';this.cancel();}
      select.value=this.selected;
      this.renderDetails();
      if(!this.fitted && this.devices.some(validPosition)) {this.fit();this.fitted=true;}
      else this.draw();
    } catch(error) {this.notice('Nie można wczytać mapy. Sprawdź połączenie z HA i uprawnienia administratora.');}
    finally {this.loading=false;this.$('refresh').disabled=false;}
  }
  renderDetails() {
    const d=this.current(), stats=this.$('stats');
    if(!d) stats.textContent=this.devices.length ? `${this.devices.length} urządzeń · wybierz zegarek z listy lub kliknij jego pinezkę.` : 'Brak urządzeń. Sprawdź integrację CALMEAN.';
    else {
      const time=d.updated_at ? new Date(d.updated_at).toLocaleString() : 'brak danych';
      stats.textContent=`${d.name}\nMiejsce: ${d.place || 'nieznane'}\nBateria: ${d.battery ?? '—'}${d.battery==null ? '' : '%'}\nOstatnia lokalizacja: ${time}\nTyp: ${d.localization_type ?? '—'}${validPosition(d) ? '' : '\nBrak współrzędnych z API — zegarek nie ma pinezki.'}${d.available ? '' : '\nAPI niedostępne — wyświetlana ostatnia pozycja'}`;
    }
    this.$('add').disabled=!d || Boolean(this.draft) || this.saving;
    const list=this.$('zones'); list.replaceChildren();
    if(!d) {const p=document.createElement('p');p.className='muted';p.textContent='Wybierz urządzenie, aby zobaczyć i zmienić jego strefy.';list.append(p);return;}
    if(!d.zones.length) {const p=document.createElement('p');p.className='muted';p.textContent='Brak stref. Dodaj pierwszą lokalizację.';list.append(p);}
    d.zones.forEach((zone,index) => {
      const row=document.createElement('div');row.className='zone';
      const title=document.createElement('strong');title.textContent=zone.name;
      const info=document.createElement('span');info.className='muted';info.textContent=`Promień ${zone.radius} m · ${zone.latitude.toFixed(5)}, ${zone.longitude.toFixed(5)}`;
      const actions=document.createElement('div');actions.className='actions';
      for(const [label, action, style] of [
        ['Edytuj',()=>this.editZone(zone),''],
        ['Usuń',()=>this.removeZone(zone),'danger'],
        ...(index>0 ? [['↑',()=>this.reorder(index),'']] : []),
      ]) {const button=document.createElement('button');button.className=`btn ${style}`;button.textContent=label;button.disabled=Boolean(this.draft)||this.saving;button.onclick=action;actions.append(button);}
      row.append(title,info,actions);list.append(row);
    });
  }
  editZone(zone) {
    const device=this.current();if(!device) return;
    this.editRevision=device.revision;
    this.editZones=structuredClone(device.zones);
    this.draft=zone ? {...zone} : {id:newZoneId(),name:'',kind:'custom',latitude:validPosition(device)?device.latitude:null,longitude:validPosition(device)?device.longitude:null,radius:50};
    this.$('editor').hidden=false;this.$('editorTitle').textContent=zone ? 'Edytuj strefę' : 'Nowa strefa';
    for(const id of ['name','kind','latitude','longitude','radius']) this.$(id).value=this.draft[id] ?? '';
    this.$('hint').textContent='Kliknij mapę, aby ustawić pinezkę strefy.';
    this.notice(validPosition(device) ? '' : 'Zegarek nie podał współrzędnych. Możesz niezależnie ustawić strefę kliknięciem mapy lub ręcznie.');this.renderDetails();
    if(validPosition(this.draft)) {this.center=[this.draft.latitude,this.draft.longitude];this.zoom=17;}
    this.draw();this.$('editor').scrollIntoView({block:'nearest'});
  }
  readDraft() {
    if(!this.draft) return;
    this.draft.name=this.$('name').value.trim();this.draft.kind=this.$('kind').value;
    for(const id of ['latitude','longitude','radius']) this.draft[id]=this.$(id).value==='' ? null : Number(this.$(id).value);
  }
  cancel() {
    this.draft=null;this.$('editor').hidden=true;
    this.$('hint').textContent='Przesuwaj mapę. Wybierz zegarek, aby edytować jego strefy.';
    this.renderDetails();this.draw();
  }
  async persist(zones, revision) {
    const d=this.current(); if(!d || this.saving) return false;
    this.saving=true;this.$('save').disabled=true;this.$('cancel').disabled=true;this.$('device').disabled=true;
    this.renderDetails();
    try {
      const result=await this._hass.callWS({type:'calmean/zones/save',entry_id:d.entry_id,device_id:d.id,zones,revision});
      d.zones=zones;d.revision=result.revision;
      this.notice('Strefy zapisane.'); return true;
    } catch(error) {
      this.notice(error.code==='conflict' ? 'Strefy zmieniono w innym oknie. Anuluj edycję, odśwież i spróbuj ponownie.' : 'Nie zapisano. Sprawdź unikalne nazwy, współrzędne i promień 50–5000 m.');
      return false;
    } finally {
      this.saving=false;this.$('save').disabled=false;this.$('cancel').disabled=false;this.$('device').disabled=false;this.renderDetails();
    }
  }
  async save() {
    this.readDraft();if(!this.draft) return;
    if(!validPosition(this.draft) || !this.draft.name || this.draft.radius<50 || this.draft.radius>5000) {this.notice('Uzupełnij nazwę, punkt i promień 50–5000 m.');return;}
    const zones=structuredClone(this.editZones),index=zones.findIndex(z=>z.id===this.draft.id);
    if(index<0) zones.push({...this.draft});else zones[index]={...this.draft};
    if(await this.persist(zones,this.editRevision)) {this.cancel();await this.refresh();}
  }
  async removeZone(zone) {
    const d=this.current(); if(!d || !window.confirm(`Usunąć strefę „${zone.name}” z urządzenia „${d.name}”?`)) return;
    if(await this.persist(d.zones.filter(z=>z.id!==zone.id),d.revision)) {await this.refresh();this.draw();}
  }
  async reorder(index) {
    const d=this.current();if(!d) return;
    const zones=structuredClone(d.zones);[zones[index-1],zones[index]]=[zones[index],zones[index-1]];
    if(await this.persist(zones,d.revision)) {await this.refresh();this.draw();}
  }
  bounds() {const rect=this.$('map').getBoundingClientRect();return [rect.width,rect.height];}
  screen(lat,lon) {
    const [width,height]=this.bounds(),[cx,cy]=project(...this.center,this.zoom),[x,y]=project(lat,lon,this.zoom),size=TILE*2**this.zoom;
    const dx=((x-cx+size/2)%size+size)%size-size/2;
    return [width/2+dx,height/2+y-cy];
  }
  clickPosition(event) {
    if(!this.draft) return;
    const rect=this.$('map').getBoundingClientRect(),[cx,cy]=project(...this.center,this.zoom);
    const [lat,lon]=unproject(cx+event.clientX-rect.left-rect.width/2,cy+event.clientY-rect.top-rect.height/2,this.zoom);
    this.$('latitude').value=lat.toFixed(7);this.$('longitude').value=lon.toFixed(7);this.readDraft();this.draw();
  }
  setupMapEvents() {
    const map=this.$('map');this.pointers=new Map();
    map.addEventListener('pointerdown',e=>{
      if(e.target.closest('button,a') || (!this.draft && e.target.closest('g[role="button"]'))) return;
      this.pointers.set(e.pointerId,[e.clientX,e.clientY]);map.setPointerCapture(e.pointerId);
      if(this.pointers.size===1) this.drag={start:[e.clientX,e.clientY],point:[e.clientX,e.clientY],center:project(...this.center,this.zoom),moved:false};
      if(this.pointers.size===2){this.drag.moved=true;this.pinch=this.pointerDistance();}
    });
    map.addEventListener('pointermove',e=>{
      if(!this.pointers.has(e.pointerId)) return;
      this.pointers.set(e.pointerId,[e.clientX,e.clientY]);
      if(this.pointers.size===2){const distance=this.pointerDistance();if(distance>this.pinch*1.5){this.changeZoom(1);this.pinch=distance;}else if(distance<this.pinch/1.5){this.changeZoom(-1);this.pinch=distance;}return;}
      if(!this.drag) return;
      const dx=e.clientX-this.drag.start[0],dy=e.clientY-this.drag.start[1];
      if(Math.hypot(dx,dy)>5) this.drag.moved=true;
      this.center=unproject(this.drag.center[0]-dx,this.drag.center[1]-dy,this.zoom);this.draw();
    });
    const finish=(e,cancel=false)=>{
      if(!this.pointers.has(e.pointerId)) return;
      const wasSingle=this.pointers.size===1,moved=this.drag?.moved;
      this.pointers.delete(e.pointerId);
      if(!cancel && wasSingle && !moved && !e.target.closest('button,a')) this.clickPosition(e);
      if(this.pointers.size===1){const point=[...this.pointers.values()][0];this.drag={start:point,center:project(...this.center,this.zoom),moved:true};}
      else if(!this.pointers.size) this.drag=null;
    };
    map.addEventListener('pointerup',e=>finish(e));map.addEventListener('pointercancel',e=>finish(e,true));
    map.addEventListener('wheel',e=>{e.preventDefault();this.changeZoom(e.deltaY<0?1:-1);},{passive:false});
    map.addEventListener('keydown',e=>{
      if(e.target!==map) return;
      if(['+','=','-'].includes(e.key)){e.preventDefault();this.changeZoom(e.key==='-'?-1:1);return;}
      const offsets={ArrowLeft:[-80,0],ArrowRight:[80,0],ArrowUp:[0,-80],ArrowDown:[0,80]};
      if(offsets[e.key]){e.preventDefault();const [x,y]=project(...this.center,this.zoom),[dx,dy]=offsets[e.key];this.center=unproject(x+dx,y+dy,this.zoom);this.draw();}
    });
  }
  pointerDistance() {const [a,b]=[...this.pointers.values()];return Math.hypot(a[0]-b[0],a[1]-b[1]);}
  changeZoom(delta) {this.zoom=Math.max(2,Math.min(19,this.zoom+delta));this.draw();}
  fit() {
    const points=this.visible().flatMap(d=>[...(validPosition(d)?[d]:[]),...d.zones]);
    if(!points.length){this.draw();return;}
    const lats=points.map(p=>p.latitude),lons=points.map(p=>p.longitude);
    this.center=[(Math.min(...lats)+Math.max(...lats))/2,(Math.min(...lons)+Math.max(...lons))/2];
    const [width,height]=this.bounds();this.zoom=16;
    for(let z=16;z>=2;z--){
      const pixel=points.map(p=>project(p.latitude,p.longitude,z));
      const padding=80;
      if(Math.max(...pixel.map(p=>p[0]))-Math.min(...pixel.map(p=>p[0]))<width-padding && Math.max(...pixel.map(p=>p[1]))-Math.min(...pixel.map(p=>p[1]))<height-padding){this.zoom=z;break;}
      this.zoom=z;
    }
    this.draw();
  }
  draw() {
    const [width,height]=this.bounds();if(!width||!height) return;
    const [cx,cy]=project(...this.center,this.zoom),left=cx-width/2,top=cy-height/2,n=2**this.zoom;
    const layer=this.shadowRoot.querySelector('.tiles'),needed=new Set();
    for(let x=Math.floor(left/TILE);x<=Math.floor((left+width)/TILE);x++) for(let y=Math.floor(top/TILE);y<=Math.floor((top+height)/TILE);y++){
      if(y<0||y>=n) continue;
      const key=`${this.zoom}/${x}/${y}`;needed.add(key);
      let img=this.tiles.get(key);
      if(!img){
        img=document.createElement('img');img.alt='';img.draggable=false;
        // Override HA's restrictive document policy using the actual page origin.
        // No fabricated Referer, proxy or changes to the CALMEAN token.
        img.referrerPolicy='strict-origin-when-cross-origin';
        img.onerror=()=>{if(this.tiles.get(key)===img){this.failedTiles.add(key);this.updateTileStatus();}};
        img.onload=()=>{this.failedTiles.delete(key);this.updateTileStatus();};
        this.tiles.set(key,img);
        img.src=`https://tile.openstreetmap.org/${this.zoom}/${((x%n)+n)%n}/${y}.png`;
        layer.append(img);
      }
      img.style.transform=`translate(${x*TILE-left}px,${y*TILE-top}px)`;
    }
    for(const [key,img] of this.tiles) if(!needed.has(key)){img.remove();this.tiles.delete(key);this.failedTiles.delete(key);}
    this.updateTileStatus();
    const svg=this.shadowRoot.querySelector('.overlay');svg.replaceChildren();svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
    const metresPerPixel=40075016.686*Math.cos(this.center[0]*Math.PI/180)/(TILE*2**this.zoom);
    this.$('scale').textContent=`100 m`;this.$('scale').style.width=`${Math.max(35,Math.min(200,100/metresPerPixel))}px`;
    // Match the label to the actual displayed ruler width, including clamped zoom levels.
    const scaleWidth=Math.max(35,Math.min(200,100/metresPerPixel));this.$('scale').textContent=`${Math.round(scaleWidth*metresPerPixel)} m`;
    for(const d of this.visible()){
      const color=PALETTE[this.devices.findIndex(item=>keyOf(item)===keyOf(d))%PALETTE.length];
      for(const zone of d.zones) this.drawZone(svg,zone,color,false);
      if(validPosition(d)){
        const [x,y]=this.screen(d.latitude,d.longitude);
        const marker=svgNode('g',{'pointer-events':'auto',cursor:'pointer',tabindex:0,role:'button','aria-label':`Wybierz ${d.name}`});
        const circle=svgNode('circle',{cx:x,cy:y,r:12,fill:color,stroke:'white','stroke-width':3,opacity:d.available?1:.55});
        const title=svgNode('title',{});title.textContent=`${d.name} · ${d.place || 'nieznane'}`;
        const text=svgNode('text',{x:x+17,y:y+5,fill:'#16283b','font-size':14,'font-weight':600,stroke:'white','stroke-width':4,'paint-order':'stroke'});text.textContent=d.name;
        marker.append(circle,title,text);
        const select=()=>{if(this.draft||this.saving)return;this.selected=keyOf(d);this.$('device').value=this.selected;this.renderDetails();this.draw();};
        marker.onclick=select;marker.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}};svg.append(marker);
      }
    }
    if(this.draft && validPosition(this.draft)) this.drawZone(svg,this.draft,'#e88718',true);
  }
  updateTileStatus() {
    const error=this.$('mapError');
    error.hidden=this.failedTiles.size===0;
    error.textContent=this.failedTiles.size ? 'Nie udało się wczytać części tła mapy. Punkty i edytor nadal działają; współrzędne można wpisać ręcznie.' : '';
  }
  drawZone(svg,zone,color,draft) {
    const [x,y]=this.screen(zone.latitude,zone.longitude);
    const resolution=40075016.686*Math.cos(Math.max(-MAX_LAT,Math.min(MAX_LAT,zone.latitude))*Math.PI/180)/(TILE*2**this.zoom);
    const circle=svgNode('circle',{cx:x,cy:y,r:zone.radius/resolution,fill:color,'fill-opacity':.12,stroke:color,'stroke-width':2,...(draft?{'stroke-dasharray':'5 4'}:{})});
    const pin=svgNode('circle',{cx:x,cy:y,r:4,fill:color});
    const text=svgNode('text',{x:x+8,y:y-9,fill:color,'font-size':13,stroke:'white','stroke-width':3,'paint-order':'stroke'});text.textContent=`${zone.name || 'Nowa strefa'} · ${zone.radius} m`;
    svg.append(circle,pin,text);
  }
}
if(!customElements.get('calmean-map-panel')) customElements.define('calmean-map-panel',CalmeanMapPanel);
