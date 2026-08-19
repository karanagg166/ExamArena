import { defineConfig } from 'vitest/config';
import { fileURLToPath } from 'url';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    testTimeout: 10000,
    setupFiles: ['./src/__tests__/setup.ts'],
    include: ['src/__tests__/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['e2e/**', 'node_modules/**', '.next/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/lib/**', 'src/hooks/**', 'src/stores/**', 'src/components/**'],
      exclude: ['src/__tests__/**', 'src/app/**', 'node_modules/**'],
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
});
