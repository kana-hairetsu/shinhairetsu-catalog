import { defineConfig } from 'astro/config';

export default defineConfig({
  // 独自ドメインを使うときは site をそのURLに書き換える
  site: 'https://example.pages.dev',
  build: { format: 'directory' },
});
