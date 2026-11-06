---
name: draw-flowchart
description: Draws flowcharts and state diagrams as paper-style posters (cream paper, typewriter type, hatched shadows, right-angle connectors, problems ringed in red) and exports HTML, PNG and SVG. Use when the user asks for a flowchart, process or workflow diagram, state diagram, pipeline or experiment-plan figure, or wants Mermaid turned into a polished image. The agent writes the Mermaid, preferably modelled and checked with pstack's /statechart, plus a small poster.json; a bundled script renders it the same way every time.
---

# Draw a flowchart poster

The work has two halves:

1. **You turn the process into Mermaid.** This is the part that needs judgment: what the states are, which branches are missing, where the process can get stuck or break a rule.
2. **`scripts/make_poster.py` renders it.** No model is involved, so the same input always gives the same poster.

`<skill>` below is the folder that holds this file.

## Workflow

1. **Understand the process.** Restate the user's goal in one sentence. List ambiguities, missing branches ("what happens when this step fails?") and risky steps. Ask the user only about forks you cannot settle yourself.

2. **Model it.** Make a folder for the chart (one folder per poster).
   - **With pstack (preferred).** If pstack's `statechart` skill is available (Claude Code: `/pstack:statechart`; Cursor: `/statechart`; or its `SKILL.md` on disk), use it: write a TLA+ spec with the user's rules as INVARIANTs, run it, read `report.md`. Write the view module as described in [references/pstack-statechart.md](references/pstack-statechart.md) so the chart converts cleanly. Then convert:
     ```bash
     python3 <skill>/scripts/make_poster.py <folder> --from-statechart <statechart-out>/chart.mmd
     ```
     It writes `<folder>/flow.mmd` and prints the problem numbers in order, with the rule each one breaks.
     If the user has asked to keep pstack switched off, do not turn it on; use the next path and say so.
   - **Without pstack.** Write `<folder>/flow.mmd` by hand following [references/mermaid-rules.md](references/mermaid-rules.md). Mark each problem you found (a broken rule, a dead end, a missing branch) with the `breaks` class.
   - `make_poster.py <folder> --init [--lang zh]` writes a starter `flow.mmd` and `poster.json` to edit.

3. **Write `<folder>/poster.json`** ([references/poster-json.md](references/poster-json.md)): title, subtitle, legend in the user's language, and a card with one line per `breaks` node, in the same order as the numbers.

4. **Render.**
   ```bash
   python3 <skill>/scripts/make_poster.py <folder>
   ```
   It checks first and draws nothing while there are errors. Fix every error; read every warning. Output: `poster.html` (self-contained, works offline), `poster.png` (2x) and `poster.svg`.

5. **Look at `poster.png`.** If you cannot view images, or to save cost, hand this to a cheaper model or subagent. Check:
   - every red-ringed node has a card line, and the numbers match;
   - no line runs through text or looks attached to the wrong box;
   - labels are in the user's language and short enough to read;
   - nothing important is cramped. Fixes: shorten labels, put a space where a line should break, split a big chart into two posters, or override spacing in `poster.json` `style`. Then render again.

6. **Report** to the user: the PNG path first, then one line per problem (the rule, and how the process reaches it), then what the model leaves out. Mention that `poster.html` has Export PNG/SVG buttons.

## Requirements

- Python 3.8+ (standard library; Pillow is used to shrink photos if installed).
- Chrome, Edge or Chromium for PNG/SVG export. If none is found, `poster.html` is still written; set `CHROME` to the browser binary to enable export.
- Optional: pstack (https://github.com/cursor/plugins/tree/main/pstack) for the TLA+ check, which needs Java 11+ and the TLA+ tools (see references/pstack-statechart.md).
- Fonts are system fonts (macOS: American Typewriter, Baskerville, Songti, Kaiti; Windows and Linux fall back to Courier New / Georgia / SimSun / Noto Serif CJK). On Linux install a CJK font such as Noto Serif CJK for Chinese.

## Limits

- Top-to-bottom layout only.
- No composite states, parallel regions, notes or subgraphs. For statechart output, use a flat view (`state()` returns a string).
- Best at 15–25 boxes; above 30 the check warns. Split larger processes into several posters.
- Automatic layout occasionally runs a line close to an unrelated box. That is why step 5 exists.

## Example

`examples/paper-submission/` in the repository: a TLA+ model of a journal submission (`statechart/`), the converted `flow.mmd`, `poster.json` and the rendered poster. `examples/paper-submission-zh/` is the same model with a Chinese view.
