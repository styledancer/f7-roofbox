# Builds the experimental graphics version (app_gfx/index.html) from the main app: newer three.js (r160),
# HDR environments, post-processing, sand texture, richer materials and models.
import sys,re
SRC='/tmp/claude-0/-home-claude/9371c78e-d13a-5b57-ac13-2f71dd22ff25/scratchpad/app/index.html'
DST='/tmp/claude-0/-home-claude/9371c78e-d13a-5b57-ac13-2f71dd22ff25/scratchpad/app_gfx/index.html'
s=open(SRC,encoding='utf-8').read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)==cnt,(a[:100],s.count(a)); s=s.replace(a,b)
# ---- 6. three.js r160 as ES modules, exposed as the old global THREE so the app code stays the same ----
rep("""<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script>
(function(){""","""<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
<script>
window.__main=function(){
(function(){""")
rep("""kick();
})();

</script>""","""kick();
})();
};
</script>
<script type="module">
import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RGBELoader} from 'three/addons/loaders/RGBELoader.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {GTAOPass} from 'three/addons/postprocessing/GTAOPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {ShaderPass} from 'three/addons/postprocessing/ShaderPass.js';
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';
T.ColorManagement.enabled=false;   // keep the app's own colour handling (it converts palette colours itself)
window.THREE=Object.assign({},T,{OrbitControls,GLTFLoader,RGBELoader,EffectComposer,RenderPass,GTAOPass,UnrealBloomPass,OutputPass,ShaderPass,RoundedBoxGeometry});
window.__main();
</script>""")
rep("outputEncoding=THREE.sRGBEncoding","outputColorSpace=THREE.SRGBColorSpace")
s=s.replace(".encoding=THREE.sRGBEncoding",".colorSpace=THREE.SRGBColorSpace")
rep("renderer.toneMapping=THREE.ACESFilmicToneMapping;","renderer.useLegacyLights=true; renderer.toneMapping=THREE.ACESFilmicToneMapping;")
rep("  renderer.toneMappingExposure=BASE.exp*(1-0.3*c.night)*(1-0.06*gd);","  renderer.toneMappingExposure=BASE.exp*(1-0.3*c.night)*(1-0.06*gd)*(GFX.q==='high'?0.78:1);")
# ---- quality setting ----
rep("const S = {","""const GFX={q:store.get('gfxQ','high')};   // 'high': HDR light, ambient occlusion, bloom; 'eco': plain render
const S = {""")
# ---- 1. real HDR environments: daylight quarry, sunrise beach, moonless night ----
rep("scene.environment=studioEnv();","""scene.environment=studioEnv();
const HDR={day:null, sun:null, night:null};
// sky dome: the upper half of the HDR panorama (real clouds), fading into the horizon colour so no foreign landscape shows
const SKY=(()=>{ const u={tex:{value:null}, k:{value:1}, hor:{value:new THREE.Color(0.8,0.85,0.9)}};
  const m=new THREE.Mesh(new THREE.SphereGeometry(92,48,24),new THREE.ShaderMaterial({uniforms:u, side:THREE.BackSide, depthWrite:false, fog:false,
    vertexShader:'varying vec3 vD; void main(){ vD=position; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
    fragmentShader:'uniform sampler2D tex; uniform float k; uniform vec3 hor; varying vec3 vD; void main(){ vec3 d=normalize(vD); vec2 uv=vec2(atan(d.z,d.x)*0.15915+0.5, asin(clamp(d.y,-1.0,1.0))*0.31831+0.5); vec3 c=texture2D(tex,uv).rgb*k; float t=smoothstep(0.02,0.22,d.y); gl_FragColor=vec4(mix(hor,c,t),1.0); }'}));
  m.renderOrder=-2; m.frustumCulled=false; m.visible=false; scene.add(m); return {mesh:m,u}; })();
[['day','hdr/quarry_01_1k.hdr'],['sun','hdr/blouberg_sunrise_2_1k.hdr'],['night','hdr/moonless_golf_1k.hdr']].forEach(([k,u])=>{
  new THREE.RGBELoader().load(u,t=>{ t.mapping=THREE.EquirectangularReflectionMapping; const pm=new THREE.PMREMGenerator(renderer);
    HDR[k]={bg:t, env:pm.fromEquirectangular(t).texture}; pm.dispose(); if(typeof applyWeatherScene==='function'&&wxReady) applyWeatherScene(); kick(); }); });""")
rep("  scene.fog=new THREE.Fog(sky, 20-14*c.fog","""  // HDR sky and light when it fits the weather: real reflections in paint and glass, real clouds overhead
  { const clear=c.cloud<0.7&&c.fog<0.3&&c.rain<0.3&&c.snow<0.3, h=c.night>0.6?HDR.night:(gd>0.35?HDR.sun:HDR.day);
    SKY.mesh.visible=false;
    if(GFX.q==='high'&&h){ scene.environment=h.env; if(false&&(clear||c.night>0.6)){ SKY.mesh.visible=true; SKY.u.tex.value=h.bg; SKY.u.k.value=(c.night>0.6?1.6:(gd>0.35?1.1:3.2))*(1-0.4*c.cloud); SKY.u.hor.value.copy(sky); } }
    else scene.environment=STUDIO_ENV; }
  scene.fog=new THREE.Fog(sky, 20-14*c.fog""")
rep("scene.environment=studioEnv();\n","const STUDIO_ENV=studioEnv(); scene.environment=STUDIO_ENV;\n")
# ---- 2. post-processing: ambient occlusion, bloom on bright highlights, gentle vignette ----
rep("let boxOnly=false;\nfunction render(){","""let boxOnly=false;
const POST=(()=>{ try{
  const rt=new THREE.WebGLRenderTarget(4,4,{type:THREE.HalfFloatType, samples:4});
  const comp=new THREE.EffectComposer(renderer,rt), rp=new THREE.RenderPass(scene,camera);
  const ao=new THREE.GTAOPass(scene,camera,4,4); ao.blendIntensity=0.85;
  ao.updateGtaoMaterial({radius:0.45, distanceExponent:1.4, thickness:1.2, scale:1.0, samples:12});
  const bloom=new THREE.UnrealBloomPass(new THREE.Vector2(4,4),0.16,0.35,3.0), out=new THREE.OutputPass();
  const vig=new THREE.ShaderPass({uniforms:{tDiffuse:{value:null},k:{value:0.28}},
    vertexShader:'varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
    fragmentShader:'uniform sampler2D tDiffuse; uniform float k; varying vec2 vUv; void main(){ vec4 c=texture2D(tDiffuse,vUv); vec2 d=vUv-0.5; float v=1.0-k*smoothstep(0.25,0.85,dot(d,d)*2.2); c.rgb*=v; c.rgb=mix(vec3(dot(c.rgb,vec3(0.299,0.587,0.114))),c.rgb,1.06); gl_FragColor=c; }'});
  const aoR=ao.render.bind(ao); ao.render=function(){ const hid=[]; scene.traverse(o=>{ if(o.visible&&(o.isSprite||o.isPoints||o.isLine||(o.material&&(o.material.transparent||o.material.isShaderMaterial)))){ o.visible=false; hid.push(o); } }); try{ aoR(...arguments); } finally{ hid.forEach(o=>o.visible=true); } };
  [rp,ao,bloom,out,vig].forEach(p=>comp.addPass(p));
  return {comp,ao,bloom,size(w,h){ const pr=Math.min(window.devicePixelRatio||1,1.6); comp.setPixelRatio(pr); comp.setSize(w,h); ao.setSize(w*pr,h*pr); }};
}catch(e){ console.warn('post-processing off',e); return null; } })();
function drawScene(){ if(GFX.q==='high'&&POST) POST.comp.render(); else renderer.render(scene,camera); }
function render(){""")
rep("  if(!boxOnly){ renderer.render(scene,camera); return; }","  if(typeof SKY!=='undefined') SKY.mesh.position.copy(camera.position);\n  if(!boxOnly){ drawScene(); return; }")
rep("  renderer.setSize(r.width,r.height,false); camera.aspect=","  renderer.setSize(r.width,r.height,false); if(POST) POST.size(r.width,r.height); camera.aspect=")
# ---- 3. sand: fine grain and ripples on the ground (texture follows the ground while driving) ----
rep("const terrain=new THREE.Mesh(terGeo,terMat);","""const SAND=(()=>{ const N=512, cv=document.createElement('canvas'); cv.width=cv.height=N; const g=cv.getContext('2d'), im=g.createImageData(N,N), h=new Float32Array(N*N);
  let a=24680; const r=()=>{ a=(a*16807)%2147483647; return a/2147483647; };
  for(let y=0;y<N;y++) for(let x=0;x<N;x++){ const rip=0.5+0.5*Math.sin((x*0.11+Math.sin(y*0.021)*9+y*0.035)); h[y*N+x]=0.55*rip+0.45*r(); }
  const nv=document.createElement('canvas'); nv.width=nv.height=N; const ng=nv.getContext('2d'), ni=ng.createImageData(N,N);
  for(let y=0;y<N;y++) for(let x=0;x<N;x++){ const i=y*N+x, H=(xx,yy)=>h[((yy+N)%N)*N+((xx+N)%N)], dx=H(x+1,y)-H(x-1,y), dy=H(x,y+1)-H(x,y-1);
    const nx=-dx*1.2, ny=-dy*1.2, nz=1, l=Math.hypot(nx,ny,nz), k=i*4; ni.data[k]=(nx/l*0.5+0.5)*255; ni.data[k+1]=(ny/l*0.5+0.5)*255; ni.data[k+2]=(nz/l*0.5+0.5)*255; ni.data[k+3]=255;
    const v=Math.round(255*(0.86+0.14*h[i])); im.data[k]=im.data[k+1]=im.data[k+2]=v; im.data[k+3]=255; }
  g.putImageData(im,0,0); ng.putImageData(ni,0,0);
  const mk=c=>{ const t=new THREE.CanvasTexture(c); t.wrapS=t.wrapT=THREE.RepeatWrapping; t.repeat.set(22,24); t.anisotropy=4; return t; };
  return {map:mk(cv), normal:mk(nv)}; })();
if(GFX.q==='high'){ terMat.map=SAND.map; terMat.normalMap=SAND.normal; terMat.normalScale=new THREE.Vector2(0.55,0.55); terMat.needsUpdate=true; }
const terrain=new THREE.Mesh(terGeo,terMat);""")
rep("  dist+=speed*dt; wheelAng+=speed*dt/M(CAR.wheelR);","  dist+=speed*dt; wheelAng+=speed*dt/M(CAR.wheelR); if(SAND){ SAND.map.offset.x=SAND.normal.offset.x=-dist/TER.W*22; }")
# ---- 5. car: metallic flakes in the paint, slightly tinted glass ----
rep("function paintFinish(m){","""const FLAKE=(()=>{ const N=256, c=document.createElement('canvas'); c.width=c.height=N; const g=c.getContext('2d'), im=g.createImageData(N,N); let a=13579; const r=()=>{ a=(a*16807)%2147483647; return a/2147483647; };
  for(let i=0;i<N*N;i++){ const k=i*4, s=r()<0.35; im.data[k]=s?Math.round(128+(r()-0.5)*120):128; im.data[k+1]=s?Math.round(128+(r()-0.5)*120):128; im.data[k+2]=255; im.data[k+3]=255; }
  g.putImageData(im,0,0); const t=new THREE.CanvasTexture(c); t.wrapS=t.wrapT=THREE.RepeatWrapping; t.repeat.set(40,40); return t; })();
function paintFinish(m){ if(GFX.q==='high'&&m.uv!==false){ m.normalMap=FLAKE; m.normalScale=new THREE.Vector2(0.06,0.06); }""")
rep("  glass:new THREE.MeshPhysicalMaterial({color:0x0b1016,","  glass:new THREE.MeshPhysicalMaterial({color:0x0a1310,")
# ---- 4. items: rounded edges ----
rep("  const box=(l,h,w,mat,x,y,z)=>add(new THREE.BoxGeometry(l,h,w),mat,x,y,z);",
    "  const box=(l,h,w,mat,x,y,z)=>add(Math.min(l,h,w)>0.04?new THREE.RoundedBoxGeometry(l,h,w,3,Math.min(0.025,Math.min(l,h,w)*0.18)):new THREE.BoxGeometry(l,h,w),mat,x,y,z);")
# ---- 5b. person: smoother, capsule limbs ----
rep("function pLimb(r1,r2,len,mat){ const g=new THREE.Group(), m=new THREE.Mesh(new THREE.CylinderGeometry(r1,r2,len,12),mat);",
    "function pLimb(r1,r2,len,mat){ const g=new THREE.Group(), m=new THREE.Mesh(new THREE.CapsuleGeometry((r1+r2)/2,Math.max(0.01,len-(r1+r2)),6,14),mat);")
# ---- quality switch in Settings ----
rep('          <div class="row"><label>Цвет машины</label><div class="colors" id="colors"></div></div>',
    '''          <div class="row"><label>Цвет машины</label><div class="colors" id="colors"></div></div>
          <div class="row"><label for="gfxQ">Графика (тестовая сборка)</label><select id="gfxQ"><option value="high">Высокая</option><option value="eco">Экономия батареи</option></select></div>''')
rep("function setTab(t){","""$('gfxQ').value=GFX.q; $('gfxQ').addEventListener('change',e=>{ store.set('gfxQ',e.target.value); location.reload(); });
function setTab(t){""")
# see-through objects confuse the ambient-occlusion pass: in high mode the figure fades out by shrinking its visibility window instead of going milky
rep("  person.visible=al>0.03; person.traverse(o=>{ if(o.isMesh) o.castShadow=al>0.5; });","  person.visible=GFX.q==='high'?al>0.5:al>0.03; if(GFX.q==='high') [pBody,pCloth,pBag].forEach(m=>{ if(m.transparent){ m.transparent=false; m.needsUpdate=true; } m.opacity=1; m.depthWrite=true; }); person.traverse(o=>{ if(o.isMesh) o.castShadow=al>0.5; });")
rep('<h1 class="pghead">Настройки</h1>','<h1 class="pghead">Настройки <span style="font:600 .7rem var(--mono);color:var(--accent);vertical-align:middle">GFX</span></h1>')

# ================= developer mode: live sliders for the look, saved on the phone and exportable as JSON =================
rep("const S = {","""// defaults tuned by the user on the phone (17 Oct 2026); previous factory values are kept in tools/dev_presets.json
const DEV_DEF={exp:1, tm:'aces', sun:1.47, hemi:1.87, fill:1.68, env:1, sky:1, ao:0.85, aoR:0.45, bloom:0.1, bloomT:4.1, bloomR:1, vig:0.37, sat:1.06,
  night:0.6, paintMet:1, paintRough:0.63, flake:0.06, coat:1, glassOp:0.78, sandN:2, sandB:1.4, shadow:3.5, fog:1, fov:11, scale:1.5};
const DEV=Object.assign({},DEV_DEF,store.get('devGfx',{})); let devOn=store.get('devOn',false);
const S = {""")
# lights, exposure, sky and reflections take the developer multipliers
rep("sun.intensity=BASE.sun*(1-0.75*c.cloud)*(1-0.9*c.night)*(1-0.2*gd); fill.intensity=BASE.fill*(1-0.6*c.night);",
    "sun.intensity=BASE.sun*DEV.sun*(1-0.75*c.cloud)*(1-0.9*c.night)*(1-0.2*gd); fill.intensity=BASE.fill*DEV.fill*(1-0.6*c.night);")
rep("  hemi.intensity=BASE.hemi*(1+0.6*c.cloud)*(1-0.55*c.night);","  hemi.intensity=BASE.hemi*DEV.hemi*(1+0.6*c.cloud)*(1-0.55*c.night)*(1+2.2*DEV.night*(GFX.q==='high'?1:0.35)*c.night);")
rep("  const envK=(1-0.88*c.night)*(1-0.35*c.cloud);","  const envK=(1-0.88*c.night*(1-0.55*DEV.night*(GFX.q==='high'?1:0.35)))*(1-0.35*c.cloud)*DEV.env;")
rep("*(GFX.q==='high'?0.78:1);","*(GFX.q==='high'?0.78:1)*DEV.exp*(1+0.7*DEV.night*(GFX.q==='high'?1:0.35)*c.night); renderer.toneMapping={aces:THREE.ACESFilmicToneMapping,agx:THREE.AgXToneMapping,reinhard:THREE.ReinhardToneMapping,cineon:THREE.CineonToneMapping}[DEV.tm]||THREE.ACESFilmicToneMapping;")
rep("SKY.u.k.value=(c.night>0.6?1.6:(gd>0.35?1.1:3.2))*(1-0.4*c.cloud);","SKY.u.k.value=(c.night>0.6?1.6:(gd>0.35?1.1:3.2))*(1-0.4*c.cloud)*DEV.sky;")
rep("  sun.shadow.radius=1+6*c.cloud;","  sun.shadow.radius=(1+6*c.cloud)*DEV.shadow;")
rep("scene.fog=new THREE.Fog(sky, 20-14*c.fog-6*(c.rain+c.snow)*0.5, 46-30*c.fog-12*(c.rain+c.snow)*0.5);","scene.fog=new THREE.Fog(sky, (20-14*c.fog-6*(c.rain+c.snow)*0.5)*DEV.fog, (46-30*c.fog-12*(c.rain+c.snow)*0.5)*DEV.fog);")
rep("function lensFor(a){ return a<1?44:35; }","function lensFor(a){ return (a<1?44:35)+(typeof DEV!=='undefined'?DEV.fov:0); }")
rep("uniforms:{tDiffuse:{value:null},k:{value:0.28}},","uniforms:{tDiffuse:{value:null},k:{value:0.28},sat:{value:1.06}},")
rep("uniform float k; varying vec2 vUv;","uniform float k; uniform float sat; varying vec2 vUv;")
rep("c.rgb=mix(vec3(dot(c.rgb,vec3(0.299,0.587,0.114))),c.rgb,1.06);","c.rgb=mix(vec3(dot(c.rgb,vec3(0.299,0.587,0.114))),c.rgb,sat);")
rep("return {comp,ao,bloom,size(","return {comp,ao,bloom,vig,size(")
rep("const pr=Math.min(window.devicePixelRatio||1,1.6);","const pr=Math.min(window.devicePixelRatio||1,1.6)*(typeof DEV!=='undefined'?DEV.scale:1);")
rep(" m.color.set(S.color); satBoost(m.color,1.4,0.8); m.metalness=0.6; m.roughness=0.2;",
    " m.color.set(S.color); satBoost(m.color,1.4,0.8); m.metalness=DEV.paintMet; m.roughness=DEV.paintRough; if('clearcoat' in m) m.clearcoat=DEV.coat; if(m.normalScale) m.normalScale.set(DEV.flake,DEV.flake);")
# the panel itself
rep('          <div class="row"><label for="gfxQ">Графика (тестовая сборка)</label>',
    '          <div class="row"><label for="devOn">Режим разработчика: ползунки графики на сцене</label><input type="checkbox" id="devOn"></div>\n          <div class="row"><label for="gfxQ">Графика (тестовая сборка)</label>')
rep("@media (prefers-reduced-motion: reduce){*{transition:none!important}.spin{animation-duration:3s}}",""".devp{position:absolute;z-index:7;left:calc(8px + var(--il));right:calc(8px + var(--ir));max-width:560px;bottom:calc(6px + var(--ib));max-height:30%;overflow:auto;border-radius:var(--rl);padding:0 10px 8px;
  --lg-base:rgba(16,20,26,.66);--lg-hi:rgba(255,255,255,.08);color:#eef2f7;font:500 .72rem var(--body);overscroll-behavior:contain;touch-action:pan-y}
.devp[hidden]{display:none}
.devp .hd{display:flex;gap:6px;align-items:center;justify-content:space-between;flex-wrap:wrap;position:sticky;top:0;z-index:1;margin:0 -10px;padding:8px 10px 6px;background:rgba(16,20,26,.94);border-radius:var(--rl) var(--rl) 0 0}
.devp .hd b{font:700 .72rem var(--mono);letter-spacing:.06em}
.devp .hd button{font:600 .68rem var(--body);border:1px solid rgba(255,255,255,.25);background:transparent;color:inherit;border-radius:8px;padding:4px 7px}
.devp .g{font:700 .62rem var(--mono);color:#9fb3ff;text-transform:uppercase;letter-spacing:.08em;margin:8px 0 2px}
.devp .r{display:grid;grid-template-columns:104px 1fr 40px;align-items:center;gap:6px;min-height:24px;line-height:1.15}
.devp .r input[type=range]{width:100%;accent-color:#86a2ff}
.devp .r output{font:500 .68rem var(--mono);text-align:right}
.devp select{font:inherit;background:rgba(255,255,255,.1);color:inherit;border:1px solid rgba(255,255,255,.25);border-radius:6px;padding:2px 4px}
.stage.devOpen #picks,.stage.devOpen .ov.tl,.stage.devOpen .ov.bo,.stage.devOpen .ov.orbp,.stage.devOpen .ov.hs,.stage.devOpen .toast{visibility:hidden}
@media (prefers-reduced-motion: reduce){*{transition:none!important}.spin{animation-duration:3s}}""")
rep("function setTab(t){","""// developer panel: every slider applies live and is saved; "Скопировать" puts all values on the clipboard as JSON to send to Claude
const DEV_UI=[['Тон и свет',[['exp','Экспозиция',0.3,2,0.01],['tm','Тонмаппинг',['aces','agx','reinhard','cineon']],['sun','Солнце',0,3,0.01],['hemi','Небо (заливка)',0,3,0.01],['fill','Контровой',0,3,0.01],['env','Отражения HDR',0,3,0.01],['sky','Яркость неба',0,3,0.01],['night','Ночь как в кино',0,1.5,0.01],['shadow','Мягкость теней',0,4,0.05],['fog','Дальность тумана',0.3,3,0.01]]],
  ['Постобработка',[['ao','Затенение AO',0,2,0.01],['aoR','Радиус AO',0.05,2,0.01],['bloom','Свечение',0,1.5,0.01],['bloomT','Порог свечения',0,6,0.05],['bloomR','Радиус свечения',0,1,0.01],['vig','Виньетка',0,0.8,0.01],['sat','Насыщенность',0,2,0.01]]],
  ['Кузов',[['paintMet','Металлик',0,1,0.01],['paintRough','Шероховатость',0,1,0.01],['coat','Лак',0,1,0.01],['flake','Искра',0,0.3,0.005],['glassOp','Стёкла: плотность',0.2,1,0.01]]],
  ['Земля и камера',[['sandN','Рельеф песка',0,2,0.01],['sandB','Яркость песка',0.5,1.5,0.01],['fov','Угол обзора ±',-15,20,1],['scale','Чёткость рендера',0.5,1.5,0.05]]]];
const devP=document.createElement('div'); devP.className='devp glass'; devP.hidden=true; stage.appendChild(devP);
function devApply(){
  store.set('devGfx',DEV);
  if(POST){ POST.ao.blendIntensity=DEV.ao; POST.ao.updateGtaoMaterial({radius:DEV.aoR}); POST.bloom.strength=DEV.bloom; POST.bloom.threshold=DEV.bloomT; POST.bloom.radius=DEV.bloomR; POST.vig.uniforms.k.value=DEV.vig; POST.vig.uniforms.sat.value=DEV.sat; }
  CM.glass.opacity=DEV.glassOp; CM.glass.needsUpdate=true;
  if(terMat.normalScale) terMat.normalScale.set(DEV.sandN,DEV.sandN); terMat.color.setScalar(DEV.sandB);
  paintMats.forEach(paintFinish); applyWeatherScene(); resize(); kick(); }
function devRender(){
  devP.innerHTML='<div class="hd"><b>DEV</b><span><button data-a="copy">Скопировать</button> <button data-a="share">Отправить</button> <button data-a="reset">Сброс</button> <button data-a="hide">✕</button></span></div>'+
    DEV_UI.map(([g,rows])=>'<div class="g">'+g+'</div>'+rows.map(([k,l,a,b,st])=>Array.isArray(a)?`<div class="r"><span>${l}</span><select data-k="${k}">${a.map(o=>`<option ${DEV[k]===o?'selected':''}>${o}</option>`).join('')}</select><output></output></div>`
      :`<div class="r"><span>${l}</span><input type="range" data-k="${k}" min="${a}" max="${b}" step="${st}" value="${DEV[k]}"><output>${(+DEV[k]).toFixed(st<0.01?3:2)}</output></div>`).join('')).join(''); }
devP.addEventListener('input',e=>{ const k=e.target.dataset.k; if(!k) return; DEV[k]=e.target.tagName==='SELECT'?e.target.value:+e.target.value;
  const o=e.target.parentNode.querySelector('output'); if(o&&e.target.tagName!=='SELECT') o.textContent=(+DEV[k]).toFixed(+e.target.step<0.01?3:2); devApply(); });
devP.addEventListener('pointerdown',e=>e.stopPropagation());
devP.addEventListener('click',async e=>{ const a=e.target.dataset&&e.target.dataset.a; if(!a) return; const json=JSON.stringify({app:'f7box-gfx',dev:DEV},null,0);
  if(a==='copy'){ try{ await navigator.clipboard.writeText(json); toast('<b>Скопировано</b>Вставьте в чат с Claude, чтобы перенести настройки в сборку.','good'); }catch(_){ prompt('Скопируйте:',json); } }
  if(a==='share'){ const Sh=nativePlugin('Share'); if(Sh) Sh.share({title:'Настройки графики',text:json}); else { try{ await navigator.clipboard.writeText(json); toast('<b>Скопировано</b>','good'); }catch(_){} } }
  if(a==='reset'){ Object.keys(DEV).forEach(k=>{ if(!(k in DEV_DEF)) delete DEV[k]; }); Object.assign(DEV,DEV_DEF); devRender(); devApply(); }
  if(a==='hide'){ setDev(false); } });
function setDev(on){ devOn=on; store.set('devOn',on); $('devOn').checked=on; devP.hidden=!on; stage.classList.toggle('devOpen',on); if(on) devRender(); kick(); }
$('devOn').addEventListener('change',e=>{ setDev(e.target.checked); if(e.target.checked) setTab('scene'); });
setTimeout(()=>{ devApply(); setDev(devOn); },0);
function setTab(t){""")


# ================= key-feature hotspots 1..5: camera flies to preset views of the box (for maker presentations) =================
rep("    camAnim.t=Math.min(1,camAnim.t+0.06);","    camAnim.t=Math.min(1,camAnim.t+(camAnim.sp?camAnim.sp*Math.min(3,dt*60):0.06));")
rep("  const a=A(); if(!a||boxOnly||camAnim||drive.mode!=='idle'||speed>0.05) return false;","  const a=A(); if(!a||boxOnly||camAnim||HS.active||drive.mode!=='idle'||speed>0.05) return false;")
rep("    &&performance.now()-ORB.last>(drop.hidden?ORB.IDLE:2500);","    &&!HS.active&&performance.now()-ORB.last>(drop.hidden?ORB.IDLE:2500);")
rep('      <div class="ov bo">','      <div class="ov hs" id="hsRow" role="group" aria-label="Ключевые моменты">'+''.join(f'<button class="glass" data-hs="{i}" aria-label="Ракурс {i}">{i}</button>' for i in range(1,6))+'</div>\n      <div class="ov bo">')
rep(".bo{left:calc(10px + var(--il));",""".hs{left:50%;transform:translateX(-50%);top:calc(10px + var(--it));gap:6px}
.hs button{width:34px;height:34px;border-radius:50%;padding:0;font:700 .82rem var(--mono);color:var(--ink);cursor:pointer;display:grid;place-items:center}
.hs button[aria-pressed="true"]{background:var(--accent);color:#fff;border-color:var(--accent)}
@media (max-width:899px){ .hs{top:auto;bottom:calc(var(--ib) + 6px + var(--hsb,170px))} }
.stage.dropOpen .ov.hs,.stage.zen .ov.hs{visibility:hidden}
.bo{left:calc(10px + var(--il));""")
rep("  tl.style.bottom=Math.round(sr.bottom-top+8)+'px';","  tl.style.bottom=Math.round(sr.bottom-top+8)+'px'; stage.style.setProperty('--hsb',Math.round(sr.bottom-top-parseFloat(getComputedStyle(stage).getPropertyValue('--ib')||0)+4)+'px');")
rep("function setTab(t){","""// box-local views: target and camera offset in metres from the box centre (x toward the tail, y up, z toward the driver side); lid: open toward the camera
const HS={active:0, VIEWS:{
  1:{t:[0,0.05,0],   c:[-0.4,1.15,1.35], lid:1},   // lid open, the whole inside from above the side
  2:{t:[0.05,0.0,0], c:[-0.95,0.75,0.85], lid:1},   // close look into the open box
  3:{t:[0,0.1,0],    c:[1.2,2.6,1.15],   lid:0},   // closed, from high behind: the shape of the lid
  4:{t:[0,0.12,0],   c:[0.15,0.22,2.3],   lid:0},   // closed, level with the roof: side profile
  5:{t:['bar',-0.06,0.42], c:[-0.55,0.12,0.95], lid:0} // close-up of the mount on the crossbar
}};
function goHotspot(n){
  const a=A(), v=(DEV.hs&&DEV.hs[n])||HS.VIEWS[n]; if(!a||!v) return;
  if(boxOnly) setBoxOnly(false);
  if(moveMode){ moveMode=false; moveBtn.setAttribute('aria-pressed','false'); } if(typeof setDrop==='function') setDrop(false);
  const want=v.lid?'1':'0'; if(String(S.lid?lidSide:0)!==want){ const t=document.querySelector(`#lidSw [data-lid="${want}"]`); if(t) t.click(); }
  const cx=M(a.L)/2, cy=M(a.H)/2, tx=v.t[0]==='bar'?(X(bars()[0])-X(curFront)):cx+v.t[0];
  const T=boxGroup.localToWorld(new THREE.Vector3(tx,(v.t[0]==='bar'?0:cy)+v.t[1],v.t[2])), P=T.clone().add(new THREE.Vector3(...v.c));
  HS.active=n; drive.userCam=true; ORB.v=0; ORB.last=performance.now();
  camAnim={from:camera.position.clone(), to:P, tf:controls.target.clone(), tt:T, t:0, sp:0.022};
  document.querySelectorAll('#hsRow [data-hs]').forEach(b=>b.setAttribute('aria-pressed',String(+b.dataset.hs===n))); kick();
}
$('hsRow').addEventListener('click',e=>{ const b=e.target.closest('[data-hs]'); if(!b) return; const n=+b.dataset.hs; if(HS.active===n){ HS.active=0; b.setAttribute('aria-pressed','false'); setView('q'); return; } goHotspot(n); });
// developer mode: hold a number for a second to store the current camera as that view (saved with the other dev settings)
document.querySelectorAll('#hsRow [data-hs]').forEach(b=>{ let tm=0;
  b.addEventListener('pointerdown',()=>{ if(!devOn) return; tm=setTimeout(()=>{ const a=A(); if(!a) return; const n=+b.dataset.hs;
    const C=boxGroup.localToWorld(new THREE.Vector3(M(a.L)/2,M(a.H)/2,0)), T=controls.target.clone(), Tl=boxGroup.worldToLocal(T.clone());
    DEV.hs=DEV.hs||{}; DEV.hs[n]={t:[+(Tl.x-M(a.L)/2).toFixed(3),+(Tl.y-M(a.H)/2).toFixed(3),+Tl.z.toFixed(3)], c:camera.position.clone().sub(T).toArray().map(v=>+v.toFixed(3)), lid:S.lid?1:0};
    store.set('devGfx',DEV); b.dataset.skip='1'; try{ navigator.vibrate&&navigator.vibrate(30); }catch(_){} toast('<b>Ракурс '+n+' сохранён</b>Текущая камера записана в эту кнопку.','good'); },900); });
  ['pointerup','pointerleave','pointercancel'].forEach(ev=>b.addEventListener(ev,()=>clearTimeout(tm))); });
$('hsRow').addEventListener('click',e=>{ const b=e.target.closest('[data-hs]'); if(b&&b.dataset.skip){ delete b.dataset.skip; e.stopImmediatePropagation(); } },true);
renderer.domElement.addEventListener('pointerdown',()=>{ if(HS.active){ HS.active=0; document.querySelectorAll('#hsRow [data-hs]').forEach(b=>b.setAttribute('aria-pressed','false')); } },{passive:true});
function setTab(t){""")


# ================= round of 2026-10-17 =================
# 1. dev panel: − / + steps, per-parameter reset, solid header
rep(".devp .hd{display:flex;gap:6px;align-items:center;justify-content:space-between;flex-wrap:wrap;position:sticky;top:0;z-index:1;margin:0 -10px;padding:8px 10px 6px;background:rgba(16,20,26,.94);border-radius:var(--rl) var(--rl) 0 0}",
    ".devp .hd{display:flex;gap:6px;align-items:center;justify-content:space-between;flex-wrap:wrap;position:sticky;top:0;z-index:2;margin:0 -10px;padding:8px 10px 6px;background:#12161c;border-radius:var(--rl) var(--rl) 0 0;box-shadow:0 4px 8px rgba(0,0,0,.35)}")
rep(".devp .r{display:grid;grid-template-columns:104px 1fr 40px;align-items:center;gap:6px;min-height:24px;line-height:1.15}",
    """.devp .r{display:grid;grid-template-columns:96px 28px minmax(0,1fr) 28px 40px 28px;align-items:center;gap:4px;min-height:30px;line-height:1.15}
.devp .r .pm,.devp .r .rs{width:28px;height:28px;padding:0;border-radius:7px;border:1px solid rgba(255,255,255,.22);background:rgba(255,255,255,.06);color:inherit;font:700 .9rem var(--mono);display:grid;place-items:center}
.devp .r .rs{font-size:.8rem;opacity:.35} .devp .r.mod .rs{opacity:1;color:#ffcf7a;border-color:#ffcf7a}
.devp .r.mod > span{color:#ffcf7a}
.devp .r select{grid-column:2 / 6}""")
rep("""      :`<div class="r"><span>${l}</span><input type="range" data-k="${k}" min="${a}" max="${b}" step="${st}" value="${DEV[k]}"><output>${(+DEV[k]).toFixed(st<0.01?3:2)}</output></div>`).join('')).join(''); }""",
    """      :`<div class="r${DEV[k]!==DEV_DEF[k]?' mod':''}" data-row="${k}"><span>${l}</span><button class="pm" data-k="${k}" data-d="-1" aria-label="Меньше">−</button><input type="range" data-k="${k}" min="${a}" max="${b}" step="${st}" value="${DEV[k]}"><button class="pm" data-k="${k}" data-d="1" aria-label="Больше">+</button><output>${(+DEV[k]).toFixed(st<0.01?3:2)}</output><button class="rs" data-k="${k}" data-rst="1" aria-label="Сбросить" title="По умолчанию: ${DEV_DEF[k]}">↺</button></div>`).join('')).join(''); }""")
rep("""Array.isArray(a)?`<div class="r"><span>${l}</span><select data-k="${k}">${a.map(o=>`<option ${DEV[k]===o?'selected':''}>${o}</option>`).join('')}</select><output></output></div>`""",
    """Array.isArray(a)?`<div class="r${DEV[k]!==DEV_DEF[k]?' mod':''}" data-row="${k}"><span>${l}</span><select data-k="${k}">${a.map(o=>`<option ${DEV[k]===o?'selected':''}>${o}</option>`).join('')}</select><button class="rs" data-k="${k}" data-rst="1" aria-label="Сбросить" title="По умолчанию: ${DEV_DEF[k]}">↺</button></div>`""")
rep("""  const o=e.target.parentNode.querySelector('output'); if(o&&e.target.tagName!=='SELECT') o.textContent=(+DEV[k]).toFixed(+e.target.step<0.01?3:2); devApply(); });""",
    """  devSync(k); devApply(); });
function devSync(k){ const row=devP.querySelector(`[data-row="${k}"]`); if(!row) return; const r=row.querySelector('input[type=range]'), o=row.querySelector('output'), sel=row.querySelector('select');
  if(r){ r.value=DEV[k]; if(o) o.textContent=(+DEV[k]).toFixed(+r.step<0.01?3:2); } if(sel) sel.value=DEV[k]; row.classList.toggle('mod',DEV[k]!==DEV_DEF[k]); }
devP.addEventListener('click',e=>{ const b=e.target.closest('button[data-k]'); if(!b) return; const k=b.dataset.k;
  if(b.dataset.rst){ DEV[k]=DEV_DEF[k]; }
  else { const r=devP.querySelector(`input[data-k="${k}"]`); if(!r) return; const st=+r.step, v=Math.min(+r.max,Math.max(+r.min,+DEV[k]+(+b.dataset.d)*st)); DEV[k]=+v.toFixed(4); }
  devSync(k); devApply(); });""")
# 4. very large ambient-occlusion radius makes dark blocks under the car: cap it
rep("['aoR','Радиус AO',0.05,2,0.01]","['aoR','Радиус AO',0.05,0.7,0.01]")
rep("  if(POST){ POST.ao.blendIntensity=DEV.ao; POST.ao.updateGtaoMaterial({radius:DEV.aoR});","  DEV.aoR=Math.min(DEV.aoR,0.7); if(POST){ POST.ao.blendIntensity=DEV.ao; POST.ao.updateGtaoMaterial({radius:DEV.aoR, distanceFallOff:1.0, thickness:1.0});")
# 2. compact items list while only the box is shown
rep(".stage.dropOpen .ov.hs,.stage.zen .ov.hs{visibility:hidden}",""".stage.dropOpen .ov.hs,.stage.zen .ov.hs{visibility:hidden}
.stage.boxonly .itemsDrop{max-height:min(27vh,220px);padding:4px;gap:0 2px}
.stage.boxonly .itemsDrop button{padding:3px 6px;gap:6px;grid-template-columns:18px minmax(0,1fr) auto}
.stage.boxonly .itemsDrop button svg{width:16px;height:16px}
.stage.boxonly .itemsDrop button .nm{font-size:.7rem;-webkit-line-clamp:1}
.stage.boxonly .itemsDrop .ih{padding:3px 6px 2px}
.stage.gateOn .ov.hs,.stage.gateOn .ov.orbp,.stage.gateOn .ov.bo,.stage.gateOn .ov.tl{visibility:hidden}""")
# 3. the see-through box stays after the items menu closes while only the box is shown; leaving that view fades it back
rep("let ghost=false, itemsOpen=false;","let ghost=false, itemsOpen=false, keepGhost=false, ghostFading=false;")
rep("  setGhost(itemsOpen||(S.wire===null?!!b:S.wire));","  setGhost(itemsOpen||keepGhost||(S.wire===null?!!b:S.wire));")
rep("  if(open) renderDrop(); setGhost(open||(S.wire===null?!!B():S.wire));","  if(open) renderDrop(); if(!open&&ghost&&!ghostFading) keepGhost=true; setGhost(open||keepGhost||(S.wire===null?!!B():S.wire));")
rep("    boxOnly=false; controls.minDistance=boxSaved?boxSaved.min:2.5;","    boxOnly=false; stage.classList.remove('boxonly'); if(keepGhost) fadeGhostOut(); controls.minDistance=boxSaved?boxSaved.min:2.5;")
rep("    boxSaved={p:camera.position.clone(), t:controls.target.clone(), min:controls.minDistance};","    boxSaved={p:camera.position.clone(), t:controls.target.clone(), min:controls.minDistance}; stage.classList.add('boxonly');")
rep("function setGhost(on){","""function fadeGhostOut(){
  if(ghostFading) return; const plain=S.wire===null?!!B():S.wire; if(plain){ keepGhost=false; return; } ghostFading=true;
  const items=[[matA,A()],[matB,B()]].filter(([m,b])=>b).map(([m,b])=>{ const c=new THREE.Color(boxFinish(b).hex); satBoost(c); return {m,c0:m.color.clone(),c}; });
  const t0=performance.now();
  const step=()=>{ const k=Math.min(1,(performance.now()-t0)/700), e=k*k*(3-2*k);
    items.forEach(({m,c0,c})=>{ m.opacity=0.2+0.8*e; m.color.copy(c0).lerp(c,e); });
    [boxGroup,cmpGroup].forEach(g=>g.traverse(o=>{ if(o.isLineSegments&&o.material) { o.material.transparent=true; o.material.opacity=1-e; } }));
    kick(); if(k<1) requestAnimationFrame(step); else { keepGhost=false; ghostFading=false; setGhost(false); [boxGroup,cmpGroup].forEach(g=>g.traverse(o=>{ if(o.isLineSegments&&o.material) o.material.opacity=1; })); } };
  step(); }
function setGhost(on){""")
# 5. overpass check: orbit around the middle of the car; panel-covered buttons hidden



# ================= 'min' graphics profile for weak phones: same models, much cheaper rendering =================
rep('<option value="eco">Экономия батареи</option>','<option value="eco">Экономия батареи</option><option value="min">Минимум (слабые телефоны)</option>')
rep("const renderer=new THREE.WebGLRenderer({antialias:true});","const renderer=new THREE.WebGLRenderer({antialias:GFX.q!=='min', powerPreference:GFX.q==='min'?'low-power':'high-performance'});")
rep("renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));","renderer.setPixelRatio(GFX.q==='min'?Math.min(window.devicePixelRatio||1,1):GFX.q==='eco'?Math.min(window.devicePixelRatio||1,1.5):Math.min(window.devicePixelRatio||1,2));")
# no real-time shadow maps: a soft painted shadow under the car instead
rep("renderer.shadowMap.enabled=true; renderer.shadowMap.type=THREE.PCFSoftShadowMap;","renderer.shadowMap.enabled=GFX.q!=='min'; renderer.shadowMap.type=GFX.q==='eco'?THREE.PCFShadowMap:THREE.PCFSoftShadowMap;")
rep("sun.shadow.mapSize.set(2048,2048);","sun.shadow.mapSize.set(GFX.q==='high'?2048:1024,GFX.q==='high'?2048:1024);")
rep("aoBlob.visible=false; aoBlob.renderOrder=-1;","aoBlob.visible=GFX.q==='min'; aoBlob.renderOrder=-1;")
rep("aoBlob.visible=false; CM.glass.transparent=gl0[0];","aoBlob.visible=GFX.q==='min'; CM.glass.transparent=gl0[0];")
# coarser ground mesh (it is rebuilt on the CPU while driving)
rep("const TER={W:44, D:48, nx:176, nz:150};","const TER={W:44, D:48, nx:GFX.q==='min'?88:176, nz:GFX.q==='min'?75:150};")
# headlight spot lights are costly per pixel: the beams and glowing lamps stay, the lights that paint the ground go
rep("  headlights.forEach(h=>{ h.L.intensity=9*hk; h.b.visible=hk>0.02; });","  headlights.forEach(h=>{ h.L.intensity=9*hk; h.L.visible=GFX.q!=='min'; h.b.visible=hk>0.02; });")
# 30 fps cap while animating
rep("  render();\n  if(busy) requestAnimationFrame(loop);","  if(!(GFX.q==='min'&&busy&&(now||0)-(window.__lastDraw||0)<31)){ window.__lastDraw=now||0; render(); }\n  if(busy) requestAnimationFrame(loop);")
# lighter materials: no second clear-coat layer
rep("function setTab(t){","""if(GFX.q==='min'){ const lite=()=>scene.traverse(o=>{ if(!o.isMesh) return; (Array.isArray(o.material)?o.material:[o.material]).forEach(m=>{ if(m&&m.isMeshPhysicalMaterial&&m.clearcoat){ m.clearcoat=0; m.needsUpdate=true; } }); });
  lite(); setTimeout(lite,4000); setTimeout(lite,12000); }
function setTab(t){""")
rep("if('clearcoat' in m) m.clearcoat=DEV.coat;","if('clearcoat' in m) m.clearcoat=GFX.q==='min'?0:DEV.coat;")


# ---- auto quality: guess from the GPU on first launch, then confirm by measured frame rate ----
rep("const GFX={q:store.get('gfxQ','high')};","""const GFX=(()=>{ const saved=store.get('gfxQ',null);
  if(saved&&saved!=='auto') return {q:saved, probing:store.get('gfxProbe','')==='run'};
  let q='high', gpu='';
  try{ const c=document.createElement('canvas').getContext('webgl'); const ext=c&&c.getExtension('WEBGL_debug_renderer_info'); gpu=ext?String(c.getParameter(ext.UNMASKED_RENDERER_WEBGL)):''; c&&c.getExtension('WEBGL_lose_context')&&c.getExtension('WEBGL_lose_context').loseContext(); }catch(_){}
  const mob=/Android|iPhone|iPad|Mobile/i.test(navigator.userAgent), cores=navigator.hardwareConcurrency||4, mem=navigator.deviceMemory||4;
  if(mob){ if(/Mali-(T|G3|G5[12]|G57|G68)|PowerVR|Adreno \\(TM\\) ?[1-5]\\d\\d|Adreno \\(TM\\) ?6[0-1]\\d|IMG|GE8320|Vivante/i.test(gpu)||mem<=3) q='min';
    else if(/Mali-G(6|7[0-6])|Adreno \\(TM\\) ?6[2-9]\\d|Adreno \\(TM\\) ?7[0-2]\\d/i.test(gpu)||cores<=6||mem<=4) q='eco'; }
  store.set('gfxQ',q); store.set('gfxProbe','run'); store.set('gfxAuto',gpu||'?'); return {q, probing:true, gpu}; })();
// measure real frame time while the scene animates; step down a level if the phone can't keep up
GFX.probe=(()=>{ if(!GFX.probing||GFX.q==='min'){ if(GFX.probing) store.set('gfxProbe','done'); return null; }
  const T0=performance.now(), dts=[]; let last=0;
  return now=>{ if(now-T0<2500||GFX.fresh){ GFX.fresh=0; last=now; return; } dts.push(now-last); last=now;
    const srt=dts.slice().sort((a,b)=>a-b), med=srt[srt.length>>1]; if(dts.length<(dts.length>=12&&med>70?12:60)) return; GFX.probe=null;
    const down=GFX.q==='high'?(med>45?'min':med>26?'eco':null):(med>36?'min':null);
    if(!down){ store.set('gfxProbe','done'); return; }
    store.set('gfxQ',down); if(down==='min') store.set('gfxProbe','done');
    try{ toast('<b>Графика упрощена под телефон</b>'+Math.round(1000/med)+' кадр/с — включаю «'+(down==='min'?'Минимум':'Экономия')+'»','info'); }catch(_){}
    setTimeout(()=>location.reload(),1800); }; })();""")
rep("function loop(now){","function loop(now){\n  if(GFX.probe) GFX.probe(now||performance.now());")
rep("function kick(){ if(!running){running=true; requestAnimationFrame(loop);} }","function kick(){ if(!running){running=true; GFX.fresh=1; requestAnimationFrame(loop);} }")
rep('<option value="min">Минимум (слабые телефоны)</option>','<option value="min">Минимум (слабые телефоны)</option><option value="auto">Определить заново</option>')
rep("$('gfxQ').value=GFX.q; $('gfxQ').addEventListener('change',e=>{ store.set('gfxQ',e.target.value); location.reload(); });",
    "$('gfxQ').value=GFX.q; $('gfxQ').addEventListener('change',e=>{ const v=e.target.value; store.set('gfxQ',v); store.set('gfxProbe',v==='auto'?'run':'done'); location.reload(); });")


# ---- haptics in the developer panel: a tick per slider step, a firmer cue when a camera view is saved
rep("devP.addEventListener('input',e=>{ const k=e.target.dataset.k; if(!k) return;","devP.addEventListener('input',e=>{ const k=e.target.dataset.k; if(!k) return; if(e.target.type==='range') hap('tick');")
rep("try{ navigator.vibrate&&navigator.vibrate(30); }catch(_){}","hap('heavy');")


# quality class on <html> so CSS can drop expensive effects (blurred veil) in the minimum profile
rep("GFX.probe=(()=>{","document.documentElement.classList.add('q-'+GFX.q);\nGFX.probe=(()=>{")


# ---- see-through box stays on after the items editor closes; it fades back to solid on: the box-frame button,
#      any drive (free, highway, overpass), a key-moment button, or switching to "box only"
rep("$('wireBtn').addEventListener('click',()=>{ S.wire=!ghost; update(); });","$('wireBtn').addEventListener('click',()=>{ if(keepGhost){ S.wire=false; fadeGhostOut(); return; } S.wire=!ghost; update(); });")
rep("function loop(now){\n","function loop(now){\n  if(keepGhost&&!ghostFading&&(drive.mode==='free'||drive.mode==='hw'||drive.mode==='gate')) fadeGhostOut();\n")
rep("  if(boxOnly) setBoxOnly(false);\n  if(moveMode){","  if(keepGhost) fadeGhostOut(); if(boxOnly) setBoxOnly(false);\n  if(moveMode){")
rep("    if(drive.mode==='intro') drive.mode='idle';\n    boxSaved=","    if(drive.mode==='intro') drive.mode='idle';\n    if(keepGhost&&!itemsOpen) fadeGhostOut();\n    boxSaved=")


# ---- performance without visual loss: shadows redrawn only when something casts differently, static car parts merged per material,
#      lower resolution only while the user is turning the camera, and a frame-rate readout in developer mode
rep("import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';","import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';\nimport * as BGU from 'three/addons/utils/BufferGeometryUtils.js';")
rep("ShaderPass,RoundedBoxGeometry});","ShaderPass,RoundedBoxGeometry,BGU});")
rep("comp.setPixelRatio(pr); comp.setSize(w,h); ao.setSize(w*pr,h*pr);","comp.setPixelRatio(pr*(window.DRK||1)); comp.setSize(w,h); ao.setSize(w*pr*(window.DRK||1),h*pr*(window.DRK||1));")
rep("\nlet running=false;\n","""
/* --- shadow map: rebuilt only when a shadow caster, the sun or visibility changed (camera moves reuse it) --- */
const PERF={shH:NaN, shN:0, frames:0, t0:performance.now(), fps:0, merged:''};
renderer.shadowMap.autoUpdate=false; renderer.shadowMap.needsUpdate=true; renderer.info.autoReset=false;
function shadowHash(){ let h=0, i=0;
  scene.traverseVisible(o=>{ if(o.castShadow&&(o.isMesh||o.isInstancedMesh)){ const e=o.matrixWorld.elements; i++; h+=((e[12]*1.31+e[13]*2.17+e[14]*3.07+e[0]*.71+e[2]*1.93+e[5]*.37+e[8]*2.29+e[10]*.53)*(1+(i%89)*.013))+i*1e-3; } });
  return h+sun.position.x*5.1+sun.position.y*7.3+sun.position.z*3.3+(sun.castShadow?17:0)+sun.shadow.radius*.7; }
function shadowCheck(){ if(!renderer.shadowMap.enabled) return; const moving=drive.mode!=='idle'||speed>0||amp>0, h=moving?NaN:shadowHash();
  if(moving||h!==PERF.shH){ PERF.shH=h; renderer.shadowMap.needsUpdate=true; PERF.shN++; } }
/* --- merge static meshes of the car per material: same picture, far fewer draw calls --- */
function flipWinding(g){ if(g.index){ const a=g.index.array; for(let i=0;i<a.length;i+=3){ const t=a[i+1]; a[i+1]=a[i+2]; a[i+2]=t; } g.index.needsUpdate=true; }
  else Object.values(g.attributes).forEach(at=>{ const n=at.itemSize, a=at.array; for(let i=0;i<at.count;i+=3) for(let k=0;k<n;k++){ const t=a[(i+1)*n+k]; a[(i+1)*n+k]=a[(i+2)*n+k]; a[(i+2)*n+k]=t; } at.needsUpdate=true; }); }
function mergeCarStatic(root){
  if(!THREE.BGU) return; root.updateMatrixWorld(true);
  const rigid=new Set([root,glbPivot,...spinWheels.map(w=>w.obj)]), skip=new Set([...stockRims,...rimMeshes]), groups=new Map(); let before=0;
  root.traverse(o=>{ if(!o.isMesh) return; before++;
    if(o.isInstancedMesh||o.isSkinnedMesh||rigid.has(o)||skip.has(o)||Array.isArray(o.material)||o.morphTargetInfluences||!o.visible) return;
    let a=o.parent; while(a&&!rigid.has(a)) a=a.parent; if(!a) return;
    const g=o.geometry, key=[a.uuid,o.material.uuid,o.castShadow,o.receiveShadow,o.renderOrder,!!g.index,Object.keys(g.attributes).sort().map(k=>k+g.attributes[k].itemSize).join(',')].join('|');
    if(!groups.has(key)) groups.set(key,{a,list:[]}); groups.get(key).list.push(o); });
  let removed=0, added=0;
  groups.forEach(({a,list})=>{ if(list.length<2) return;
    const inv=new THREE.Matrix4().copy(a.matrixWorld).invert();
    const geos=list.map(o=>{ const g=o.geometry.clone(), m=new THREE.Matrix4().multiplyMatrices(inv,o.matrixWorld); g.applyMatrix4(m); if(m.determinant()<0) flipWinding(g); g.morphAttributes={}; return g; });
    let mg=null; try{ mg=THREE.BGU.mergeGeometries(geos,false); }catch(e){} if(!mg) return;
    const mesh=new THREE.Mesh(mg,list[0].material); mesh.castShadow=list[0].castShadow; mesh.receiveShadow=list[0].receiveShadow; mesh.renderOrder=list[0].renderOrder; mesh.name='merged';
    a.add(mesh); list.forEach(o=>o.parent&&o.parent.remove(o)); removed+=list.length; added++; geos.forEach(g=>g.dispose()); });
  PERF.merged=before+' → '+(before-removed+added); console.log('car parts merged', PERF.merged); renderer.shadowMap.needsUpdate=true;
}
/* --- dynamic resolution: a little lower only while a finger or mouse is turning the camera --- */
const DR={k:1, base:renderer.getPixelRatio(), hold:false, t:0};
function setResK(k){ if(Math.abs(DR.k-k)<0.01) return; DR.k=k; window.DRK=k; renderer.setPixelRatio(DR.base*k); resize(); }
function drOn(){ DR.hold=true; clearTimeout(DR.t); setResK(GFX.q==='high'?0.7:0.75); }
function drOff(){ DR.hold=false; clearTimeout(DR.t); DR.t=setTimeout(()=>{ if(!DR.hold&&!camAnim){ setResK(1); kick(); } },260); }
renderer.domElement.addEventListener('pointerdown',drOn); addEventListener('pointerup',drOff); addEventListener('pointercancel',drOff);
renderer.domElement.addEventListener('wheel',()=>{ drOn(); drOff(); },{passive:true});
/* --- frame-rate readout (developer mode) --- */
const perfEl=document.createElement('div'); perfEl.className='perf'; perfEl.hidden=true; stage.appendChild(perfEl);
function perfTick(){ PERF.frames++; const n=performance.now(); if(n-PERF.t0<500) return; PERF.fps=Math.round(PERF.frames*1000/(n-PERF.t0)); PERF.frames=0; PERF.t0=n;
  perfEl.hidden=!devOn; if(!devOn) return; const i=renderer.info.render;
  perfEl.textContent=`${PERF.fps} к/с · ${i.calls} выз · ${Math.round(i.triangles/1000)}k тр · тени ${PERF.shN} · ×${DR.k.toFixed(2)}${PERF.merged?' · части '+PERF.merged:''}`; }
let running=false;
""")
rep("  scene.updateMatrixWorld(); camera.updateMatrixWorld();   // project overlays with this frame's camera, not the previous one\n",
    "  scene.updateMatrixWorld(); camera.updateMatrixWorld();   // project overlays with this frame's camera, not the previous one\n  perfTick(); renderer.info.reset(); shadowCheck();\n")
rep("    collectStockRims(); applyRims();\n    carModelReady=true;","    collectStockRims(); applyRims(); mergeCarStatic(root);\n    carModelReady=true;",cnt=2)
rep(".devp[hidden]{display:none}",".devp[hidden]{display:none}\n.perf{position:absolute;z-index:8;left:50%;transform:translateX(-50%);top:calc(6px + var(--it));background:rgba(10,12,16,.78);color:#9ff0c0;font:600 11px/1.3 ui-monospace,Menlo,monospace;padding:4px 9px;border-radius:8px;pointer-events:none;white-space:nowrap}\n.perf[hidden]{display:none}")


# ---- shadow silhouette: one light invisible mesh casts the car body's shadow; wheels and the tailgate keep their own
rep("    collectStockRims(); applyRims(); mergeCarStatic(root);\n    carModelReady=true;","    collectStockRims(); applyRims(); mergeCarStatic(root); loadShadowProxy(root, CARDEF.model.replace('.json','_shadow.json'));\n    carModelReady=true;",cnt=2)
rep("function mergeCarStatic(root){","""function loadShadowProxy(root, file){
  if(GFX.q==='min') return;   // no shadow maps there
  loadModel(file, g=>{ let src=null; g.scene.traverse(o=>{ if(o.isMesh&&!src) src=o; }); if(!src) return;
    const pm=new THREE.Mesh(src.geometry, new THREE.MeshBasicMaterial({colorWrite:false, depthWrite:false, transparent:true, opacity:0}));
    pm.name='shadow_proxy'; pm.castShadow=true; pm.receiveShadow=false; pm.frustumCulled=false; root.add(pm);
    const keep=new Set(); [glbPivot,...spinWheels.map(w=>w.obj)].forEach(n=>n.traverse(o=>keep.add(o)));
    root.traverse(o=>{ if(o.isMesh&&o!==pm&&!keep.has(o)) o.castShadow=false; });
    renderer.shadowMap.needsUpdate=true; kick(); });
}
function mergeCarStatic(root){""")


# ---- faster model unpacking: the browser decodes base64 natively instead of a per-byte loop
rep("""    const bin=atob(d.glb), buf=new Uint8Array(bin.length);
    for(let i=0;i<bin.length;i++) buf[i]=bin.charCodeAt(i);
    new THREE.GLTFLoader().parse(buf.buffer, '', onLoad, err=>console.warn('model parse failed', url, err));""","""    return fetch('data:application/octet-stream;base64,'+d.glb).then(r=>r.arrayBuffer()).then(ab=>new THREE.GLTFLoader().parse(ab, '', onLoad, err=>console.warn('model parse failed', url, err)));""")

G83DIR='/tmp/claude-0/-home-claude/9371c78e-d13a-5b57-ac13-2f71dd22ff25/scratchpad/tools/g83'
exec(open(G83DIR+'/g83.py',encoding='utf-8').read())
open(DST,'w',encoding='utf-8').write(s); print('gfx ok')
