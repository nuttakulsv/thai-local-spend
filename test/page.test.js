const { JSDOM, VirtualConsole } = require("jsdom");
const fs = require("fs"), path = require("path"), assert = require("assert");
const ROOT = process.argv[2];
const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
const vc = new VirtualConsole(); const errors = [];
vc.on("jsdomError", (e) => errors.push(String(e.message || e))); vc.on("error", (e) => errors.push(String(e)));
const dom = new JSDOM(html, { runScripts: "dangerously", url: "http://localhost/", virtualConsole: vc,
  beforeParse(w) {
    w.fetch = async (u) => { const p = path.join(ROOT, decodeURIComponent(new URL(u, "http://localhost/").pathname));
      return fs.existsSync(p) ? { ok: true, json: async () => JSON.parse(fs.readFileSync(p, "utf8")) } : { ok: false, status: 404 }; };
    w.scrollTo = () => {};
  } });
const w = dom.window, d = w.document;
const tick = (ms = 400) => new Promise((r) => setTimeout(r, ms));
const text = () => d.querySelector("#main").textContent;
(async () => {
  await tick();
  assert(text().includes("เลือกจังหวัด"), "country view");
  const provs = d.querySelectorAll("#prov option").length; assert(provs > 70, "province options " + provs);
  w.location.hash = encodeURIComponent("เชียงใหม่"); await tick();
  assert(text().includes("เลือกอำเภอ"), "province view"); assert(!d.querySelector("#dist").disabled);
  const idx = JSON.parse(fs.readFileSync(path.join(ROOT, "data/index.json")));
  const dist = Object.keys(idx.provinces["เชียงใหม่"])[0];
  w.location.hash = encodeURIComponent("เชียงใหม่") + "/" + encodeURIComponent(dist); await tick();
  assert(text().includes("หน่วยงานที่จ้างมากที่สุด"), "district view");
  const items = d.querySelectorAll(".item").length; assert(items > 0, "items " + items);
  assert(d.title.startsWith(dist), "title " + d.title);
  // click the top unit: list filters to that unit
  const first = d.querySelector(".rank li .nm").textContent; d.querySelector(".rank li").click(); await tick(50);
  assert([...d.querySelectorAll(".item .meta")].every((m) => m.textContent.includes(first)), "unit filter");
  assert(d.querySelector(".chip").textContent.includes(first), "chip shown");
  d.querySelector(".chip").click(); await tick(50);
  // search
  const inp = d.querySelector("input[type=search]"); inp.value = "zzzz-not-there"; inp.dispatchEvent(new w.Event("input")); await tick(300);
  assert(text().includes("ไม่พบสัญญา"), "empty search");
  // a project name with markup must stay text
  assert(!d.querySelector("#main script"), "no injected script");
  // Bangkok has persons masked
  w.location.hash = encodeURIComponent("กรุงเทพมหานคร") + "/" + encodeURIComponent("ราชเทวี"); await tick();
  assert(text().includes("ราชเทวี") || d.title.includes("ราชเทวี"));
  w.location.hash = "nonsense/x"; await tick(); assert(text().includes("เลือกจังหวัด"), "bad hash -> country");
  console.log("page ok;", errors.length ? "errors: " + errors.join(" | ") : "no script errors");
})().catch((e) => { console.error("FAIL", e.message, errors); process.exit(1); });
