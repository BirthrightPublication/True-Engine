import init, {createRawViewport} from './true_engine_web.js';
export const SDK_VERSION = '0.1.3';
let initialized;
const activeCanvases = new WeakSet();
const identity = () => ({translation: [0, 0, 0], rotation: [0, 0, 0, 1], scale: [1, 1, 1]});
function id(value) {
  if (!Number.isInteger(value) || value < 1 || value > 0xffffffff) throw new Error('IDs must be integers in 1..4294967295');
  return value;
}
function node(spec, primitive) {
  return {id: id(spec.id), parent: spec.parent == null ? null : id(spec.parent),
    name: spec.name ?? (primitive ?? 'Mesh'), primitive,
    transform: {...identity(), ...spec.transform}, material: spec.material ?? {color: [0.3, 0.65, 0.9, 1]}};
}
function invoke(fn) {
  try { return fn(); } catch (error) { throw error instanceof Error ? error : new Error(String(error)); }
}
/** Create actual wgpu rendering on a caller-owned canvas. No DOM replacement or CSS 3D. */
export async function createViewport(canvas, options = {}) {
  if (!(canvas instanceof HTMLCanvasElement)) throw new Error('Expected an HTMLCanvasElement');
  if (canvas.width > 8192 || canvas.height > 8192) throw new Error('Initial canvas dimensions must not exceed 8192');
  if (activeCanvases.has(canvas)) throw new Error('Canvas already has an active True Engine viewport');
  activeCanvases.add(canvas);
  let raw;
  try {
    initialized ??= init().catch(error => { initialized = undefined; throw error; });
    await initialized;
    raw = await createRawViewport(canvas, options.backend ?? 'auto');
  } catch (error) {
    activeCanvases.delete(canvas);
    throw error instanceof Error ? error : new Error(String(error));
  }
  let disposed = false, frame = 0, dragging = null;
  const listeners = [];
  function check() { if (disposed) throw new Error('Viewport is disposed'); }
  function call(method, ...args) { check(); return invoke(() => raw[method](...args)); }
  function changed(method, ...args) { const result = call(method, ...args); requestRender(); return result; }
  function requestRender() {
    if (disposed || frame) return;
    frame = requestAnimationFrame(() => {
      frame = 0;
      try { api.render(); } catch (error) {
        canvas.dispatchEvent(new CustomEvent('true-engine-error', {detail: error}));
        if (options.onError) options.onError(error); else console.error(error);
      }
    });
  }
  function listen(type, handler, config) {
    canvas.addEventListener(type, handler, config);
    listeners.push(() => canvas.removeEventListener(type, handler, config));
  }
  const api = {
    version: SDK_VERSION,
    backend: raw.backend,
    addPrimitive(spec) {
      if (!['Cube', 'Plane', 'Sphere'].includes(spec.primitive)) throw new Error('Unknown primitive');
      return changed('addPrimitive', JSON.stringify(node(spec, spec.primitive)));
    },
    loadMesh(spec) {
      if (!(spec.positions instanceof Float32Array) || !(spec.indices instanceof Uint32Array)) throw new Error('Use Float32Array positions and Uint32Array indices');
      if (spec.positions.length > 3_000_000 || spec.indices.length > 3_000_000) throw new Error('Mesh exceeds SDK geometry budget');
      return changed('loadMesh', JSON.stringify(node(spec, null)), spec.positions, spec.indices);
    },
    setMaterial(nodeId, material) { return changed('setMaterial', id(nodeId), JSON.stringify(material)); },
    setTransform(nodeId, transform) { return changed('setTransform', id(nodeId), JSON.stringify({...identity(), ...transform})); },
    orbit(dx, dy) { return changed('orbit', dx, dy); },
    pan(dx, dy) { return changed('pan', dx, dy); },
    zoom(delta) { return changed('zoom', delta); },
    resetCamera() { return changed('resetCamera'); },
    setCamera(camera) { return changed('setCamera', JSON.stringify(camera)); },
    getCamera() { return JSON.parse(call('getCamera')); },
    pick(x, y) { return call('pick', x, y) ?? null; },
    exportProject() { return call('exportProject'); },
    importProject(json) { return changed('importProject', json); },
    resize(width, height) {
      check();
      if (![width, height].every(v => Number.isInteger(v) && v > 0 && v <= 8192)) throw new Error('Canvas dimensions must be integers in 1..8192');
      call('resize', width, height);
      canvas.width = width; canvas.height = height;
      requestRender();
    },
    render() { return call('render'); },
    dispose() {
      if (disposed) return;
      disposed = true; cancelAnimationFrame(frame); observer?.disconnect();
      for (const remove of listeners) remove();
      if (dragging && canvas.hasPointerCapture(dragging.pointerId)) canvas.releasePointerCapture(dragging.pointerId);
      try {
        raw.destroy();
        if (api.backend === 'webgpu') canvas.getContext('webgpu')?.unconfigure();
      } finally { raw.free(); activeCanvases.delete(canvas); }
    }
  };
  let observer;
  try {
    if (options.controls !== false) {
      listen('contextmenu', event => event.preventDefault());
      listen('pointerdown', event => {
        if (![0, 2].includes(event.button)) return;
        dragging = {pointerId: event.pointerId, button: event.button, x: event.clientX, y: event.clientY, moved: 0};
        canvas.setPointerCapture(event.pointerId); event.preventDefault(); canvas.focus();
      });
      listen('pointermove', event => {
        if (!dragging || dragging.pointerId !== event.pointerId) return;
        const dx = event.clientX - dragging.x, dy = event.clientY - dragging.y;
        dragging.x = event.clientX; dragging.y = event.clientY; dragging.moved += Math.abs(dx) + Math.abs(dy);
        if (dragging.button === 0) api.orbit(dx, dy); else api.pan(dx, dy);
      });
      listen('pointerup', event => {
        if (!dragging || dragging.pointerId !== event.pointerId) return;
        if (dragging.button === 0 && dragging.moved <= 4) {
          const rect = canvas.getBoundingClientRect();
          const selected = api.pick((event.clientX - rect.left) * canvas.width / rect.width, (event.clientY - rect.top) * canvas.height / rect.height);
          canvas.dispatchEvent(new CustomEvent('true-engine-pick', {detail: {id: selected}}));
        }
        if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
        dragging = null;
      });
      listen('lostpointercapture', () => { dragging = null; });
      listen('pointercancel', () => { dragging = null; });
      listen('wheel', event => { event.preventDefault(); api.zoom(-event.deltaY / 100); }, {passive: false});
      listen('keydown', event => { if (event.key.toLowerCase() === 'r') { api.resetCamera(); event.preventDefault(); } });
    }
    if (options.autoResize !== false) {
      observer = new ResizeObserver(() => {
        const rect = canvas.getBoundingClientRect(), ratio = Math.min(devicePixelRatio || 1, 2);
        if (rect.width <= 0 || rect.height <= 0) return;
        const width = Math.min(8192, Math.max(1, Math.round(rect.width * ratio)));
        const height = Math.min(8192, Math.max(1, Math.round(rect.height * ratio)));
        if (canvas.width !== width || canvas.height !== height) api.resize(width, height);
      });
      observer.observe(canvas);
    }
    api.render();
    return Object.freeze(api);
  } catch (error) { api.dispose(); throw error; }
}
