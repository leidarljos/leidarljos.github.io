(function () {
  var form = document.getElementById("site-search");
  var input = document.getElementById("site-search-q");
  var out = document.getElementById("site-search-results");
  if (!form || !input || !out) return;

  var index = null;
  function load() {
    if (index) return Promise.resolve(index);
    return fetch("/search-index.json")
      .then(function (r) { return r.json(); })
      .then(function (j) { index = j.docs || []; return index; });
  }

  function score(doc, words) {
    var hay = (doc.title + " " + doc.text).toLowerCase();
    var s = 0;
    for (var i = 0; i < words.length; i++) {
      var w = words[i];
      if (!w) continue;
      var t = doc.title.toLowerCase().indexOf(w);
      var b = hay.indexOf(w);
      if (b < 0) return 0;
      s += t >= 0 ? 8 : 1;
    }
    return s;
  }

  function snippet(text, words) {
    var low = text.toLowerCase();
    var at = 0;
    for (var i = 0; i < words.length; i++) {
      var p = low.indexOf(words[i]);
      if (p >= 0) { at = Math.max(0, p - 40); break; }
    }
    var cut = text.slice(at, at + 180).replace(/\s+/g, " ");
    return (at > 0 ? "…" : "") + cut + (at + 180 < text.length ? "…" : "");
  }

  function render(q) {
    var words = q.toLowerCase().trim().split(/\s+/).filter(Boolean);
    if (!words.length) {
      out.innerHTML = "";
      return;
    }
    load().then(function (docs) {
      var hits = docs
        .map(function (d) { return { d: d, s: score(d, words) }; })
        .filter(function (h) { return h.s > 0; })
        .sort(function (a, b) { return b.s - a.s; })
        .slice(0, 20);
      if (!hits.length) {
        out.innerHTML = "<p class=\"quiet\">No pages matched.</p>";
        return;
      }
      out.innerHTML = hits.map(function (h) {
        return "<a class=\"search-hit\" href=\"" + h.d.url + "\"><strong>" +
          h.d.title.replace(/</g, "&lt;") + "</strong><span>" +
          snippet(h.d.text, words).replace(/</g, "&lt;") + "</span></a>";
      }).join("");
    });
  }

  var q = new URLSearchParams(location.search).get("q") || "";
  if (q) { input.value = q; render(q); }
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var v = input.value.trim();
    history.replaceState(null, "", "/docs/search/" + (v ? "?q=" + encodeURIComponent(v) : ""));
    render(v);
  });
  input.addEventListener("input", function () { render(input.value); });
})();
