import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    reporters: ['default'],
    pool: 'threads',
    fileParallelism: false,
  },
});
