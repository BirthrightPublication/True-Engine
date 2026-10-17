import {test, expect} from '@playwright/test';
import {PNG} from 'pngjs';
import fs from 'node:fs/promises';
const settle = page => page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
async function pixels(page) { await settle(page); return PNG.sync.read(await page.locator('canvas').first().screenshot()); }
function changed(a,b) {
  let count = 0; for (let i=0; i<a.data.length; i+=4) if (Math.abs(a.data[i]-b.data[i])+Math.abs(a.data[i+1]-b.data[i+1])+Math.abs(a.data[i+2]-b.data[i+2])>30) count++;
  return count;
}
function count(image,predicate) { let n=0; for(let i=0;i<image.data.length;i+=4) if(predicate(...image.data.subarray(i,i+3))) n++; return n; }
test.beforeEach(async ({page}, info) => {
  const errors=[]; page.on('pageerror',e=>errors.push(e.message)); page.on('console',m=>{if(m.type()==='error') errors.push(m.text());});
  page.engineErrors=errors;
  await page.goto(`/example/?backend=${info.project.metadata.backend}`);
  await expect(page.locator('#status')).toContainText('ready');
});
test.afterEach(async({page}) => { expect(page.engineErrors).toEqual([]); });

test('loads compiled SDK and renders real primitive and custom mesh pixels', async({page},info) => {
  expect(await page.evaluate(()=>window.sdkExample.viewport.backend)).toBe(info.project.metadata.backend);
  expect(await page.evaluate(()=>getComputedStyle(document.querySelector('canvas')).transform)).toBe('none');
  const response=await page.request.get('/package/true_engine_web_bg.wasm');
  expect(response.status()).toBe(200); expect(response.headers()['content-type']).toContain('application/wasm');
  const bytes=await response.body(); expect([...bytes.subarray(0,4)]).toEqual([0,97,115,109]);
  const image=await pixels(page);
  expect(count(image,(r,g,b)=>b>r*1.3 && b>70)).toBeGreaterThan(1000);
  expect(count(image,(r,g,b)=>r>g*1.4 && r>b*1.4 && r>80)).toBeGreaterThan(1000);
});
test('material and transform updates change GPU output', async({page}) => {
  const before=await pixels(page);
  await page.locator('#material').click(); const after=await pixels(page);
  expect(changed(before,after)).toBeGreaterThan(1000);
  expect(count(after,(r,g,b)=>g>r*1.4 && g>b*1.4 && g>80)).toBeGreaterThan(1000);
  await page.evaluate(()=>window.sdkExample.viewport.setTransform(2,{translation:[1.1,1,0],scale:[1.5,.5,1]}));
  expect(changed(after,await pixels(page))).toBeGreaterThan(1000);
});
test('loads indexed triangle geometry and picks its actual triangles',async({page})=>{
  await page.evaluate(()=>{
    const v=window.sdkExample.viewport;
    v.setCamera({target:[0,0,0],yaw:0,pitch:0,distance:4});
    v.loadMesh({id:3,name:'test triangle',positions:new Float32Array([-0.6,-0.6,1,0.6,-0.6,1,0,0.6,1]),indices:new Uint32Array([0,1,2]),material:{color:[1,0,0,1]}});
    v.render();
  });
  const image=await pixels(page); expect(count(image,(r,g,b)=>r>80&&g<10&&b<10)).toBeGreaterThan(2000);
  const hit=await page.evaluate(()=>{const c=document.querySelector('canvas');return window.sdkExample.viewport.pick(c.width/2,c.height/2);}); expect(hit).toBe(3);
  await page.locator('canvas').click({position:{x:500,y:240}});
  await expect(page.locator('#selected')).toHaveText('Selected: 3');
});
test('mouse orbit, pan, wheel and keyboard reset control the real camera',async({page})=>{
  const initial=await page.evaluate(()=>window.sdkExample.viewport.getCamera()), before=await pixels(page);
  const bounds=await page.locator('canvas').boundingBox(); const x=bounds.x+450,y=bounds.y+230;
  await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x+85,y+30,{steps:5});await page.mouse.up();
  const orbited=await page.evaluate(()=>window.sdkExample.viewport.getCamera());expect(orbited.yaw).not.toBe(initial.yaw);
  expect(changed(before,await pixels(page))).toBeGreaterThan(1500);
  await page.mouse.down({button:'right'});await page.mouse.move(x+110,y+65,{steps:5});await page.mouse.up({button:'right'});
  expect((await page.evaluate(()=>window.sdkExample.viewport.getCamera())).target).not.toEqual(initial.target);
  await page.mouse.wheel(0,-150); expect((await page.evaluate(()=>window.sdkExample.viewport.getCamera())).distance).toBeLessThan(initial.distance);
  await page.locator('canvas').press('r');expect(await page.evaluate(()=>window.sdkExample.viewport.getCamera())).toEqual(initial);
  expect(changed(before,await pixels(page))).toBe(0);
});
test('file save and reopen restores geometry, material and camera',async({page},info)=>{
  const before=await pixels(page);const original=await page.evaluate(()=>window.sdkExample.viewport.exportProject());
  const downloading=page.waitForEvent('download');await page.locator('#save').click();const download=await downloading;
  const file=info.outputPath('project.json');await download.saveAs(file);
  expect(JSON.parse(await fs.readFile(file,'utf8'))).toEqual(JSON.parse(original));
  await page.evaluate(()=>{const v=window.sdkExample.viewport;v.orbit(80,20);v.setMaterial(2,{color:[0,1,0,1]});});
  expect(changed(before,await pixels(page))).toBeGreaterThan(1500);
  await page.locator('#open').setInputFiles(file);await expect(page.locator('#status')).toContainText('Reopened');
  expect(JSON.parse(await page.evaluate(()=>window.sdkExample.viewport.exportProject()))).toEqual(JSON.parse(original));
  expect(changed(before,await pixels(page))).toBe(0);
});
test('invalid meshes, IDs and unknown formats preserve the current scene',async({page})=>{
  const result=await page.evaluate(()=>{
    const v=window.sdkExample.viewport,before=v.exportProject(),errors=[];
    for(const fn of [()=>v.loadMesh({id:3,positions:new Float32Array([0,0,0]),indices:new Uint32Array([0,1,2])}),()=>v.addPrimitive({id:1,primitive:'Cube'}),()=>v.addPrimitive({id:-1,primitive:'Cube'}),()=>v.setMaterial(1,{color:[NaN,0,0,1]}),()=>v.setCamera({target:[0,0,0],yaw:0,pitch:0,distance:0}),()=>v.importProject('{"format":"true-engine-web-project","format_version":99}'),()=>v.resize(0,100)]){
      try {fn(); errors.push(false);} catch(error) {errors.push(error instanceof Error);}
    }
    return {errors,unchanged:v.exportProject()===before};
  });expect(result.errors).toEqual(Array(7).fill(true));expect(result.unchanged).toBe(true);
});
test('camera boundary and initial size errors leave the host reusable',async({page})=>{
  const result=await page.evaluate(async()=>{
    const {viewport:v,createViewport}=window.sdkExample;
    v.setCamera({target:[1000000,0,0],yaw:0,pitch:0,distance:1000});
    const before=v.exportProject();let bounded=false;try{v.pan(-1,0);}catch{bounded=true;}
    const unchanged=before===v.exportProject();v.resetCamera();
    const c=document.createElement('canvas');c.width=100000;c.height=20;
    let oversized=false;try{await createViewport(c,{backend:v.backend,autoResize:false});}catch{oversized=true;}
    c.width=100;c.height=100;document.body.append(c);
    const recovered=await createViewport(c,{backend:v.backend,autoResize:false});recovered.render();recovered.dispose();
    return{bounded,unchanged,oversized};
  });expect(result).toEqual({bounded:true,unchanged:true,oversized:true});
});
test('resizes, isolates multiple host-owned canvases and disposes resources',async({page})=>{
  const state=await page.evaluate(async()=>{
    const {viewport:v,createViewport}=window.sdkExample;
    const c=document.createElement('canvas');c.width=200;c.height=200;document.body.append(c);
    const second=await createViewport(c,{backend:v.backend,controls:false,autoResize:false});
    second.addPrimitive({id:1,primitive:'Sphere'});second.resize(240,180);second.render();
    let duplicateRejected=false;try{await createViewport(c);}catch{duplicateRejected=true;}
    const backend=second.backend; second.dispose();second.dispose();
    let disposedRejected=false;try{second.render();}catch{disposedRejected=true;}
    const recreated=await createViewport(c,{backend,controls:false,autoResize:false});
    recreated.addPrimitive({id:1,primitive:'Cube'});recreated.render();recreated.dispose();
    v.render();return{duplicateRejected,disposedRejected,width:c.width,height:c.height,backend,firstNodes:JSON.parse(v.exportProject()).project.scene.nodes.length};
  });expect(state).toMatchObject({duplicateRejected:true,disposedRejected:true,width:240,height:180,firstNodes:2});
});
