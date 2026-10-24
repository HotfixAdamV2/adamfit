# st.segmented_control

A row of buttons where one (or several) can be selected, like a toggle with more than two choices. Returns the selected option.

## Basic example
```python
period = st.segmented_control("Time period", ["1M", "3M", "6M", "1Y", "All"], default="3M", required=True)
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Text shown above the buttons | required |
| `options` | The choices | required |
| `default` | Option selected at first | None |
| `required` | When `True`, clicking the selected option cannot unselect it, so there is always a value | `False` |
| `selection_mode` | `"single"` or `"multi"` | `"single"` |
| `format_func` | Turns each option into the text shown | `str` |
| `key` | Name under which the value is kept in `st.session_state` | None |
| `on_change` | Function called when the selection changes, before the rerun | None |
| `persist_state` | `"session"` keeps the value for the whole session, even when the widget isn't drawn (e.g. its chart card is hidden) or you visit another page. Needs `key` | None |

## Used in
- [My Profile page](../profile_page.md): the units toggle and the chart time period
- [Charts over time](../charts.md): the time period (1M to All, or Custom), which macro to show, Daily / Weekly / Monthly and Bars / Lines for the weight change, on the [Home page](../home_page.md) and [Nutrition page](../nutrition_page.md)
