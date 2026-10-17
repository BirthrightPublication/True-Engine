import {createViewport, type Camera, type Viewport} from '../../Build/sdk-web/package/index.js';
async function host(canvas: HTMLCanvasElement): Promise<Viewport> {
  const viewport = await createViewport(canvas, {backend:'auto', controls:true});
  viewport.addPrimitive({id:1, primitive:'Cube', material:{color:[1,0,0,1]}});
  viewport.loadMesh({id:2, positions:new Float32Array([0,0,0,1,0,0,0,1,0]), indices:new Uint32Array([0,1,2])});
  viewport.setTransform(2,{translation:[0,0,1]});
  const camera:Camera=viewport.getCamera();viewport.setCamera(camera);
  const hit:number|null=viewport.pick(100,100);void hit;
  viewport.importProject(viewport.exportProject());return viewport;
}
void host;
