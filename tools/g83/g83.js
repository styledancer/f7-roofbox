/* ================= gfx-83 ================= */
/* --- cinematic dusk: dark sky with a glowing horizon, mountain silhouettes, a warm lantern by the car --- */
window.CINE=(()=>{
  const lin=h=>new THREE.Color(h).convertSRGBToLinear();
  const q=fitView('q'), sd=new THREE.Vector3().subVectors(q[1],q[0]); sd.y=0; sd.normalize();   // the glow sits behind the car in the 3/4 view
  const u={k:{value:0}, flatc:{value:new THREE.Color(0.5,0.5,0.5)}, sun:{value:sd.clone()}, lowc:{value:lin(0x0b0d12)}};
  const tail='\n#include <tonemapping_fragment>\n#include <colorspace_fragment>\n}';
  const dome=new THREE.Mesh(new THREE.SphereGeometry(95,24,16), new THREE.ShaderMaterial({uniforms:u, side:THREE.BackSide, depthTest:false, depthWrite:false, fog:false,
    vertexShader:'varying vec3 vD; void main(){ vD=position; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
    fragmentShader:'uniform float k; uniform vec3 flatc; uniform vec3 sun; uniform vec3 lowc; varying vec3 vD; void main(){ vec3 d=normalize(vD); float e=d.y; vec2 h2=normalize(d.xz+vec2(1e-5)); float az=max(0.0,dot(h2,normalize(sun.xz))); float h=clamp(e,0.0,1.0);'
      +'vec3 top=vec3(0.004,0.006,0.014); vec3 mid=vec3(0.020,0.026,0.055); vec3 c=mix(mid,top,smoothstep(0.05,0.6,h));'
      +'vec3 glow=mix(vec3(0.20,0.04,0.03),vec3(1.5,0.55,0.07),pow(az,1.6)); float band=exp(-h*13.0)*(0.10+0.90*pow(az,1.6)); c=mix(c,glow,clamp(band,0.0,1.0));'
      +'c+=vec3(1.0,0.50,0.12)*exp(-h*30.0)*pow(az,5.0)*0.9; c=mix(c,lowc,smoothstep(0.004,-0.03,e)); gl_FragColor=vec4(mix(flatc,c,k),1.0);'+tail}));
  dome.renderOrder=-10; dome.frustumCulled=false;
  // two rings of ridges, built once
  const ridge=(R,lo,hi,seed,N)=>{ let a=seed; const r=()=>{ a=(a*16807)%2147483647; return a/2147483647; };
    const ph=[r()*6.28,r()*6.28,r()*6.28,r()*6.28], pos=[], hh=[], idx=[];
    for(let i=0;i<=N;i++){ const t=i/N*Math.PI*2, n=0.5+0.5*(0.5*Math.sin(3*t+ph[0])+0.28*Math.sin(7*t+ph[1])+0.14*Math.sin(17*t+ph[2])+0.08*Math.sin(41*t+ph[3]));
      const y=lo+(hi-lo)*Math.pow(n,1.5)+(i%2?0.35:0)*(hi-lo)*0.06; pos.push(Math.cos(t)*R,y,Math.sin(t)*R, Math.cos(t)*R,-2,Math.sin(t)*R); hh.push(1,0);
      if(i<N){ const o=i*2; idx.push(o,o+1,o+2, o+1,o+3,o+2); } }
    const g=new THREE.BufferGeometry(); g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3)); g.setAttribute('hh',new THREE.Float32BufferAttribute(hh,1)); g.setIndex(idx); return g; };
  const mMat=(base,rim)=>new THREE.ShaderMaterial({uniforms:{k:u.k, flatc:u.flatc, sun:u.sun, base:{value:lin(base)}, rim:{value:rim}}, side:THREE.DoubleSide, depthTest:false, depthWrite:false, fog:false,
    vertexShader:'attribute float hh; varying float vH; varying vec3 vD; void main(){ vH=hh; vD=position; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
    fragmentShader:'uniform float k; uniform vec3 flatc; uniform vec3 sun; uniform vec3 base; uniform float rim; varying float vH; varying vec3 vD; void main(){ float az=max(0.0,dot(normalize(vD.xz),normalize(sun.xz)));'
      +'vec3 c=base+vec3(0.55,0.15,0.03)*rim*pow(az,3.0)*smoothstep(0.55,1.0,vH); gl_FragColor=vec4(mix(flatc,c,k),1.0);'+tail});
  const far=new THREE.Mesh(ridge(90,10,44,24691,220), mMat(0x171b27,0.4)), near=new THREE.Mesh(ridge(84,3,20,8642,180), mMat(0x090b10,0.12));
  far.renderOrder=-9; near.renderOrder=-8; far.frustumCulled=near.frustumCulled=false;
  const grp=new THREE.Group(); grp.add(dome,far,near); grp.visible=false; scene.add(grp);
  // lantern: warm light pooling on the sand next to the car
  const lamp=new THREE.PointLight(0xff8a2e,0,10,1.5); lamp.visible=false; car.add(lamp);
  const glow=new THREE.Sprite(new THREE.SpriteMaterial({map:hlGlowTex, color:0xffa040, transparent:true, opacity:0, depthWrite:false, blending:THREE.AdditiveBlending, fog:false})); glow.scale.set(1.5,1.5,1); glow.visible=false; car.add(glow);
  const key=new THREE.Vector3(-sd.x*5-sd.z*4, 6.5, -sd.z*5+sd.x*4);   // soft cool key from the camera side
  const vg=document.createElement('div'); vg.className='cineVg'; stage.appendChild(vg);
  const C={k:0, grp, lamp, key,
    apply(k,sky){ C.k=k; u.k.value=k; u.flatc.value.copy(sky).convertSRGBToLinear(); grp.visible=k>0.01; vg.style.opacity=k.toFixed(2); if(k<0.005) { lamp.visible=glow.visible=false; return; }
      const L=(a,b)=>a+(b-a)*k;
      if(scene.fog){ scene.fog.color.lerp(u.lowc.value,k); scene.fog.near=L(scene.fog.near,15); scene.fog.far=L(scene.fog.far,62); }
      sun.position.lerp(key,k); sun.intensity*=L(1,0.42); sun.color.lerp(new THREE.Color(0xdde4f6),k); WX_SUN=sun.intensity;
      hemi.intensity*=L(1,0.3); hemi.color.lerp(new THREE.Color(0x56679a),k); fill.intensity*=L(1,0.45);
      renderer.toneMappingExposure*=L(1,0.95);
      cSoil.multiplyScalar(L(1,0.26)); cGrass.multiplyScalar(L(1,0.26)); sandFar.material.color.copy(cSoil).multiplyScalar(0.9); terDirty=true;
      C.tick(); },
    tick(){ if(C.k<0.005) return; grp.position.set(camera.position.x,0,camera.position.z);
      const on=drive.mode==='idle'&&speed===0&&!boxOnly, sdn=lidSide||1;
      if(lamp.visible!==on){ lamp.visible=on; glow.visible=on; }
      if(on){ lamp.intensity=7*C.k; lamp.position.set(X(CAR.L*0.86),0.42,sdn*(M(CAR.W)/2+1.55)); glow.position.copy(lamp.position); glow.position.y=0.2; glow.material.opacity=0.8*C.k; } } };
  return C; })();

/* --- blueprint view inside the items constructor: line drawing on a dark sheet --- */
window.BP=(()=>{
  const bg=new THREE.Color(0x0b1422);
  const fillM=new THREE.MeshBasicMaterial({color:new THREE.Color(0x0c1524).convertSRGBToLinear(), side:THREE.DoubleSide, polygonOffset:true, polygonOffsetFactor:1.5, polygonOffsetUnits:1.5, toneMapped:false, fog:false});
  const glassM=new THREE.MeshBasicMaterial({color:new THREE.Color(0x14233a).convertSRGBToLinear(), side:THREE.DoubleSide, transparent:true, opacity:0.28, depthWrite:false, toneMapped:false, fog:false});
  const lineM=new THREE.LineBasicMaterial({color:new THREE.Color(0xcfe1ff).convertSRGBToLinear(), transparent:true, opacity:0.8, toneMapped:false, fog:false});
  const grid=new THREE.GridHelper(48,48,0x123a66,0x0a2038); grid.material.transparent=true; grid.material.opacity=0.9; grid.material.toneMapped=false; grid.visible=false; grid.position.y=0.002; scene.add(grid);
  const fog=new THREE.Fog(bg.clone().convertSRGBToLinear(),14,46);
  const B={on:false, swapped:[], hidden:[], queue:[], busy:false,
    check(){ const want=(itemsOpen||keepGhost)&&!boxOnly&&drive.mode==='idle'; if(want!==B.on) B.set(want); return B.on; },
    set(on){ B.on=on; stage.classList.toggle('bpOn',on);
      if(on){ B.swapped=[]; B.hidden=[]; const skip=new Set(); [boxGroup,cmpGroup].forEach(g=>g.traverse(o=>skip.add(o)));
        car.traverse(o=>{ if(skip.has(o)||o.userData.bp) return;
          const m=o.material; if(o.isSprite||(o.isMesh&&m&&!Array.isArray(m)&&(m.isShaderMaterial||m.colorWrite===false||o.name==='shadow_proxy'||o===aoBlob||m.blending===THREE.AdditiveBlending))){ B.hidden.push(o); return; }
          if(!o.isMesh||Array.isArray(o.material)||o.isInstancedMesh) return;
          B.swapped.push([o,o.material]); o.material=(o.material.transparent&&o.material.opacity<0.9)?glassM:fillM;
          let ls=o.children.find(c=>c.userData.bp); if(ls) ls.visible=true; else B.queue.push(o); });
        B.pump(); }
      else { B.swapped.forEach(([o,m])=>{ o.material=m; const ls=o.children.find(c=>c.userData.bp); if(ls) ls.visible=false; }); B.swapped=[]; B.hidden=[]; B.queue=[]; }
      renderer.shadowMap.needsUpdate=true; kick(); },
    pump(){ if(B.busy) return; B.busy=true;
      const step=()=>{ const t0=performance.now();
        while(B.queue.length&&performance.now()-t0<14){ const o=B.queue.shift(); if(!B.on) break; const g=o.geometry; if(!g||!g.attributes.position) continue;
          if(!g.userData.bpE){ try{ g.userData.bpE=new THREE.EdgesGeometry(g,24); }catch(e){ continue; } }
          const ls=new THREE.LineSegments(g.userData.bpE,lineM); ls.userData.bp=1; ls.raycast=()=>{}; ls.frustumCulled=false; o.add(ls); }
        kick(); if(B.queue.length&&B.on) setTimeout(step,0); else B.busy=false; };
      setTimeout(step,30); },
    draw(){ const hid=[], hide=o=>{ if(o.visible){ o.visible=false; hid.push(o); } };
      scene.children.forEach(o=>{ if(o!==car&&!o.isLight&&o!==grid) hide(o); }); B.hidden.forEach(hide);
      const b0=scene.background, f0=scene.fog, hi=hemi.intensity, si=sun.intensity, ex=renderer.toneMappingExposure, cs=sun.castShadow;
      scene.background=bg; scene.fog=fog; grid.visible=true; hemi.intensity=1.25; sun.intensity=0.9; renderer.toneMappingExposure=1; sun.castShadow=false;
      renderer.render(scene,camera);
      hid.forEach(o=>o.visible=true); grid.visible=false; scene.background=b0; scene.fog=f0; hemi.intensity=hi; sun.intensity=si; renderer.toneMappingExposure=ex; sun.castShadow=cs; } };
  return B; })();

/* --- product thumbnails rendered from the real 3D shapes --- */
const THUMB=(()=>{ let T=null; const cache={}, wait=[]; let busy=false;
  const init=()=>{ const sc=new THREE.Scene(); sc.environment=STUDIO_ENV; sc.add(new THREE.HemisphereLight(0xffffff,0x8a8f98,0.3));
    const d=new THREE.DirectionalLight(0xffffff,0.55); d.position.set(-3,5,4); sc.add(d); const d2=new THREE.DirectionalLight(0xdfe8ff,0.18); d2.position.set(4,2,-3); sc.add(d2);
    return {sc, cam:new THREE.PerspectiveCamera(26,1.6,0.05,30), rt:new THREE.WebGLRenderTarget(400,250), cv:document.createElement('canvas')}; };
  const make=(box,fin)=>{ if(!T) T=init(); const {sc,cam,rt,cv}=T;
    const m=new THREE.MeshPhysicalMaterial({side:THREE.DoubleSide}); m.color.set(fin.hex); satBoost(m.color); m.metalness=fin.metal||0.05; m.roughness=fin.rough; m.clearcoat=fin.gloss?1:0; m.clearcoatRoughness=0.06; m.envMapIntensity=0.55;
    const g=new THREE.Group(), own=box.mesh?boxMesh(box):null, tmp=[];
    if(own){ g.add(new THREE.Mesh(own.geo,m)); if(own.lid) g.add(new THREE.Mesh(own.lid,m)); }
    else ['base','lid'].forEach(p=>{ const ge=boxPart(box.L,box.W,box.H,box.prof,p); tmp.push(ge); g.add(new THREE.Mesh(ge,m)); });
    sc.add(g); const L=M(box.L), H=M(box.H), W=M(box.W), c=new THREE.Vector3(L/2,H*0.45,0), dir=new THREE.Vector3(-0.62,0.36,0.7).normalize();
    cam.position.copy(c).addScaledVector(dir,Math.max(L*1.62,W*2.6)+0.6); cam.lookAt(c); cam.updateProjectionMatrix();
    const cc=new THREE.Color(); renderer.getClearColor(cc); const ca=renderer.getClearAlpha(), tm=renderer.toneMapping;
    renderer.setRenderTarget(rt); renderer.setClearColor(0x000000,0); renderer.clear(); renderer.render(sc,cam);
    const w=rt.width, h=rt.height, px=new Uint8Array(w*h*4); renderer.readRenderTargetPixels(rt,0,0,w,h,px);
    renderer.setRenderTarget(null); renderer.setClearColor(cc,ca); renderer.toneMapping=tm;
    sc.remove(g); tmp.forEach(x=>x.dispose()); m.dispose();
    cv.width=w; cv.height=h; const ctx=cv.getContext('2d'), im=ctx.createImageData(w,h), o=im.data, lut=new Uint8Array(256); for(let i=0;i<256;i++) lut[i]=Math.round(255*Math.pow(Math.min(1,i/255),1/2.2));
    for(let y=0;y<h;y++) for(let x=0;x<w;x++){ const s=((h-1-y)*w+x)*4, t=(y*w+x)*4, a=px[s+3]; if(!a) continue; const k=255/a; o[t]=lut[Math.min(255,Math.round(px[s]*k))]; o[t+1]=lut[Math.min(255,Math.round(px[s+1]*k))]; o[t+2]=lut[Math.min(255,Math.round(px[s+2]*k))]; o[t+3]=a; }
    ctx.putImageData(im,0,0); return cv.toDataURL('image/png'); };
  const pump=()=>{ if(busy) return; busy=true; const step=()=>{ const j=wait.shift(); if(!j){ busy=false; kick(); return; }
      const key=j[0].id+'|'+j[1].id; if(!cache[key]){ try{ if(j[0].mesh&&!boxMesh(j[0])){ if((j[2]=(j[2]||0)+1)<40) wait.push(j); setTimeout(step,250); return; } cache[key]=make(j[0],j[1]); }catch(e){ console.warn('thumb',e); cache[key]=''; } }
      document.querySelectorAll('img[data-th="'+key+'"]').forEach(i=>{ if(cache[key]) i.src=cache[key]; }); setTimeout(step,24); }; setTimeout(step,60); };
  return {attr(box,fin){ fin=fin||boxFinish(box); const key=box.id+'|'+fin.id; if(cache[key]) return 'data-th="'+key+'" src="'+cache[key]+'"';
      if(!wait.some(j=>j[0]===box&&j[1]===fin)) wait.push([box,fin]); pump(); return 'data-th="'+key+'" src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="'; }}; })();

/* --- prices: only where a shop page showed one; everything else says so --- */
const PRICE={'ed-390':[26796,'ВсеИнструменты'],'ed-420':[27260,'ВсеИнструменты'],'ed-580':[38425,'ВсеИнструменты']}, PRICE_AT='ноябрь 2026';
const rub=n=>fmt(n).replace(/ /g,' ')+' ₽';
const priceShort=b=>PRICE[b.id]?rub(PRICE[b.id][0]):'цена на сайте';
const IC_VOL='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/></svg>', IC_DIM='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 17L17 3l4 4L7 21z"/><path d="M7.5 12.5l1.5 1.5M10.5 9.5l1.5 1.5M13.5 6.5l1.5 1.5"/></svg>';

/* --- cart --- */
const CARTS={items:store.get('cart',[]),
  has(b){ const f=boxFinish(b).id; return CARTS.items.some(i=>i.id===b.id&&i.fin===f); },
  toggle(b){ const f=boxFinish(b).id, k=CARTS.items.findIndex(i=>i.id===b.id&&i.fin===f); if(k>=0) CARTS.items.splice(k,1); else CARTS.items.push({id:b.id,fin:f}); CARTS.save(); return k<0; },
  save(){ store.set('cart',CARTS.items); CARTS.render(); },
  render(){ const n=CARTS.items.length, c=$('cartCnt'); if(c){ c.hidden=!n; c.textContent=n; }
    const el=$('cartBody'); if(!el) return;
    const rows=CARTS.items.map((i,k)=>{ const b=byId(i.id); if(!b) return ''; const f=b.colors.find(c=>c.id===i.fin)||b.colors[0], sh=SHOPS[b.brand];
      return `<div class="crow"><img alt="" ${THUMB.attr(b,f)}><div><b>${b.brand} ${b.model}</b><span>${b.V} л · ${dimsTxt(b.L,b.W,b.H)} см · ${f.name}</span><span class="cp">${PRICE[b.id]?rub(PRICE[b.id][0]):'цена на сайте магазина'}</span>${sh?`<a href="${sh.url(b)}" target="_blank" rel="noopener" data-ext>Купить · ${sh.name}</a>`:''}</div><button class="cx" data-k="${k}" aria-label="Убрать ${b.brand} ${b.model} из корзины">×</button></div>`; }).join('');
    const known=CARTS.items.filter(i=>PRICE[i.id]), sum=known.reduce((s,i)=>s+PRICE[i.id][0],0), rest=n-known.length;
    el.innerHTML=n?rows+`<div class="ctot"><span>Итого${rest?' (без '+rest+' '+(rest===1?'товара':'товаров')+' с ценой на сайте)':''}</span><b>${known.length?rub(sum):'—'}</b></div><p class="fine">Цены — последние, что показывал магазин (${PRICE_AT}). Заказ оформляется на сайте магазина: приложение ничего не продаёт и не списывает.</p><button class="mini" id="cartShare">Поделиться списком</button>`
      :'<p class="cempty">Корзина пуста. Откройте карточку бокса на сцене и нажмите «В корзину».</p>';
    el.querySelectorAll('.cx').forEach(x=>x.addEventListener('click',()=>{ CARTS.items.splice(+x.dataset.k,1); CARTS.save(); if(SHOP) SHOP.sync(); }));
    el.querySelectorAll('a[data-ext]').forEach(a=>a.addEventListener('click',e=>{ if(isNativeApp()){ e.preventDefault(); location.href=a.href; } }));
    const sb=$('cartShare'); if(sb) sb.addEventListener('click',()=>{ const txt='Мой список автобоксов:\n'+CARTS.items.map(i=>{ const b=byId(i.id), f=b.colors.find(c=>c.id===i.fin)||b.colors[0], sh=SHOPS[b.brand]; return '• '+b.brand+' '+b.model+', '+b.V+' л, '+f.name+(PRICE[b.id]?', '+rub(PRICE[b.id][0]):'')+(sh?' — '+sh.url(b):''); }).join('\n');
      if(navigator.share) navigator.share({text:txt}).catch(()=>{}); else if(navigator.clipboard) navigator.clipboard.writeText(txt).then(()=>toast('<b>Список скопирован</b>','good')); }); } };

/* --- box title in the corner + product sheet --- */
const SHOP={el:$('shop'), isOpen:false,
  open(){ SHOP.isOpen=true; SHOP.el.hidden=false; stage.classList.add('shopOpen'); SHOP.sync(); const s=SHOP.el.querySelector('.pc[aria-pressed="true"]'); if(s) s.scrollIntoView({inline:'center',block:'nearest'}); kick(); },
  close(){ SHOP.isOpen=false; SHOP.el.hidden=true; stage.classList.remove('shopOpen'); kick(); },
  sync(){ const a=A(); if(!a) return;
    $('boxTitle').innerHTML=`<span class="bb">${a.brand}</span><b>${a.model}</b><span class="bs">${IC_VOL}${a.V} л</span><span class="bs">${IC_DIM}${dimsTxt(a.L,a.W,a.H)} см</span>`;
    $('boxTitle').setAttribute('aria-label','Карточка бокса '+a.brand+' '+a.model);
    if(!SHOP.isOpen) return;
    const sx0=$('shopCar').scrollLeft; $('shopCar').innerHTML=BOXES.map(b=>`<button class="pc" data-id="${b.id}" aria-pressed="${b.id===S.sel}"><img alt="" ${THUMB.attr(b)}><b>${b.model}</b><span>${b.brand} · ${b.V} л</span><span class="pr">${priceShort(b)}</span></button>`).join(''); $('shopCar').scrollLeft=sx0;
    $('shopCar').querySelectorAll('.pc').forEach(p=>p.addEventListener('click',()=>{ if(p.dataset.id===S.sel) return; selectBox(p.dataset.id); hap&&hap('tick'); }));
    const f=boxFinish(a), sh=SHOPS[a.brand], pr=PRICE[a.id], inC=CARTS.has(a);
    $('shopDet').innerHTML=`<div class="dh"><img class="dimg" alt="${a.brand} ${a.model}, ${f.name}" ${THUMB.attr(a,f)}><div><span class="br">${a.brand}</span><h3>${a.model}</h3>
      <ul class="spec"><li>Объём<b>${a.V} л</b></li><li>Снаружи<b>${dimsTxt(a.L,a.W,a.H)} см</b></li><li>Внутри<b>${dimsTxt(a.Li,a.Wi,a.Hi,a.est)} см</b></li></ul></div></div>
      <div><span class="lbl">Цвет · ${f.name}</span><div class="sws">${a.colors.map(c=>`<button class="sw" data-fin="${c.id}" title="${c.name}" aria-label="${c.name}" aria-pressed="${c.id===f.id}" style="background:${c.hex}"></button>`).join('')}</div></div>
      <div class="buyrow"><div class="price"><b${pr?'':' class="np"'}>${pr?rub(pr[0]):'Цена на сайте'}</b><small>${pr?pr[1]+', '+PRICE_AT:'магазин не показывает цену'}</small></div><button class="addc${inC?' in':''}" id="shopAdd">${CART}${inC?'В корзине · убрать':'В корзину'}</button></div>
      ${sh?`<a class="site" id="shopSite" href="${sh.url(a)}" target="_blank" rel="noopener">${CART}Открыть в магазине<span class="sh">· ${sh.name}</span></a>`:''}`;
    $('shopDet').querySelectorAll('.sw').forEach(b=>b.addEventListener('click',()=>{ S.boxColor[a.id]=b.dataset.fin; store.set('boxColor',S.boxColor); setGhost(ghost); renderBoxButtons(); renderCmpSelect(); kick(); }));
    $('shopAdd').addEventListener('click',()=>{ const added=CARTS.toggle(a); hap&&hap('click'); SHOP.sync(); if(added) toast('<b>В корзине</b>'+a.brand+' '+a.model,'good'); });
    const st=$('shopSite'); if(st) st.addEventListener('click',e=>{ if(isNativeApp()){ e.preventDefault(); location.href=st.href; } }); } };
window.SHOP=SHOP;
$('boxTitle').addEventListener('click',()=>SHOP.isOpen?SHOP.close():SHOP.open());
$('shopX').addEventListener('click',SHOP.close);
document.addEventListener('keydown',e=>{ if(e.key==='Escape'&&SHOP.isOpen) SHOP.close(); });
renderBoxButtons=(f=>function(){ f.apply(this,arguments); SHOP.sync(); })(renderBoxButtons);
setTab=(f=>function(t){ if(t!=='scene'&&SHOP.isOpen) SHOP.close(); f.apply(this,arguments); if(t==='cart') CARTS.render(); })(setTab);
CARTS.render();
applyWeatherScene();
