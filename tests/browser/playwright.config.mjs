import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: '.', testMatch: '*.spec.mjs', workers: 1,
  use: { baseURL: 'http://127.0.0.1:8877', viewport: {width:1440,height:1000}, trace:'retain-on-failure',
    ...(process.env.PRAXIS_BROWSER_CHANNEL?{channel:process.env.PRAXIS_BROWSER_CHANNEL}:{}) },
  webServer: { command:'python -m uvicorn praxis.api:app --host 127.0.0.1 --port 8877', cwd:'../..',
    url:'http://127.0.0.1:8877/health', reuseExistingServer:false,
    env:{PRAXIS_DB:`.test-tmp/browser-e2e-${process.pid}-${Date.now()}.db`} },
});
