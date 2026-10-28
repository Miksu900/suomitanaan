// taxikoskela.fi – staattiset sivut; www → juuriosoite, http-otsakkeet ja välimuisti.
export default {
  async fetch(request, env) {
    const u = new URL(request.url);
    if (u.hostname === 'www.taxikoskela.fi') return Response.redirect('https://taxikoskela.fi' + u.pathname + u.search, 301);
    const res = await env.ASSETS.fetch(request);
    const h = new Headers(res.headers);
    h.set('x-content-type-options', 'nosniff');
    h.set('referrer-policy', 'strict-origin-when-cross-origin');
    if ((h.get('content-type') || '').includes('text/html')) h.set('cache-control', 'public, max-age=300');
    return new Response(res.body, { status: res.status, headers: h });
  }
};
