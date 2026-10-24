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
| `persist_state` | `"session"` keeps the value for the whole session, even when the widget isn't drawn (e.g. its chart card is hidden) or you visit another page. Needs `key` | None |

**Picking a range.** Pass a pair, e.g. `value=(start, end)`, and the picker selects a range and returns a tuple. While the user is halfway through (only the start clicked), it returns a tuple with just one date, so check `len(picked)` before using both ends:
```python
picked = st.date_input("Date range", value=(today - timedelta(days=91), today), max_value=today, format="YYYY-MM-DD", key=f"{key}_range")
if len(picked) == 2:
    start, end = picked
```

## Used in
- [My Profile page](../profile_page.md): birth date, weigh-in date, and the start and end dates of a Google Health sync (`min_value` / `max_value` limit the range)
- [Nutrition page](../nutrition_page.md): the day being logged (the ‹ › buttons change it through its key)
- [Charts over time](../charts.md): the custom date range of the weight and macros charts (a `(start, end)` pair)
