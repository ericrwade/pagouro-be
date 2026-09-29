"""Emit the human-scoring page (an Artifact) for the 40-image blind sample. Images are inlined as
data URIs from manifest_b64.json; the page never says which arm made a picture. Answers are encoded
into one short code the scorer pastes back; score_human.py decodes it against the judge's verdicts.

    python scripts/make_scoring_page.py --sample evals/results/round1/human_sample --out <path.html>
"""
from __future__ import annotations
import argparse, html, io, json, os, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    items = json.load(open(os.path.join(a.sample, "manifest_b64.json"), encoding="utf-8"))
    cards = []
    for it in items:
        n = it["n"]
        text_block = ""
        if it["expect_text"]:
            text_block = f"""
        <div class="q" data-q="text">
          <span class="ql">Are the asked-for words legible?</span>
          <span class="seg"><button type="button" data-v="Y">Yes</button><button type="button" data-v="N">No</button></span>
        </div>"""
        cards.append(f"""
    <article class="card" id="card-{n:02d}" data-n="{n:02d}" data-text="{'1' if it['expect_text'] else '0'}">
      <div class="num">{n + 1} <span>of 40</span></div>
      <img src="data:image/jpeg;base64,{it['b64']}" alt="picture {n + 1}" width="384" height="384" loading="lazy">
      <div class="body">
        <p class="cap">{html.escape(it['caption'])}</p>
        <div class="q" data-q="subject">
          <span class="ql">Is that what the picture shows?</span>
          <span class="seg"><button type="button" data-v="Y">Yes</button><button type="button" data-v="N">No</button></span>
        </div>
        <div class="q" data-q="style">
          <span class="ql">Does it look like a lithographic poster of about 1900?</span>
          <span class="seg"><button type="button" data-v="Y">Yes</button><button type="button" data-v="N">No</button></span>
        </div>{text_block}
      </div>
    </article>""")
    page = f"""<title>Pagouro BE Scoring</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=Source+Sans+3:wght@400;600&display=swap">
<style>
:root {{
  --stock: #f3ead8; --stock-2: #e9dcc2; --ink: #2a2118; --ink-2: #5e5245; --rule: #cdbfa3;
  --vermilion: #c8412b; --prussian: #1f3a63; --gold: #b8892b; --yes: #2f6b3a; --no: #a12e22;
  --card: #fbf6ea;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --stock: #1e1a15; --stock-2: #2a241c; --ink: #efe6d2; --ink-2: #bdb09a; --rule: #4a4033;
  --vermilion: #e2634d; --prussian: #7ea0d6; --gold: #d3a54a; --yes: #6fbf7c; --no: #e07a6e; --card: #26211a; color-scheme: dark;
}} }}
:root[data-theme="dark"] {{
  --stock: #1e1a15; --stock-2: #2a241c; --ink: #efe6d2; --ink-2: #bdb09a; --rule: #4a4033;
  --vermilion: #e2634d; --prussian: #7ea0d6; --gold: #d3a54a; --yes: #6fbf7c; --no: #e07a6e; --card: #26211a; color-scheme: dark;
}}
body {{ background: var(--stock); color: var(--ink); font: 16px/1.5 "Source Sans 3", "Segoe UI", system-ui, sans-serif; margin: 0; padding-block: 0 48px; padding-inline: 16px; }}
.wrap {{ max-width: 760px; margin: 0 auto; }}
header {{ position: sticky; top: env(safe-area-inset-top, 0px); background: var(--stock); border-bottom: 2px solid var(--ink); padding-block: 12px 10px; z-index: 2; }}
h1 {{ font: 700 26px/1.1 "Playfair Display", Georgia, serif; margin: 0 0 4px; letter-spacing: .01em; text-wrap: balance; }}
.sub {{ color: var(--ink-2); margin: 0; font-size: 15px; }}
.prog {{ display: flex; align-items: center; gap: 10px; margin-top: 8px; font-variant-numeric: tabular-nums; font-weight: 600; }}
.bar {{ flex: 1; height: 8px; background: var(--stock-2); border: 1px solid var(--rule); }}
.bar i {{ display: block; height: 100%; width: 0; background: var(--vermilion); transition: width .2s; }}
.intro {{ margin: 18px 0 22px; padding: 12px 14px; border-left: 4px solid var(--prussian); background: var(--card); }}
.intro p {{ margin: 0 0 6px; }}
.card {{ display: grid; grid-template-columns: 240px 1fr; gap: 16px; background: var(--card); border: 1px solid var(--rule); padding: 14px; margin-bottom: 18px; }}
.card img {{ width: 100%; height: auto; max-width: 100%; border: 1px solid var(--rule); background: var(--stock-2); }}
.num {{ grid-column: 1 / -1; font: 700 15px "Playfair Display", Georgia, serif; color: var(--prussian); letter-spacing: .04em; }}
.num span {{ color: var(--ink-2); font-weight: 500; }}
.cap {{ margin: 0 0 12px; font: 500 19px/1.3 "Playfair Display", Georgia, serif; text-wrap: balance; }}
.q {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px 12px; padding: 8px 0; border-top: 1px dashed var(--rule); }}
.ql {{ flex: 1 1 220px; }}
.seg {{ display: inline-flex; border: 1.5px solid var(--ink); }}
.seg button {{ font: 600 15px "Source Sans 3", system-ui, sans-serif; background: transparent; color: var(--ink); border: 0; padding: 6px 16px; cursor: pointer; min-width: 64px; }}
.seg button + button {{ border-left: 1.5px solid var(--ink); }}
.seg button:focus-visible {{ outline: 3px solid var(--gold); outline-offset: 2px; }}
.seg button.on[data-v="Y"] {{ background: var(--yes); color: #fff; }}
.seg button.on[data-v="N"] {{ background: var(--no); color: #fff; }}
.card.done {{ border-color: var(--gold); }}
.result {{ background: var(--card); border: 2px solid var(--ink); padding: 14px; margin-top: 8px; }}
.result h2 {{ font: 700 20px "Playfair Display", Georgia, serif; margin: 0 0 6px; }}
.result textarea {{ width: 100%; box-sizing: border-box; font: 14px/1.4 ui-monospace, Consolas, monospace; min-height: 96px; background: var(--stock); color: var(--ink); border: 1px solid var(--rule); padding: 8px; }}
.result .row {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-top: 8px; }}
.result button {{ font: 600 15px "Source Sans 3", system-ui, sans-serif; background: var(--vermilion); color: #fff; border: 0; padding: 8px 18px; cursor: pointer; }}
.result button:focus-visible {{ outline: 3px solid var(--gold); outline-offset: 2px; }}
.note {{ color: var(--ink-2); font-size: 14px; }}
@media (max-width: 560px) {{ .card {{ grid-template-columns: 1fr; }} .card img {{ max-width: 320px; }} }}
@media (prefers-reduced-motion: reduce) {{ .bar i {{ transition: none; }} }}
</style>
<div class="wrap">
  <header>
    <h1>Pagouro BE scoring sheet</h1>
    <p class="sub">Round 1 gate. Forty pictures, shuffled, from three models you are not told apart. Two or three yes/no answers each.</p>
    <div class="prog"><span id="count">0 / 40</span><div class="bar"><i id="fill"></i></div></div>
  </header>
  <div class="intro">
    <p><strong>Subject:</strong> yes if the main thing the caption asks for is recognisably there. A crab that looks like a lobster is a no. A cat that is clearly a cat is a yes even if the pose is off.</p>
    <p><strong>Style:</strong> yes if it reads as a lithographic poster of about 1900 (flat colour, bold outline, poster paper); no if it looks like a photo, a 3D render or a modern digital painting.</p>
    <p><strong>Words</strong> (six pictures): yes only if you can actually read the word the caption asked for.</p>
    <p class="note">Your answers are kept in this browser as you go. When the counter reads 40 / 40, copy the code at the bottom and paste it to me.</p>
  </div>
{''.join(cards)}
  <section class="result" id="result">
    <h2>Your code</h2>
    <p class="note" id="rnote">Answer every question above; the code fills in as you go.</p>
    <textarea id="code" readonly></textarea>
    <div class="row"><button type="button" id="copy">Copy code</button><span class="note" id="copied"></span></div>
  </section>
</div>
<script>
(function() {{
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var state = {{}};
  try {{ state = JSON.parse(localStorage.getItem('be_round1_scores') || '{{}}') || {{}}; }} catch (e) {{ state = {{}}; }}
  function save() {{ try {{ localStorage.setItem('be_round1_scores', JSON.stringify(state)); }} catch (e) {{}} }}
  function keyOf(card, q) {{ return card.dataset.n + ':' + q; }}
  function render() {{
    var done = 0, parts = [];
    cards.forEach(function(card) {{
      var n = card.dataset.n, qs = card.querySelectorAll('.q'), complete = true, code = n;
      qs.forEach(function(q) {{
        var v = state[keyOf(card, q.dataset.q)];
        q.querySelectorAll('button').forEach(function(b) {{ b.classList.toggle('on', b.dataset.v === v); }});
        if (!v) complete = false;
        code += v || '_';
      }});
      if (card.dataset.text === '0') code += '-';
      card.classList.toggle('done', complete);
      if (complete) done++;
      parts.push(code);
    }});
    document.getElementById('count').textContent = done + ' / 40';
    document.getElementById('fill').style.width = (done / 40 * 100) + '%';
    document.getElementById('code').value = 'BE1 ' + parts.join(' ');
    document.getElementById('rnote').textContent = done === 40 ? 'All forty answered. Copy the code and paste it to me.' : ('Answered ' + done + ' of 40 so far; the code updates as you go.');
  }}
  cards.forEach(function(card) {{
    card.querySelectorAll('.q').forEach(function(q) {{
      q.querySelectorAll('button').forEach(function(b) {{
        b.addEventListener('click', function() {{ state[keyOf(card, q.dataset.q)] = b.dataset.v; save(); render(); }});
      }});
    }});
  }});
  document.getElementById('copy').addEventListener('click', function() {{
    var ta = document.getElementById('code'), msg = document.getElementById('copied');
    var done = function() {{ msg.textContent = 'Copied.'; setTimeout(function() {{ msg.textContent = ''; }}, 2000); }};
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(ta.value).then(done, function() {{ ta.focus(); ta.select(); msg.textContent = 'Select the text and copy it.'; }});
    }} else {{ ta.focus(); ta.select(); msg.textContent = 'Select the text and copy it.'; }}
  }});
  render();
}})();
</script>
"""
    io.open(a.out, "w", encoding="utf-8", newline="\n").write(page)
    print("wrote", a.out, len(page) // 1024, "KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
