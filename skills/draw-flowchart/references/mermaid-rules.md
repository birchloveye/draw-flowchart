# Mermaid rules for draw-flowchart

The renderer reads a small part of Mermaid. Write `flow.mmd` like this and it renders the first time. Run `make_poster.py <folder> --check` after writing.

## 1. Which diagram

| Diagram | Use for | First line |
|---|---|---|
| State diagram | something moving between states: a request, a paper, an experiment's progress, a TLC check | `stateDiagram-v2` |
| Flowchart | steps and decisions | `flowchart TB` |

Always drawn top to bottom; a `direction` line is ignored.

## 2. State diagram

```
stateDiagram-v2
  s0: Drafting                    %% give every state an id, then its text
  s1: In review
  [*] --> s0                      %% start
  s0 --> s1: you submit           %% arrow, colon, label
  s1 --> s1: a week passes        %% back to itself: drawn as a small curl on the right
  s1 --> [*]                      %% end (optional)
```

- Ids use letters, digits, `_`, `-`, `.` only.
- Every state needs an `id: text` line, or the poster shows the id.

## 3. Flowchart

```
flowchart TB
  A[Split the data] --> B[Write the evaluation]
  B -->|script ready| C(Run the baseline)       %% |text| is the arrow label
  D -- it installs --> E[Run the new model]      %% this label form works too
```

- **One arrow per line.** `A --> B --> C` is not supported.
- Box shapes are not distinguished; all boxes are rounded rectangles.

## 4. Text

- **Node text up to about 26 Chinese characters wide, edge labels up to about 24** (a Latin letter counts about half). Node text wraps at roughly 12 Chinese characters or 22 Latin letters per line.
- To choose where a line breaks, put a space there: the renderer breaks at spaces when it can.
- **Conditions go in square brackets:** `you submit elsewhere [after months of silence]`. Bracketed text is drawn in dark red.
- Write the reader's words, not variable or function names: "you resubmit", not `ReviseMajor`.
- Write in the user's language. In Chinese, put a space between Chinese and Latin words (`C-RADIOv4 装不上`).

## 5. Colours

Colour nodes with `class <ids> <name>`. Use only these names:

| Name | Colour | Suggested use |
|---|---|---|
| `blue` | pale blue | getting ready, early stages |
| `cream` | cream | in progress, middle stages |
| `lavender` | pale lavender | results, the end |
| `wood` | wooden-sign tan | setbacks, outside events |
| `sage` | pale green | another phase when needed |
| `breaks` | pink + red double ring + number | **problems**: a broken rule, a dead end, a missing branch |

```
  class s0,s1 blue
  class s4,s7 breaks
```

- **`breaks` nodes are numbered in the order they appear on `class` lines** (above: s4 is 1, s7 is 2). The card in `poster.json` must list them in the same order, one line each.
- **Arrows into a `breaks` node are drawn red** automatically ("the step into the problem").
- Use at most four colours besides `breaks`, one per phase.
- `classDef name fill:#rrggbb` defines a custom fill, but prefer the names above so posters look alike.

## 6. Not supported (errors)

- composite states `state X { ... }` and parallel regions `--`
- `note`, `subgraph`, `end`
- `style`, `linkStyle` and `click` lines are skipped (no error, no effect)

## 7. Size

- 15–25 boxes look best; above 30 the check warns. Split bigger processes ("part I", "part II").
- Keep the arrows leaving one box to about five, or they crowd.

## 8. Before rendering

1. Does every state have text?
2. Does every `breaks` node stand for a problem the reader should see, and does the card follow the same order?
3. Can every box be reached from the start?
4. Does `--check` report no errors?
