import { defineConfig } from 'astro/config';

export default defineConfig({
  // 独自ドメインを使うときは site をそのURLに書き換える
  site: 'https://example.pages.dev',
  build: { format: 'directory' },
  // 配列の説明（src/content/notes/*.md）は ' や " をキー名として書くので、引用符の自動変換を止める
  markdown: { smartypants: false },
});
