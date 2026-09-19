/** 非公開モードのあいだは、検索エンジンにすべて拒否を返す。
 *  正式公開時は Cloudflare Pages の環境変数に PUBLIC_INDEXABLE=true を設定する。 */
export function GET() {
  const indexable = import.meta.env.PUBLIC_INDEXABLE === 'true';
  const body = indexable
    ? 'User-agent: *\nAllow: /\n'
    : 'User-agent: *\nDisallow: /\n';
  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}
