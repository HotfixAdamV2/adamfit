# st.date_input

A calendar picker. Returns a Python `datetime.date`, or `None` if `value=None` and nothing is picked.

## Basic example
```python
weigh_date = st.date_input("Date", value=date.today(), max_value=date.today())
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Text shown above the picker | required |
| `value` | Starting date. `None` starts empty | Today |
| `min_value` / `max_value` | Earliest and latest selectable dates | 10 years either side of `value` |
| `format` | How the date is displayed (`"YYYY/MM/DD"`, `"MM/DD/YYYY"`...) | `"YYYY/MM/DD"` |
| `key` | Unique name. Callbacks can change the date via `st.session_state[key]` | None |
| `width` | `"stretch"` or a width in pixels | `"stretch"` |

## Used in
- [My Profile page](../profile_page.md)
- [Nutrition page](../nutrition_page.md): the day being logged (the ‹ › buttons change it through its key)
