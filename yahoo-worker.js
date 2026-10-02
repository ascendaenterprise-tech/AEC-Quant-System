// Optional faster feed: a Cloudflare Worker that reads Yahoo Finance server-side and answers with CORS headers.
// Deploy: Cloudflare dashboard > Workers & Pages > Create > paste this > Deploy. Then on each page, before aec-yahoo.js:
//   <script>window.AEC_YAHOO_API='https://YOUR-WORKER.workers.dev/';window.AEC_YAHOO_SYMBOLS=[...];</script>
// (AEC_YAHOO_SYMBOLS = the contents of yahoo_symbols.json.) Results are cached 10 seconds at the edge.
const UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36'};
const OK = /^[A-Za-z0-9.^=\-]{1,20}$/;
async function one(sym) {
  const r = await fetch('https://query1.finance.yahoo.com/v8/finance/chart/' + encodeURIComponent(sym) + '?range=1d&interval=5m&includePrePost=true', {headers: UA, cf: {cacheTtl: 10, cacheEverything: true}});
  const d = await r.json(); const res = d.chart && d.chart.result && d.chart.result[0]; if (!res) return null;
  const m = res.meta, q = (res.indicators.quote || [{}])[0], c = (q.close || []).filter(x => x != null);
  const sp = c.length <= 120 ? c : Array.from({length: 120}, (_, i) => c[Math.floor(i * (c.length - 1) / 119)]);
  return {p: m.regularMarketPrice, pc: m.chartPreviousClose || m.previousClose, h: m.regularMarketDayHigh, l: m.regularMarketDayLow, t: m.regularMarketTime, st: m.marketState, ccy: m.currency, spark: sp};
}
export default {
  async fetch(req) {
    const cors = {'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json', 'Cache-Control': 'public, max-age=10'};
    const syms = (new URL(req.url).searchParams.get('symbols') || '').split(',').filter(s => OK.test(s)).slice(0, 80);
    const quotes = {}; await Promise.all(syms.map(async s => { try { const v = await one(s); if (v && v.p != null) quotes[s] = v; } catch (e) {} }));
    return new Response(JSON.stringify({source: 'Yahoo Finance', asof: new Date().toISOString(), quotes}), {headers: cors});
  }
};
