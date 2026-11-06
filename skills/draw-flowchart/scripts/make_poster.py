#!/usr/bin/env python3
"""Render a flowchart / state diagram (flow.mmd + poster.json) as a paper-style poster.

Usage:
    make_poster.py <folder>                         check, write poster.html, export poster.png + poster.svg
    make_poster.py <folder> --check                 check only
    make_poster.py <folder> --no-png                write poster.html only
    make_poster.py <folder> --init [--lang zh]      create a starter flow.mmd + poster.json
    make_poster.py <folder> --from-statechart <chart.mmd> [--force]
                                                    convert a chart.mmd made by pstack's /statechart into flow.mmd

The folder holds:
    flow.mmd      Mermaid source (rules: references/mermaid-rules.md)
    poster.json   title, legend, photos, problem card (fields: references/poster-json.md)

Rendering uses only the bundled template and dagre, so the same input always gives the same poster.
PNG/SVG export drives a local Chrome / Edge / Chromium in headless mode; without one, only the HTML is written.
Standard library only; Pillow is used to shrink photos when it is installed.
"""
import argparse
import base64
import io
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL / "assets" / "template.html"
DAGRE = SKILL / "assets" / "vendor" / "dagre-0.8.5.min.js"
PALETTE = {"blue", "cream", "lavender", "wood", "sage", "breaks"}
# pstack statechart colour classes -> this palette
STATECHART_COLORS = {"blue": "blue", "teal": "cream", "yellow": "cream", "purple": "lavender",
                     "pink": "lavender", "tan": "wood", "orange": "wood"}
MAX_NODE_CHARS = 26     # in display units: a Chinese character = 1, a Latin letter or space = 0.55
MAX_EDGE_CHARS = 24
MAX_NODES = 30
PHOTO_MAX_PX = 480


def chrome_candidates():
    pf = [os.environ.get(k, "") for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
    names = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "msedge", "chrome"]
    return [
        os.environ.get("CHROME", ""),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        *[shutil.which(n) or "" for n in names],
        *[str(Path(p) / "Google/Chrome/Application/chrome.exe") for p in pf if p],
        *[str(Path(p) / "Microsoft/Edge/Application/msedge.exe") for p in pf if p],
    ]


# ---------------------------------------------------------------- checking
ID = r"[\w\-.]+"
RE_STATE_EDGE = re.compile(rf"^(\[\*\]|{ID})\s*-->\s*(\[\*\]|{ID})\s*(?::\s*(.*))?$")
RE_STATE_NODE = re.compile(rf"^({ID})\s*:\s*(.+)$")
RE_BARE_ID = re.compile(rf"^({ID})$")
RE_FLOW_EDGE1 = re.compile(r"^(.+?)\s*--\s+([^>]+?)\s+-->\s*(.+)$")
RE_FLOW_EDGE2 = re.compile(r"^(.+?)\s*(?:-->|==>|-\.->|---)\s*(?:\|([^|]*)\|)?\s*(.+)$")
RE_FLOW_NODE = re.compile(rf"^({ID})\s*(.*)$")
RE_CLASS = re.compile(r"^class\s+(\S+)\s+(\S+)$")
RE_CLASSDEF = re.compile(r"^classDef\s+(\S+)\s+(.+)$")
SKIP = re.compile(r"^(direction\s|style\s|linkStyle|click\s)")
UNSUPPORTED = re.compile(r"^(state\s|note\s|\}|end$|subgraph|--$)")


def display_len(text):
    """Rough printed width: CJK characters count 1, everything else 0.55 (both fonts are about that ratio)."""
    return sum(1 if re.match(r"[\u2e80-\u9fff\uf900-\ufaff\uff00-\uffef\u3000-\u303f]", ch) else 0.55 for ch in text)


def strip_front_matter(lines):
    if lines and lines[0].strip() == "---":
        end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == "---"), 0)
        return [""] * (end + 1) + lines[end + 1:]
    return lines


def check_mermaid(text):
    """Check the source against what the renderer supports. Returns (errors, warnings, stats)."""
    errors, warns = [], []
    lines = strip_front_matter(text.splitlines())
    kind, labels, ids, classes, classdefs, breaks, n_edges = None, {}, set(), {}, set(), [], 0

    def edge_label(lab, no):
        if display_len(lab) > MAX_EDGE_CHARS:
            warns.append(f"line {no}: edge label is long (about {display_len(lab):.0f} Chinese characters wide; keep to {MAX_EDGE_CHARS}): {lab}")

    def flow_node(tok, no):
        m = RE_FLOW_NODE.match(tok.strip())
        if not m:
            errors.append(f"line {no}: cannot read node '{tok.strip()}'")
            return
        ids.add(m.group(1))
        if m.group(2).strip():
            labels[m.group(1)] = re.sub(r'^[\[\(\{>]+|[\]\)\}]+$', "", m.group(2).strip()).strip().strip('"')

    for no, raw in enumerate(lines, 1):
        line = re.sub(r"%%.*$", "", raw).strip()
        if not line:
            continue
        if kind is None:
            if re.match(r"^stateDiagram(-v2)?\b", line):
                kind = "state"; continue
            if re.match(r"^(flowchart|graph)\b", line):
                kind = "flow"; continue
            errors.append(f"line {no}: the first line must be 'stateDiagram-v2' or 'flowchart TB'")
            kind = "state"
        if m := RE_CLASSDEF.match(line):
            classdefs.add(m.group(1)); continue
        if m := RE_CLASS.match(line):
            for nid in (x.strip() for x in m.group(1).split(",")):
                classes[nid] = m.group(2)
                if m.group(2) == "breaks" and nid not in breaks:
                    breaks.append(nid)
            continue
        if SKIP.match(line):
            continue
        if UNSUPPORTED.match(line):
            errors.append(f"line {no}: not supported by the renderer (composite/parallel states, notes, subgraphs): {line}")
            continue
        if kind == "state":
            if m := RE_STATE_EDGE.match(line):
                n_edges += 1
                ids.update(x for x in (m.group(1), m.group(2)) if x != "[*]")
                edge_label((m.group(3) or "").strip(), no)
                continue
            if m := RE_STATE_NODE.match(line):
                labels[m.group(1)] = m.group(2).strip(); ids.add(m.group(1)); continue
            if RE_BARE_ID.match(line):
                ids.add(line); continue
            errors.append(f"line {no}: cannot read: {line}")
        else:
            m = RE_FLOW_EDGE1.match(line) or RE_FLOW_EDGE2.match(line)
            if m:
                n_edges += 1
                flow_node(m.group(1), no); flow_node(m.group(3), no)
                edge_label((m.group(2) or "").strip(), no)
                continue
            flow_node(line, no)

    if kind is None:
        errors.append("the source is empty")
    for nid in sorted(ids - set(labels)):
        warns.append(f"node {nid} has no text (the poster will show '{nid}'); add a line '{nid}: text'")
    for nid, lab in labels.items():
        if display_len(lab) > MAX_NODE_CHARS:
            warns.append(f"node {nid} text is long (about {display_len(lab):.0f} Chinese characters wide; keep to {MAX_NODE_CHARS}): {lab}")
    for nid, cls in classes.items():
        if cls not in PALETTE and cls not in classdefs:
            warns.append(f"node {nid} uses class '{cls}', not one of {', '.join(sorted(PALETTE))}; it gets the default fill")
        if nid not in ids:
            warns.append(f"class line names {nid}, which is not in the chart")
    if len(ids) > MAX_NODES:
        warns.append(f"{len(ids)} nodes; above {MAX_NODES} the layout gets crowded, consider two posters")
    return errors, warns, {"nodes": len(ids), "edges": n_edges, "breaks": breaks, "labels": labels}


def check_poster(poster, folder, stats):
    errors, warns = [], []
    if not isinstance(poster, dict):
        return ["poster.json must be a JSON object"], warns
    if not poster.get("title"):
        errors.append("poster.json needs a 'title'")
    for i, p in enumerate(poster.get("photos") or [], 1):
        f = p.get("file") if isinstance(p, dict) else None
        if not f:
            errors.append(f"photo {i} has no 'file'")
        elif not (folder / f).is_file():
            errors.append(f"photo {i} not found: {folder / f}")
    card = poster.get("card")
    if card:
        n_items, n_breaks = len(card.get("items") or []), len(stats["breaks"])
        if n_items != n_breaks:
            warns.append(f"the card has {n_items} items but {n_breaks} nodes are marked 'breaks'; the numbers will not match")
    return errors, warns


# ---------------------------------------------------------------- building
def photo_data_url(path):
    try:
        from PIL import Image
        im = Image.open(path).convert("RGB")
        im.thumbnail((PHOTO_MAX_PX, PHOTO_MAX_PX), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=85)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except ImportError:
        mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
        return f"data:{mime};base64," + base64.b64encode(Path(path).read_bytes()).decode()


def build_html(mermaid, poster, folder):
    content = {"mermaid": mermaid, "poster": poster,
               "photos": [photo_data_url(folder / p["file"]) for p in poster.get("photos") or []]}
    blob = json.dumps(content, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8")
    for key, val in (("/*__DAGRE__*/", DAGRE.read_text(encoding="utf-8")),
                     ("/*__CONTENT__*/", blob),
                     ("__PAGE_TITLE__", poster.get("title", "flowchart").replace("<", "&lt;"))):
        assert html.count(key) == 1, f"template is missing {key}"
        html = html.replace(key, val)
    return html


def run_chrome(chrome, args):
    r = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--virtual-time-budget=20000", *args], capture_output=True, text=True, timeout=180)
    return r.stdout


def export(chrome, html_path, folder, scale):
    url = html_path.resolve().as_uri() + "#bare"
    dom = run_chrome(chrome, ["--dump-dom", url])
    body = re.search(r"<body([^>]*)>", dom)
    attrs = dict(re.findall(r'data-(\w+)="([^"]*)"', body.group(1))) if body else {}
    if attrs.get("ready") != "1":
        raise RuntimeError("the page did not finish drawing in the browser")
    if attrs.get("error"):
        raise RuntimeError("the page reported: " + attrs["error"])
    w, h = int(float(attrs["w"])), int(float(attrs["h"]))
    m = re.search(r"<svg xmlns=.*?</svg>", dom, re.S)
    if m:
        (folder / "poster.svg").write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + m.group(0), encoding="utf-8")
    png = folder / "poster.png"
    if png.exists():
        png.unlink()
    run_chrome(chrome, [f"--window-size={w},{h}", f"--force-device-scale-factor={scale}", f"--screenshot={png}", url])
    if not png.exists():
        raise RuntimeError("the browser did not write the PNG")
    return w, h


# ---------------------------------------------------------------- pstack statechart
def decode_entities(s):
    s = re.sub(r"ﬂ°°(\d+)¶ß", lambda m: chr(int(m.group(1))), s)   # Mermaid's encoded entities (titles)
    return re.sub(r"#(\d+);", lambda m: chr(int(m.group(1))), s)    # #12289; style entities (labels)


def from_statechart(chart_path):
    """Turn pstack statechart's chart.mmd into renderer input. Returns (flow_text, title, notes)."""
    text = decode_entities(Path(chart_path).read_text(encoding="utf-8"))
    lines = text.splitlines()
    title = ""
    if lines and lines[0].strip() == "---":
        end = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == "---")
        for l in lines[1:end]:
            m = re.match(r'\s*title:\s*"?(.*?)"?\s*$', l)
            if m:
                title = m.group(1)
        lines = lines[end + 1:]
    body, final, order, notes, depth = [], {}, [], [], 0
    for raw in lines:
        line = raw.strip()
        if line.startswith('state "Legend" as legend'):
            depth = 1; continue
        if depth:
            depth += line.count("{") - line.count("}")
            continue
        if re.match(r'^state\s+"', line) or line == "--":
            raise SystemExit("This chart has parallel regions (a statechart view whose state() returns an object). "
                             "The renderer draws flat charts only: make state() return a string and run statechart again.")
        if not line or line.startswith("classDef") or line.startswith("direction") or re.match(r"^class\s+lg\d+\s", line):
            continue
        m = RE_CLASS.match(line)
        if m:
            cls = m.group(2)
            for nid in m.group(1).split(","):
                if nid not in order:
                    order.append(nid)
                if cls in ("breaks", "mayBreak"):
                    if cls == "mayBreak":
                        notes.append(f"{nid} may break a rule (only some model states behind it do); drawn as a problem")
                    final[nid] = "breaks"
                elif cls in ("bugPath", "repeats"):
                    continue
                elif final.get(nid) != "breaks":
                    final[nid] = STATECHART_COLORS.get(cls, cls)
            continue
        if line.startswith("stateDiagram"):
            body.append("stateDiagram-v2"); continue
        body.append("  " + line)
    groups = {}
    for nid in order:
        if nid in final and final[nid] != "breaks":
            groups.setdefault(final[nid], []).append(nid)
    breaks = [nid for nid in order if final.get(nid) == "breaks"]
    tail = [f"  class {','.join(ids)} {cls}" for cls, ids in groups.items()]
    if breaks:
        tail.append(f"  class {','.join(breaks)} breaks")
    head = [f"%% Converted from {Path(chart_path).name} (pstack statechart) by make_poster.py --from-statechart",
            "%% Problem numbers follow the order of the 'breaks' class line."]
    return "\n".join(head + body + tail) + "\n", title, notes


def rule_map(report_path, labels):
    """From statechart's report.md: which chart state ends each broken rule's shortest path."""
    if not report_path.is_file():
        return []
    text = decode_entities(report_path.read_text(encoding="utf-8"))
    out = []
    for sec in re.split(r"^## ", text, flags=re.M)[1:]:
        head, _, rest = sec.partition("\n")
        m = re.match(r"(\S+) breaks", head)
        steps = re.findall(r"^\d+\.\s+(.*)$", rest, flags=re.M)
        if m and steps:
            last = steps[-1].rsplit(": ", 1)[-1].strip()
            nid = next((k for k, v in labels.items() if v == last), None)
            out.append((m.group(1), last, nid))
    return out


# ---------------------------------------------------------------- starters
STARTER = {
    "en": ("""stateDiagram-v2
  s0: Drafting
  s1: In review
  s2: Accepted
  s3: Stuck waiting
  [*] --> s0
  s0 --> s1: you submit
  s1 --> s0: changes requested
  s1 --> s2: approved
  s1 --> s3: nobody responds [after two weeks]
  class s0 blue
  class s1 cream
  class s2 lavender
  class s3 breaks
""", {"kicker": "process · I", "title": "A review", "subtitle": "from draft to accepted",
      "stamp": "rule broken", "card": {"title": "What the check found", "items": ["Nothing happens when nobody responds"]}}),
    "zh": ("""stateDiagram-v2
  s0: 写初稿
  s1: 审阅中
  s2: 通过
  s3: 卡住没人管
  [*] --> s0
  s0 --> s1: 你提交
  s1 --> s0: 要求修改
  s1 --> s2: 同意
  s1 --> s3: 没人回复 [两周后]
  class s0 blue
  class s1 cream
  class s2 lavender
  class s3 breaks
""", {"kicker": "流程 · 一", "title": "一次审阅", "subtitle": "从初稿到通过",
      "stamp": "规则被打破", "card": {"title": "检查发现的问题", "items": ["没人回复时，流程没有下一步"]}}),
}


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Render flow.mmd + poster.json as a paper-style poster")
    ap.add_argument("folder", help="folder with flow.mmd and poster.json")
    ap.add_argument("--check", action="store_true", help="check only, do not draw")
    ap.add_argument("--no-png", action="store_true", help="write poster.html only")
    ap.add_argument("--scale", type=float, default=2, help="PNG scale (default 2)")
    ap.add_argument("--init", action="store_true", help="create a starter flow.mmd and poster.json")
    ap.add_argument("--lang", choices=["en", "zh"], default="en", help="language of the --init starter")
    ap.add_argument("--from-statechart", metavar="CHART_MMD", help="convert pstack statechart's chart.mmd into flow.mmd")
    ap.add_argument("--force", action="store_true", help="let --init / --from-statechart overwrite files")
    a = ap.parse_args()
    folder = Path(a.folder).resolve()
    mmd, pj = folder / "flow.mmd", folder / "poster.json"

    if a.init:
        folder.mkdir(parents=True, exist_ok=True)
        flow, poster = STARTER[a.lang]
        for f, content in ((mmd, flow), (pj, json.dumps(poster, ensure_ascii=False, indent=2) + "\n")):
            if f.exists() and not a.force:
                sys.exit(f"{f} exists; use --force to overwrite")
            f.write_text(content, encoding="utf-8")
        print(f"Wrote {mmd} and {pj}. Edit them, then run: make_poster.py {folder}")
        return

    if a.from_statechart:
        chart = Path(a.from_statechart).resolve()
        if mmd.exists() and not a.force:
            sys.exit(f"{mmd} exists; use --force to overwrite")
        folder.mkdir(parents=True, exist_ok=True)
        flow, title, notes = from_statechart(chart)
        mmd.write_text(flow, encoding="utf-8")
        print(f"Wrote {mmd}" + (f" (statechart title: {title})" if title else ""))
        for n in notes:
            print("  note: " + n)
        _, _, stats = check_mermaid(flow)
        rules = rule_map(chart.parent / "report.md", stats["labels"])
        if stats["breaks"]:
            print("Problem numbers on the poster (write poster.json 'card.items' in this order):")
            for i, nid in enumerate(stats["breaks"], 1):
                broken = [r for r, _, n in rules if n == nid]
                print(f"  {i}. {nid}: {stats['labels'].get(nid, nid)}" + (f"  <- breaks {', '.join(broken)}" if broken else ""))
        if not pj.exists():
            print(f"Now write {pj} (fields: references/poster-json.md) and run: make_poster.py {folder}")
        return

    for f in (mmd, pj):
        if not f.is_file():
            sys.exit(f"missing {f} (make_poster.py {folder} --init creates a starter)")
    mermaid = mmd.read_text(encoding="utf-8")
    try:
        poster = json.loads(pj.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"poster.json is not valid JSON: line {e.lineno} column {e.colno}: {e.msg}")

    errors, warns, stats = check_mermaid(mermaid)
    e2, w2 = check_poster(poster, folder, stats)
    errors += e2
    warns += w2
    print(f"Check: {stats['nodes']} nodes, {stats['edges']} edges, {len(stats['breaks'])} problem nodes")
    for w in warns:
        print("  warning: " + w)
    for e in errors:
        print("  error: " + e)
    if errors:
        sys.exit("Errors found; nothing drawn.")
    if a.check:
        print("Check passed.")
        return

    html_path = folder / "poster.html"
    html_path.write_text(build_html(mermaid, poster, folder), encoding="utf-8")
    print(f"Wrote {html_path}")
    if a.no_png:
        return
    chrome = next((c for c in chrome_candidates() if c and Path(c).exists()), None)
    if not chrome:
        print("No Chrome / Edge / Chromium found; skipped PNG/SVG (set CHROME to the browser binary).")
        return
    try:
        w, h = export(chrome, html_path, folder, a.scale)
    except Exception as e:
        sys.exit(f"Export failed: {e}")
    print(f"Wrote {folder / 'poster.png'} ({int(w * a.scale)}x{int(h * a.scale)}) and {folder / 'poster.svg'}")


if __name__ == "__main__":
    main()
