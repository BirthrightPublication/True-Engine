export const SDK_VERSION: '0.1.3';
export type Vec3 = [number, number, number];
export interface Transform {translation?: Vec3; rotation?: [number, number, number, number]; scale?: Vec3}
export interface Material {color: [number, number, number, number]}
export interface NodeOptions {id: number; parent?: number | null; name?: string; transform?: Transform; material?: Material}
export interface PrimitiveOptions extends NodeOptions {primitive: 'Cube' | 'Plane' | 'Sphere'}
export interface MeshOptions extends NodeOptions {positions: Float32Array; indices: Uint32Array}
export interface Camera {target: Vec3; yaw: number; pitch: number; distance: number}
export interface Viewport {
  readonly version: '0.1.3';
  readonly backend: 'webgpu' | 'webgl2';
  addPrimitive(spec: PrimitiveOptions): void;
  loadMesh(spec: MeshOptions): void;
  setMaterial(id: number, material: Material): void;
  setTransform(id: number, transform: Transform): void;
  orbit(dx: number, dy: number): void;
  pan(dx: number, dy: number): void;
  zoom(delta: number): void;
  resetCamera(): void;
  setCamera(camera: Camera): void;
  getCamera(): Camera;
  /** Physical canvas pixels, top-left origin. */
  pick(x: number, y: number): number | null;
  exportProject(): string;
  importProject(json: string): void;
  resize(width: number, height: number): void;
  render(): void;
  dispose(): void;
}
export interface ViewportOptions {
  backend?: 'auto' | 'webgpu' | 'webgl2'; controls?: boolean; autoResize?: boolean;
  onError?: (error: Error) => void;
}
export function createViewport(canvas: HTMLCanvasElement, options?: ViewportOptions): Promise<Viewport>;
