# st.toggle

An on/off switch. Returns `True` when it is on. Use it for settings that change the page straight away (like showing or hiding a chart). Inside forms, `st.checkbox` is the usual choice.

## Basic example
```python
shown = st.toggle("Show", value=True, key="home_weight_shown", persist_state="session")
if shown:
    draw_chart()
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Text next to the switch | required |
| `value` | Whether it starts on | `False` |
| `key` | Name under which the value is kept in `st.session_state` | None |
| `persist_state` | `"session"` keeps the value when the switch isn't drawn or you visit another page (needs `key`). `"page"` keeps it only while you stay on the page. `None` forgets it | None |
| `on_change` | `"rerun"` (rerun the page when flipped) or a callback function | `"rerun"` |
| `help` | Tooltip next to the label | None |
| `width` | `"content"`, `"stretch"` or pixels | `"content"` |

## Used in
- [Charts over time](../charts.md): the **Show** switch on every chart card, and the weight change chart's **% change** switch, on the [Home page](../home_page.md), [My Profile page](../profile_page.md) and [Nutrition page](../nutrition_page.md)
