# gfx-83: render-core power saving, cinematic dusk look, box title, blueprint constructor, product sheet, cart
import os
D=G83DIR
css=open(D+'/g83.css',encoding='utf-8').read(); js=open(D+'/g83.js',encoding='utf-8').read()
# first run of this build starts in the cinematic look
rep("const GFX=(()=>{ const saved=store.get('gfxQ',null);","if(!store.get('g83',0)){ store.set('g83',1); store.set('wxMode','cine'); }\nconst GFX=(()=>{ const saved=store.get('gfxQ',null);")
# ---- render core: activity clock, frame governor, sleep ----
rep("let running=false;\nfunction kick(){ if(!running){running=true; GFX.fresh=1; requestAnimationFrame(loop);} }",
"""let running=false;
/* power saving: ambient motion (the figure, the idle orbit, rain) runs at 30 fps and stops by itself a while after the last touch; touch-driven motion is capped at 60 */
const ACT={t:performance.now()}, AWK=ms=>performance.now()-ACT.t<ms;
const FG={first:true, last:0, cap:16.6, amb:false, hot:false, run:0,
  tick(tn){ const gap=tn-FG.last; if(gap>3000) FG.run=0; else FG.run+=Math.min(gap,100); if(gap>8000) FG.hot=false; if(FG.run>50000) FG.hot=true; FG.first=false; FG.last=tn; }};
['pointerdown','keydown','wheel','touchstart'].forEach(ev=>document.addEventListener(ev,()=>{ ACT.t=performance.now(); kick(); },{passive:true,capture:true}));
document.addEventListener('pointermove',e=>{ if(e.buttons){ ACT.t=performance.now(); } },{passive:true,capture:true});
document.addEventListener('visibilitychange',()=>{ if(!document.hidden){ ACT.t=performance.now(); kick(); } });
function kick(){ if(!running){running=true; GFX.fresh=1; FG.first=true; requestAnimationFrame(loop);} }""")
rep("function loop(now){\n  if(keepGhost&&","function loop(now){\n  { const tn=now||performance.now(); if(!FG.first&&!GFX.probe&&tn-FG.last<FG.cap-2.5){ requestAnimationFrame(loop); return; } FG.tick(tn); }\n  if(keepGhost&&")
rep("  if(stepPerson(dt)) busy=true;","  let amb=false; if(stepPerson(dt)) amb=true;")
rep("  if(stepWeather(dt)) busy=true;","  if(stepWeather(dt)) amb=true;")
rep("  if(stepOrbit(dt)) busy=true;\n  if(stepPivot(dt)) busy=true;\n  if(controls.update()) busy=true;",
    "  const orb=stepOrbit(dt); if(orb) amb=true;\n  if(stepPivot(dt)){ if(orb) amb=true; else busy=true; }\n  if(controls.update()){ if(orb) amb=true; else busy=true; }")
rep("  if(!(GFX.q==='min'&&busy&&(now||0)-(window.__lastDraw||0)<31)){ window.__lastDraw=now||0; render(); }",
    "  FG.amb=amb&&!busy; FG.cap=(GFX.q==='min'||FG.amb||FG.hot)?33.3:16.6; busy=busy||amb;\n  render();")
rep("  if(!still) pT=(pT+dt/4.2)%1;","  const live=!still&&(AWK(14000)||pT>=0.02); if(live) pT=(pT+dt/4.2)%1;")
rep("  return !still;\n}","  return live;\n}")
rep("&&!HS.active&&performance.now()-ORB.last>(drop.hidden?ORB.IDLE:2500);","&&!HS.active&&performance.now()-ORB.last>(drop.hidden?ORB.IDLE:2500)&&AWK(ORB.IDLE+40000);")
rep("  return moving||rainLines.visible||snowPts.visible;","  return moving||((rainLines.visible||snowPts.visible)&&AWK(90000));")
rep("  if(moving||h!==PERF.shH){ PERF.shH=h; renderer.shadowMap.needsUpdate=true; PERF.shN++; } }",
    "  if(!moving&&FG.amb&&h!==PERF.shH&&performance.now()-(PERF.shT||0)<90) return;\n  if(moving||h!==PERF.shH){ PERF.shH=h; PERF.shT=performance.now(); renderer.shadowMap.needsUpdate=true; PERF.shN++; } }")
# ---- cinematic look wired into the weather system ----
rep("cur:{cloud:0, rain:0, snow:0, fog:0, night:0, golden:0, stars:0, sx:-4, sy:8, sz:5}};","cur:{cloud:0, rain:0, snow:0, fog:0, night:0, golden:0, stars:0, sx:-4, sy:8, sz:5, cine:0}};")
rep("const m=WX.mode, z={cloud:0, rain:0, snow:0, fog:0, night:0, golden:0, stars:0, sx:-4, sy:8, sz:5, wind:0, windDir:0};","const m=WX.mode, z={cloud:0, rain:0, snow:0, fog:0, night:0, golden:0, stars:0, sx:-4, sy:8, sz:5, wind:0, windDir:0, cine:0};")
rep("night:{night:1, stars:1, cloud:0.1}}[m]);","night:{night:1, stars:1, cloud:0.1}, cine:{cine:1, stars:0.3}}[m]);")
rep("['cloud','rain','snow','fog','night','golden','stars','sx','sy','sz'].forEach(n=>{ const d=t[n]-c[n];","['cloud','rain','snow','fog','night','golden','stars','sx','sy','sz','cine'].forEach(n=>{ const d=t[n]-c[n];")
rep("['cloud','rain','snow','fog','night'].forEach(n=>WX.cur[n]=t[n]);","['cloud','rain','snow','fog','night','cine'].forEach(n=>WX.cur[n]=t[n]);")
rep("function wxApply(snap){ wxRender();","function wxApply(snap){ if(WX.mode==='cine') document.documentElement.dataset.theme='dark'; else if(document.documentElement.dataset.theme==='dark') delete document.documentElement.dataset.theme; wxRender();")
rep("live:'Реальная погода: '+WX_CITY.name, off:'Без погоды',","live:'Реальная погода: '+WX_CITY.name, cine:'Кино · сумерки', off:'Без погоды',")
rep("const hk=Math.max(c.night,c.fog*0.9);","const hk=Math.max(c.night,c.fog*0.9,(c.cine||0)*0.9);")
rep("beamMat.uniforms.op.value=0.5*c.night+0.6*c.fog;","beamMat.uniforms.op.value=0.5*c.night+0.6*c.fog+0.3*(c.cine||0);")
rep(".lerp(new THREE.Color(0xd01010),0.7*c.night)",".lerp(new THREE.Color(0xd01010),0.7*Math.max(c.night,c.cine||0))")
rep("(1-0.35*c.cloud)*DEV.env;","(1-0.35*c.cloud)*DEV.env*(1-0.5*(c.cine||0));")
rep("CM.amber.emissive.setHex(0x2a1200);\n  kick();\n}","CM.amber.emissive.setHex(0x2a1200);\n  if(window.CINE) window.CINE.apply(c.cine||0, sky);\n  kick();\n}")
rep("  STARS.p.position.copy(camera.position);\n","  STARS.p.position.copy(camera.position); if(window.CINE) window.CINE.tick();\n")
# ---- blueprint draw path ----
rep("  if(!boxOnly){ drawScene(); return; }","  if(!boxOnly){ if(window.BP&&window.BP.check()) window.BP.draw(); else drawScene(); return; }")
# ---- markup ----
rep('      <div class="ov wx">','      <div class="ov btl"><button id="boxTitle"></button></div>\n      <div class="ov wx">')
rep('      <div class="readout" id="readout" hidden></div>','      <div class="shop glass" id="shop" role="dialog" aria-label="Карточка бокса" hidden><div class="shh"><i class="grab"></i><button class="shx" id="shopX" aria-label="Закрыть">×</button></div><div><span class="lbl">Модели</span><div class="shc" id="shopCar"></div></div><div class="shd" id="shopDet"></div></div>\n      <div class="readout" id="readout" hidden></div>')
rep('   <div class="tabpage" id="pgInfo">','   <div class="tabpage" id="pgCart"><h1 class="pghead">Корзина</h1><section id="cartBody"></section></div>\n   <div class="tabpage" id="pgInfo">')
rep('<span>Настройки</span></button>\n</nav>','<span>Настройки</span></button>\n  <button role="tab" data-tab="cart" aria-selected="false" class="ctab"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 4h2l2.4 11h10.2L20 7H6.2"/><circle cx="9.5" cy="19" r="1.4"/><circle cx="16.5" cy="19" r="1.4"/></svg><span>Корзина</span><i class="cnt" id="cartCnt" hidden></i></button>\n</nav>')
rep("['A','B'].forEach(k=>$('chip'+k).addEventListener('click',()=>{ const p=$('pop'+k), open=p.hidden;","['A','B'].forEach(k=>$('chip'+k).addEventListener('click',()=>{ if(k==='A'&&window.SHOP){ closePops(); window.SHOP.isOpen?window.SHOP.close():window.SHOP.open(); return; } const p=$('pop'+k), open=p.hidden;")
# ---- styles and the feature block ----
i=s.index('</style>'); s=s[:i]+css+s[i:]
rep("\nrenderItemChips();\nloadCarModel();\nselectBox(S.sel);","\n"+js+"\nrenderItemChips();\nloadCarModel();\nselectBox(S.sel);")
