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

## Used in
- [My Profile page](../profile_page.md): the units toggle and the chart time period
