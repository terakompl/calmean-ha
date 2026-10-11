/* DOM test harness, not a full HA server or visual browser test. */
const {JSDOM}=require('jsdom');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {randomUUID}=require('node:crypto');
(async()=>{
  const dom=new JSDOM('<!doctype html><body></body>',{url:'http://homeassistant.example.invalid',runScripts:'outside-only',pretendToBeVisual:true});
  const w=dom.window;
  w.structuredClone=structuredClone;
  Object.defineProperty(w.crypto,'randomUUID',{value:undefined});
  w.ResizeObserver=class{observe(){}disconnect(){}};
  w.HTMLElement.prototype.scrollIntoView=function(){};
  w.HTMLElement.prototype.setPointerCapture=function(){};
  w.HTMLElement.prototype.getBoundingClientRect=function(){return {left:330,top:63,width:1000,height:700};};
  w.confirm=()=>true;
  w.eval(fs.readFileSync(path.join(__dirname,'../../custom_components/calmean/frontend/calmean-map.js'),'utf8'));
  const devices=[
    {entry_id:'synthetic',id:'watch-a',name:'Zegarek A',latitude:0,longitude:0,battery:75,active:true,available:true,updated_at:'2026-01-01T00:00:00Z',place:'Dom',revision:0,zones:[{id:'home',name:'Dom',kind:'home',latitude:0,longitude:0,radius:50}]},
    {entry_id:'synthetic',id:'watch-b',name:'Zegarek B',latitude:.005,longitude:.01,battery:42,active:true,available:true,updated_at:null,place:'Szkoła',revision:0,zones:[{id:'school',name:'Szkoła',kind:'school',latitude:.005,longitude:.01,radius:100}]},
  ];
  const commands=[];
  const panel=w.document.createElement('calmean-map-panel');
  panel.hass={callWS:async msg=>{
    commands.push(structuredClone(msg));
    if(msg.type==='calmean/map')return {devices:structuredClone(devices)};
    const device=devices.find(d=>d.id===msg.device_id);
    if(msg.revision!==device.revision)throw {code:'conflict'};
    device.zones=structuredClone(msg.zones);
    for(const d of devices)d.revision++;
    return {revision:device.revision};
  }};
  w.document.body.append(panel);
  // Wait for the initial async websocket snapshot.
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(panel.devices.length,2);
  assert.equal(panel.shadowRoot.querySelector('.tiles img').referrerPolicy,'strict-origin-when-cross-origin');
  panel.$('device').value=JSON.stringify(['synthetic','watch-a']);
  panel.$('device').dispatchEvent(new w.Event('change'));
  assert.match(panel.$('stats').textContent,/Zegarek A/);
  panel.$('add').click();assert.equal(panel.$('radius').value,'50');
  assert.match(panel.draft.id,/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/);
  panel.$('name').value='Dziadkowie';
  // Clicking a displayed point must preserve its geographic coordinates.
  for(const center of [[52,17],[0,0],[-33,151],[10,-179.9],[10,179.9]]) {
    panel.center=center;panel.zoom=17;
    panel.clickPosition({clientX:830,clientY:413});
    assert.ok(Math.abs(panel.draft.latitude-center[0])<1e-6);
    assert.ok(Math.abs(panel.draft.longitude-center[1])<1e-6);
    const point=[center[0]+0.0001,center[1]+0.0001];
    const [x,y]=panel.screen(...point);
    panel.clickPosition({clientX:330+x,clientY:63+y});
    assert.ok(Math.abs(panel.draft.latitude-point[0])<1e-6);
    assert.ok(Math.abs(panel.draft.longitude-point[1])<1e-6);
  }
  panel.center=[0,0];

  panel.clickPosition({clientX:930,clientY:413});
  panel.readDraft();assert.ok(Number.isFinite(panel.draft.longitude));
  const originalRadius=panel.shadowRoot.querySelector('circle[stroke-dasharray]').getAttribute('r');
  panel.$('radius').value='100';panel.readDraft();panel.draw();
  assert.ok(Math.abs(Number(panel.shadowRoot.querySelector('circle[stroke-dasharray]').getAttribute('r'))/Number(originalRadius)-2)<1e-10);
  panel.$('radius').value='49';await panel.save();assert.equal(commands.filter(c=>c.type==='calmean/zones/save').length,0);
  panel.$('radius').value='50';await panel.save();
  assert.equal(devices[0].zones.length,2);assert.equal(devices[1].zones.length,1);
  panel.editZone(panel.current().zones[1]);panel.$('radius').value='100';await panel.save();
  assert.equal(devices[0].zones[1].radius,100);
  await panel.reorder(1);assert.equal(devices[0].zones[0].name,'Dziadkowie');
  panel.editZone(panel.current().zones[0]);for(const d of devices)d.revision++;
  await panel.save();assert.match(panel.$('notice').textContent,/innym oknie/);assert.ok(panel.draft);
  panel.cancel();await panel.refresh();await panel.removeZone(panel.current().zones[0]);
  assert.equal(devices[0].zones.length,1);
  panel.selected='';panel.renderDetails();panel.draw();
  panel.shadowRoot.querySelectorAll('g[role="button"]')[1].dispatchEvent(new w.Event('click'));
  assert.match(panel.$('stats').textContent,/Zegarek B/);
  devices[1].name='<img src=x onerror=alert(1)>';await panel.refresh();
  assert.equal(panel.shadowRoot.querySelectorAll('aside img').length,0);
  assert.match(panel.$('stats').textContent,/<img/);
  // Failed API availability is reported without pretending it is current.
  devices[1].available=false;await panel.refresh();assert.match(panel.$('stats').textContent,/API niedostępne/);
  // Tiles are retained across redraws, not re-requested on every snapshot.
  const tile=panel.shadowRoot.querySelector('.tiles img');panel.draw();
  assert.equal(panel.shadowRoot.querySelector('.tiles img'),tile);
  tile.dispatchEvent(new w.Event('error'));
  assert.equal(panel.$('mapError').hidden,false);
  tile.dispatchEvent(new w.Event('load'));
  assert.equal(panel.$('mapError').hidden,true);
  devices[1].latitude=null;devices[1].longitude=null;
  await panel.refresh();assert.match(panel.$('stats').textContent,/Brak współrzędnych/);
  panel.$('add').click();assert.equal(panel.$('editor').hidden,false);
  panel.$('name').value='Strefa bez GPS';
  panel.$('latitude').value='1';panel.$('longitude').value='1';
  await panel.save();assert.equal(devices[1].zones.at(-1).name,'Strefa bez GPS');
  panel.remove();dom.window.close();
  console.log('Frontend DOM tests passed: device selection, map pin, 50 m radius, circle scaling, independent save, edit, priority, conflicts, delete, escaped names, availability, tile reuse, HTTP UUID fallback, Referer policy, tile failure, editing without GPS.');
})().catch(error=>{console.error(error);process.exit(1);});
