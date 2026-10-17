import {defineConfig} from '@playwright/test';
import path from 'node:path';
const root = path.resolve(import.meta.dirname, '../..');
export default defineConfig({
  testDir: '.', testMatch: 'integration.spec.js', timeout: 60000, workers: 1,
  reporter: [['list'], ['json', {outputFile: `${root}/Build/sdk-browser-results.json`}]],
  use: {baseURL: 'http://127.0.0.1:8197', viewport: {width: 1100, height: 900},
    launchOptions: {executablePath: process.env.CHROMIUM_PATH || undefined,
      args: ['--no-sandbox', '--disable-dev-shm-usage', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--enable-unsafe-webgpu']},
    screenshot: 'only-on-failure', trace: 'retain-on-failure'},
  webServer: {command: `"${process.env.PYTHON || 'python3'}" -m http.server 8197 --bind 127.0.0.1 --directory "${root}/Build/sdk-web"`, url: 'http://127.0.0.1:8197/example/', reuseExistingServer: false},
  projects: (process.env.SDK_BACKENDS || 'webgl2').split(',').map(name => ({name, metadata: {backend: name}}))
});
