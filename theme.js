// Colour scheme switch. The choice cycles system -> light -> dark and is
// kept in localStorage._theme, the key the project docs (Shibuya) use, so
// one choice holds across leidarljos.github.io. The inline head script
// applies it before first paint; this file wires the button.
(function () {
  var order = ["auto", "light", "dark"];
  var next = { auto: "light", light: "dark", dark: "system" };
  var name = { auto: "system", light: "light", dark: "dark" };
  var root = document.documentElement;
  function current() {
    var t = root.getAttribute("data-theme");
    return t === "light" || t === "dark" ? t : "auto";
  }
  function paint(btn, mode) {
    var label = "Colour scheme: " + name[mode] + ". Switch to " + next[mode] + ".";
    btn.setAttribute("aria-label", label);
    btn.setAttribute("title", label);
  }
  var bar = { light: "#F6F2E8", dark: "#0B0B0A" };
  function tint(mode) {
    document.querySelectorAll('meta[name="theme-color"]').forEach(function (m) {
      if (!m.dataset.media) m.dataset.media = m.getAttribute("media") || "";
      if (mode === "auto") m.setAttribute("media", m.dataset.media);
      else { m.setAttribute("content", bar[mode]); m.removeAttribute("media"); }
      if (mode === "auto") m.setAttribute("content", /light/.test(m.dataset.media) ? bar.light : bar.dark);
    });
  }
  function apply(mode) {
    if (mode === "auto") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", mode);
    try { localStorage._theme = mode; } catch (e) {}
    tint(mode);
  }
  tint(current());
  document.querySelectorAll("[data-theme-switch]").forEach(function (btn) {
    btn.hidden = false;
    paint(btn, current());
    btn.addEventListener("click", function () {
      var mode = order[(order.indexOf(current()) + 1) % order.length];
      apply(mode);
      document.querySelectorAll("[data-theme-switch]").forEach(function (b) { paint(b, mode); });
    });
  });
})();
