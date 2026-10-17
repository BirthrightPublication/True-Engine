import {createViewport, SDK_VERSION} from '../package/index.js';
const canvas = document.querySelector('#viewport');
const status = document.querySelector('#status');
const report = error => { status.textContent = `Engine error: ${error.message ?? error}`; status.className = 'error'; };
try {
  const backend = new URLSearchParams(location.search).get('backend') ?? 'auto';
  const viewport = await createViewport(canvas, {backend, onError: report});
  viewport.addPrimitive({id: 1, name: 'Cube', primitive: 'Cube', transform: {translation: [-1.1, 0, 0]}});
  viewport.loadMesh({id: 2, name: 'Indexed pyramid',
    positions: new Float32Array([-.6,-.5,-.6, .6,-.5,-.6, .6,-.5,.6, -.6,-.5,.6, 0,.7,0]),
    indices: new Uint32Array([0,2,1,0,3,2,0,1,4,1,2,4,2,3,4,3,0,4]),
    transform: {translation: [1.1, 0, 0]}, material: {color: [.9,.4,.15,1]}});
  viewport.render();
  status.textContent = `SDK ${SDK_VERSION} · ${viewport.backend} · ready`;
  // Exposed for the automated host-contract test, not an application singleton.
  window.sdkExample = {viewport, createViewport};
  canvas.addEventListener('true-engine-pick', event => { document.querySelector('#selected').textContent = `Selected: ${event.detail.id ?? 'none'}`; });
  document.querySelector('#reset').onclick = () => viewport.resetCamera();
  let green = false;
  document.querySelector('#material').onclick = () => { green = !green; viewport.setMaterial(1, {color: green ? [.15,.9,.25,1] : [.3,.65,.9,1]}); };
  document.querySelector('#save').onclick = () => {
    const url = URL.createObjectURL(new Blob([viewport.exportProject()], {type: 'application/json'}));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'true-engine-example.json'; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  document.querySelector('#open').onchange = async event => {
    const file = event.target.files[0]; if (!file) return;
    try { viewport.importProject(await file.text()); status.textContent = `Reopened ${file.name} · ${viewport.backend}`; }
    catch (error) { report(error); }
    event.target.value = '';
  };
  window.addEventListener('pagehide', () => viewport.dispose(), {once: true});
} catch (error) { report(error); console.error(error); }
