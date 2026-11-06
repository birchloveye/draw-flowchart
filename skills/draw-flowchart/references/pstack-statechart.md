# Using pstack's /statechart for the first half

pstack (https://github.com/cursor/plugins/tree/main/pstack) has a `statechart` skill: you write the process as a TLA+ spec with the user's rules as INVARIANTs, TLC checks every reachable state, and it writes `chart.mmd` (a Mermaid state diagram) and `report.md` (the shortest path to each broken rule). draw-flowchart turns that `chart.mmd` into a poster. Follow pstack's own SKILL.md for the spec; this page covers only what makes the hand-off clean.

## Write the view so it converts

| Do | Why |
|---|---|
| `state()` returns a **string** | parallel regions (an object) and parent states (an array) cannot be drawn yet; the converter stops with an error |
| keep labels short, in the reader's words, conditions in `[brackets]` | same text rules as [mermaid-rules.md](mermaid-rules.md) |
| `colors` uses statechart's names `blue`, `teal`, `yellow`, `purple`, `pink`, `tan`, `orange` | they map to this skill's palette (table below) |
| add `CONSTRAINT Explore` where `Explore` is the conjunction of the rules that can break | each problem becomes the end of its path, so the poster shows one red box per problem instead of everything after it |
| return the same label for a whole family of model states | keep the chart near 20 arrows; statechart draws nothing above 500 states |
| when several actions share one TLA+ helper (TLC names them all after the helper), name steps by `from` and `to` in `step()` | see `examples/paper-submission/statechart/view-en.mjs` |

Colour mapping used by `--from-statechart`:

| statechart | poster |
|---|---|
| blue | blue |
| teal, yellow | cream |
| purple, pink | lavender |
| tan, orange | wood |
| `breaks`, `mayBreak` | breaks (red ring and number) |
| `bugPath`, `repeats` | dropped |

## Convert and render

```bash
python3 <skill>/scripts/make_poster.py <folder> --from-statechart <statechart-out>/chart.mmd
# prints, for example:
#   1. s8: Lost in the system  <- breaks NoDeadlock
#   2. s9: Under review at two journals  <- breaks NoDualSubmission
# write poster.json "card.items" in that order, then:
python3 <skill>/scripts/make_poster.py <folder>
```

The rule names come from `report.md` next to `chart.mmd`. Turn each into a sentence for the card: what goes wrong and what the plan is missing.

## Running TLC without mise

statechart installs Java and TLC with `mise` on first run. Without mise, point it at a TLA+ jar and an existing Java 11+:

```bash
curl -L -o tla2tools.jar https://github.com/tlaplus/tlaplus/releases/download/v1.7.4/tla2tools.jar
# sha256 936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88
TLA2TOOLS=$PWD/tla2tools.jar JAVA=$(command -v java) <pstack>/skills/statechart/scripts/statechart Spec.tla --config Spec.cfg --view view.mjs --out out
```

## Example

`examples/paper-submission/statechart/`: `Submission.tla`, `Submission.cfg`, `view-en.mjs`, `view-zh.mjs`, and statechart's output in `out-en/` and `out-zh/`.
