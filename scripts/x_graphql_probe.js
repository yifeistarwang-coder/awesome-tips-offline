/* Probe the X web app for the current TweetDetail GraphQL queryId and bearer token.
 * Runs in the page context (x.com) so bundles are same-origin.
 * Result is written to window.__probe as a JSON string:
 *   {"queryId": "...", "bearer": "..."} or {"error": "..."}
 */
window.__probe = 'PENDING';
(async function () {
  try {
    var urls = [].slice.call(document.querySelectorAll('script[src]'))
      .map(function (s) { return s.src; })
      .filter(function (u) { return u.indexOf('https://abs.twimg.com/responsive-web/') === 0; });
    var ops = {};
    var bearer = null;
    for (var i = 0; i < urls.length; i++) {
      try {
        var txt = await (await fetch(urls[i])).text();
        var m;
        var re1 = /queryId:\s*"([^"]+)",\s*operationName:\s*"([^"]+)"/g;
        while ((m = re1.exec(txt))) ops[m[2]] = m[1];
        var re2 = /operationName:\s*"([^"]+)",\s*queryId:\s*"([^"]+)"/g;
        while ((m = re2.exec(txt))) ops[m[1]] = m[2];
        var bt = txt.match(/Bearer\s+(A{10,}[A-Za-z0-9%_=-]{20,})/);
        if (bt && !bearer) bearer = bt[1];
      } catch (e) { /* ignore individual bundle failures */ }
    }
    window.__probe = JSON.stringify({ queryId: ops.TweetDetail || null, bearer: bearer });
  } catch (e) {
    window.__probe = JSON.stringify({ error: String(e && e.message || e) });
  }
})();
'probe-started'
