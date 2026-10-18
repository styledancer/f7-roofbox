// Model optimisation: simplify within a tiny screen error, keep every named node, and build a light shadow-only silhouette for the cars.
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {dedup, weld, prune, simplify} from '@gltf-transform/functions';
import {MeshoptSimplifier} from 'meshoptimizer';
import fs from 'fs';
await MeshoptSimplifier.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
const tris=doc=>{ let t=0; for(const m of doc.getRoot().listMeshes()) for(const p of m.listPrimitives()){ const i=p.getIndices(); t+=(i?i.getCount():p.getAttribute('POSITION').getCount())/3; } return Math.round(t); };
const ERR=parseFloat(process.env.ERR||'0.0008');
const CFG={
  haval_f7:{err:ERR, moving:/^(wheel|boot|windscreen_r|brakelight_m)/i},
  outlander:{err:ERR, moving:/^(wheel_|tailgate)/i},
  thule_rack:{err:ERR}, touring100:{err:ERR*0.75}, rim_old:{err:ERR*1.2}, rim_steel:{err:ERR*1.2}
};
const NOSHADOW=/glass|window|wind|lens|light|lamp|chrome_light|transparent|mirror_glass/i;
fs.mkdirSync('out',{recursive:true}); const stats={};
for(const [name,c] of Object.entries(CFG)){
  const src=JSON.parse(fs.readFileSync(`www/${name}.json`,'utf8')), buf=Buffer.from(src.glb,'base64');
  const doc=await io.readBinary(new Uint8Array(buf)); const t0=tris(doc);
  await doc.transform(dedup(), weld(), simplify({simplifier:MeshoptSimplifier, ratio:0, error:c.err, lockBorder:true}), prune({keepLeaves:true, keepAttributes:true}));
  const out=await io.writeBinary(doc); const t1=tris(doc);
  fs.writeFileSync(`out/${name}.json`, JSON.stringify({...src, glb:Buffer.from(out).toString('base64')}));
  stats[name]={tris_before:t0, tris_after:t1, bytes_before:buf.length, bytes_after:out.length};
  if(c.moving){
    // shadow silhouette: every static, opaque part in one mesh, heavily simplified; moving parts keep casting their own shadow
    const d=await io.readBinary(new Uint8Array(buf)); const pos=[], idx=[];
    const walk=(n,inMoving)=>{ const mv=inMoving||c.moving.test(n.getName()); const m=n.getMesh();
      if(m&&!mv){ const W=n.getWorldMatrix();
        for(const p of m.listPrimitives()){ const mat=p.getMaterial(); if(mat&&(NOSHADOW.test(mat.getName())||mat.getAlphaMode()==='BLEND')) continue; if(NOSHADOW.test(n.getName())) continue;
          const P=p.getAttribute('POSITION'); if(!P) continue; const base=pos.length/3, v=[0,0,0];
          for(let i=0;i<P.getCount();i++){ P.getElement(i,v); const x=v[0],y=v[1],z=v[2];
            pos.push(W[0]*x+W[4]*y+W[8]*z+W[12], W[1]*x+W[5]*y+W[9]*z+W[13], W[2]*x+W[6]*y+W[10]*z+W[14]); }
          const I=p.getIndices(); if(I){ for(let i=0;i<I.getCount();i++) idx.push(base+I.getScalar(i)); } else for(let i=0;i<P.getCount();i++) idx.push(base+i); } }
      for(const ch of n.listChildren()) walk(ch,mv); };
    for(const sc of d.getRoot().listScenes()) for(const n of sc.listChildren()) walk(n,false);
    const P=new Float32Array(pos); let I=new Uint32Array(idx);
    // weld positions so the simplifier sees one surface
    const key=new Map(), remap=new Uint32Array(P.length/3), up=[]; const q=1e4;
    for(let i=0;i<P.length/3;i++){ const k=Math.round(P[3*i]*q)+','+Math.round(P[3*i+1]*q)+','+Math.round(P[3*i+2]*q); let j=key.get(k); if(j===undefined){ j=up.length/3; key.set(k,j); up.push(P[3*i],P[3*i+1],P[3*i+2]); } remap[i]=j; }
    const UP=new Float32Array(up); for(let i=0;i<I.length;i++) I[i]=remap[I[i]];
    const target=Math.floor(I.length*0.04/3)*3;
    let fin=I; for(const e of [0.01,0.02,0.04,0.08]){ const [r]=MeshoptSimplifier.simplify(I, UP, 3, target, e, []); fin=r; if(r.length<=target*1.5) break; }
    // write a tiny glb with one node "shadow_proxy"
    const {Document}=await import('@gltf-transform/core'); const od=new Document(); const b=od.createBuffer();
    const pa=od.createAccessor().setType('VEC3').setArray(UP).setBuffer(b), ia=od.createAccessor().setType('SCALAR').setArray(new Uint32Array(fin)).setBuffer(b);
    const prim=od.createPrimitive().setAttribute('POSITION',pa).setIndices(ia); const mesh=od.createMesh('shadow_proxy').addPrimitive(prim);
    od.createScene().addChild(od.createNode('shadow_proxy').setMesh(mesh));
    await od.transform(prune());
    const sb=await io.writeBinary(od); fs.writeFileSync(`out/${name}_shadow.json`, JSON.stringify({format:'glb-base64', glb:Buffer.from(sb).toString('base64')}));
    stats[name+'_shadow']={tris_source:I.length/3, tris_after:fin.length/3, bytes:sb.length};
  }
  console.log(name, JSON.stringify(stats[name]), stats[name+'_shadow']?JSON.stringify(stats[name+'_shadow']):'');
}
fs.writeFileSync('out/stats.json', JSON.stringify(stats,null,1));
