# st.pills

A row of small rounded buttons ("pills"). With `selection_mode="multi"` you can turn several on at once, like a set of switches, so it suits a few options that all fit on one line. Returns the selected options as a list (or a single option in `"single"` mode).

## Basic example
```python
lines = {"raw": "Weigh-ins", "avg": "Rolling average"}
shown = st.pills(
    "Lines",
    list(lines),
    selection_mode="multi",
    default=list(lines),
    format_func=lines.get,
    key="home_weight_lines",
)
# shown is e.g. ["raw", "avg"], ["avg"] or [] when both are turned off
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Text shown above the pills | required |
| `options` | The choices | required |
| `selection_mode` | `"single"` (pick one) or `"multi"` (pick any number, including none) | `"single"` |
| `default` | Option(s) selected at first. A list in `"multi"` mode | None |
| `format_func` | Turns each option into the text shown. The return value is still the raw option | `str` |
| `key` | Name under which the value is kept in `st.session_state` | None |
| `required` | In `"single"` mode, stops the user unselecting the chosen option. Not allowed with `"multi"` | `False` |
| `width` | `"content"`, `"stretch"` or pixels | `"content"` |
| `persist_state` | `"session"` keeps the value for the whole session, even when the widget isn't drawn (e.g. its chart card is hidden) or you visit another page. Needs `key` | None |

Keep the options themselves fixed (e.g. `"raw"`, `"avg"`) and change only the text through `format_func`. Changing the options list can reset the widget.

## Used in
- [Charts over time](../charts.md): turning each chart line on or off, and choosing what the weight change is based on ("Based on", defaulting to the rolling average only), on the [Home page](../home_page.md), [My Profile page](../profile_page.md) and [Nutrition page](../nutrition_page.md)
