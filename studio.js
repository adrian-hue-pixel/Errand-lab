import * as THREE from './vendor/three/three.module.js';
import { GLTFLoader } from './vendor/three/GLTFLoader.js';
const $=id=>document.getElementById(id);
const stage=$('stage'),canvas=$('world'),film=$('film'),status=$('studio-status');
const cfg=JSON.parse(stage.dataset.assets);
const track=await fetch('/models/route.json').then(response=>response.json());
const total=track.distance.at(-1);
let p=0,playing=false,last=0,mode='live',renderer,scene,camera,rig,ready=false,phi=.6,elevation=.68,zoom=8,sky,mascot;
function point(progress){
  const distance=progress*total;
  let i=1;while(i<track.distance.length-1 && track.distance[i]<distance)i++;
  const a=track.points[i-1],b=track.points[i],f=(distance-track.distance[i-1])/(track.distance[i]-track.distance[i-1]||1);
  return [a[0]+f*(b[0]-a[0]),a[1]+f*(b[1]-a[1]),Math.atan2(b[0]-a[0],b[1]-a[1])];
}
function travel(){const t=Math.min(1,p/.84);return t*t*(3-2*t);}
function paint(){
  $('scrub').value=Math.round(p*1000);
  $('distance').textContent=(total*travel()).toFixed(1)+' m';
  const duration=mode==='film' && Number.isFinite(film.duration)?film.duration:track.duration;
  $('eta').textContent=Math.ceil((1-p)*duration)+' s';
  $('waypoint').textContent=track.stops.find(stop=>stop.at>travel()+.001)?.name || 'Arrived';
  if(!renderer || !ready || mode!=='live')return;
  const [x,z,angle]=point(travel());
  rig.position.set(x,1.417,z);rig.rotation.y=angle;
  mascot.rotation.y=.65+.10*Math.sin(p*Math.PI*2);
  camera.position.set(x+zoom*Math.cos(elevation)*Math.sin(phi),2.25+zoom*Math.sin(elevation),z+zoom*Math.cos(elevation)*Math.cos(phi));
  camera.lookAt(x,2.35,z);sky.position.copy(camera.position);renderer.render(scene,camera);
}
let recorder=null;
function stop(){if(recorder?.state==='recording')recorder.stop();playing=false;$('play').textContent=p>=1?'Replay':'Play route';film.pause();}
function tick(time){
  if(!playing || mode!=='live')return;
  if(last) p=Math.min(1,p+(time-last)/1000/track.duration);last=time;paint();
  if(p<1)requestAnimationFrame(tick);else stop();
}
function switchMode(next){
  stop();mode=next;canvas.hidden=next!=='live';film.hidden=next!=='film';
  $('mode-live').setAttribute('aria-pressed',String(next==='live'));$('mode-film').setAttribute('aria-pressed',String(next==='film'));
  $('play').disabled=$('scrub').disabled=next==='live'?!ready:!cfg.video;
  for(const id of ['orbit','zoom-in','zoom-out']) $(id).disabled=next!=='live'||!ready;
  if(next==='film' && Number.isFinite(film.duration))film.currentTime=p*film.duration;
  status.textContent=next==='film'?(cfg.video?'Recorded route · Cinema mode':'The recorded route will appear here when the film is added.'):(ready?'Drag to orbit. Scroll to zoom.':'Waiting for the town, vehicle and Capi models.');
  paint();
}
$('mode-live').onclick=()=>switchMode('live');$('mode-film').onclick=()=>switchMode('film');
if(cfg.video){film.src=cfg.video;film.onloadedmetadata=()=>{if(mode==='film')film.currentTime=p*film.duration;};}
film.ontimeupdate=()=>{if(mode==='film' && Number.isFinite(film.duration)){p=film.currentTime/film.duration;paint();}};
film.onended=()=>{p=1;stop();paint();};film.onerror=()=>{stop();status.textContent='The recording could not play in this browser.';};
$('play').onclick=async()=>{
  if(playing){stop();return;}
  if(p>=.999)p=0;
  playing=true;last=0;$('play').textContent='Pause';
  if(mode==='film'){try{film.currentTime=p*film.duration || 0; await film.play();}catch{stop();status.textContent='Playback is unavailable.';}}
  else requestAnimationFrame(tick);
};
$('scrub').oninput=e=>{p=Number(e.target.value)/1000;if(mode==='film'&&Number.isFinite(film.duration))film.currentTime=p*film.duration;paint();};
$('orbit').onclick=()=>{phi+=.35;paint();};
function magnify(f){zoom=THREE.MathUtils.clamp(zoom*f,3,20);paint();}
$('zoom-in').onclick=()=>magnify(.85);$('zoom-out').onclick=()=>magnify(1.15);
canvas.onwheel=e=>{e.preventDefault();magnify(Math.exp(Math.sign(e.deltaY)*.09));};
let drag=null;canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);};
canvas.onpointermove=e=>{if(!drag)return;phi-=(e.clientX-drag[0])*.009;elevation=THREE.MathUtils.clamp(elevation+(e.clientY-drag[1])*.007,.15,1.45);drag=[e.clientX,e.clientY];paint();};
canvas.onpointerup=canvas.onpointercancel=()=>{drag=null;};
switchMode(cfg.video?'film':'live');
if(cfg.models){
  try{
    renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});
    renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;
    scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(40,1,.1,400);
    scene.add(new THREE.HemisphereLight(0xffffff,0x718780,2));
    const sun=new THREE.DirectionalLight(0xffead4,2.5);sun.position.set(12,32,8);scene.add(sun);
    const loader=new GLTFLoader();
    const [town,van,capi,dome]=await Promise.all(['town','vehicle','capi','sky'].map(name=>loader.loadAsync('/models/'+name+'.glb')));
    sky=dome.scene;sky.scale.setScalar(.004);sky.traverse(o=>{if(o.isMesh){const map=o.material.emissiveMap || o.material.map;o.material=new THREE.MeshBasicMaterial({map,side:THREE.DoubleSide,depthWrite:false});o.renderOrder=-10;}});scene.add(sky);
    town.scene.scale.setScalar(.0254);town.scene.traverse(o=>{if(!o.isMesh)return;const m=o.material;if(['M0_0_0_44','M0_0_0_45'].includes(m.name)){m.transparent=false;m.alphaTest=0;m.polygonOffset=true;m.polygonOffsetFactor=-2;m.polygonOffsetUnits=-2;}if(m.name==='proxy_2'){m.color.setHex(0x303238);m.polygonOffset=true;m.polygonOffsetFactor=2;m.polygonOffsetUnits=3;}});
    van.scene.scale.setScalar(64);scene.add(town.scene);rig=new THREE.Group();rig.add(van.scene);
    mascot=capi.scene;mascot.scale.setScalar(.68);mascot.position.set(-19.9,1.475+.544*.68,31.05);scene.add(mascot,rig);
    const curve=track.points.map(([x,z])=>new THREE.Vector3(x,1.432,z));
    scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(curve),new THREE.LineBasicMaterial({color:0xf0af55})));
    for(const stop of track.stops){const mark=new THREE.Mesh(new THREE.CylinderGeometry(.42,.42,.16,24),new THREE.MeshStandardMaterial({color:0x78cab1}));mark.position.set(stop.x,1.44,stop.z);scene.add(mark);}
    ready=true;new ResizeObserver(()=>{const w=stage.clientWidth,h=stage.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();paint();}).observe(stage);
    if(mode==='live')switchMode('live');
    const record=$('record-route');
    const codec=window.MediaRecorder && ['video/webm;codecs=vp9','video/webm;codecs=vp8','video/mp4'].find(type=>MediaRecorder.isTypeSupported(type));
    if(codec && canvas.captureStream){
      record.hidden=false;
      record.onclick=()=>{
        if(recorder?.state==='recording')return;
        switchMode('live');p=0;paint();
        const capture=canvas.captureStream(30);
        const chunks=[];
        try {recorder=new MediaRecorder(capture,{mimeType:codec,videoBitsPerSecond:8000000});}
        catch {capture.getTracks().forEach(t=>t.stop());status.textContent='Recording is unavailable in this browser.';return;}
        recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
        recorder.onstop=()=>{
          capture.getTracks().forEach(t=>t.stop());record.disabled=false;
          if(!chunks.length){status.textContent='No frames were recorded.';return;}
          const url=URL.createObjectURL(new Blob(chunks,{type:codec}));
          const link=document.createElement('a');link.href=url;link.download=codec.includes('mp4')?'sample-route.mp4':'sample-route.webm';link.click();
          setTimeout(()=>URL.revokeObjectURL(url),30000);status.textContent='Recording exported. Place the downloaded file in media/ for Cinema mode.';
        };
        record.disabled=true;recorder.start();status.textContent='Recording the route…';$('play').click();
      };
    }
  } catch {switchMode(cfg.video?'film':'live');status.textContent='The model or WebGL renderer could not load. Check the GLB files or open Cinema.';}
}
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
