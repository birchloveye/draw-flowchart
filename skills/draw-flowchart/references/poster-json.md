# poster.json

Everything on the poster that is not the chart. Only `title` is required.

```json
{
  "lang": "en",
  "kicker": "the life of a paper · I",
  "title": "A submission",
  "subtitle": "TLC finds two ways it goes wrong",
  "legend": { "title": "How to read", "broken": "Breaks a rule or gets stuck", "redLine": "The step into the problem" },
  "stamp": "rule broken",
  "photos": [
    { "file": "photos/site.jpg", "rotate": -2, "caption": ["First caption line", "second line"] }
  ],
  "card": {
    "title": "What TLC found",
    "items": ["One line for problem 1", "One line for problem 2"]
  },
  "style": { "nodeFont": 20, "ranksep": 60, "fills": { "blue": "#d8e4f0" } }
}
```

| Field | Meaning | If missing |
|---|---|---|
| `lang` | `"en"` or `"zh"`: language of the page buttons and the default legend | Chinese if the title contains Chinese, else English |
| `kicker` | small line above the title, like a series name | not drawn |
| `title` | the big title (top left) | **required** |
| `subtitle` | one line under the title, set in italics | not drawn |
| `legend` | box at top right explaining the red marks; `null` hides it | default text in `lang` |
| `stamp` | red rubber stamp next to the legend, e.g. "rule broken" | not drawn |
| `photos` | pictures pinned in empty space with tape; `file` is relative to the folder; `rotate` in degrees (keep within ±3); `caption` is a list of lines | none |
| `card` | the problem card; `items` must match the `breaks` nodes in number and order | not drawn |
| `style` | overrides any setting in `CONFIG` at the top of `assets/template.html` (colours, fonts, sizes, spacing); `fills` is merged by colour name | defaults |

Photos and the card find the highest free spot on the poster by themselves; there are no coordinates to set. Photos are shrunk to 480 px and embedded, so `poster.html` works when copied elsewhere.

Useful `style` keys: `nodeFont`, `labelFont` (text sizes), `nodeMaxWidth`, `labelMaxWidth` (wrap widths), `nodesep`, `ranksep` (spacing), `inkWobble` (0 for perfectly smooth lines), `grain` (paper texture on/off), `paper`, `ink`, `red`.
