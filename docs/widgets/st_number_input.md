# st.number_input

A box for entering a number, with + and - buttons. Returns an `int` or `float`, or `None` if `value=None` and the box is empty.

All numbers you pass (`value`, `min_value`, `max_value`, `step`) **must be the same type**. Mixing `0` and `0.5` raises an error, so write `0.0`.

## Basic example
```python
weight = st.number_input("Weight (lb)", min_value=0.1, max_value=1500.0, value=180.0, step=0.1, format="%.1f")
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Text shown above the box | required |
| `min_value` / `max_value` | Allowed range | None (no limit) |
| `value` | Starting number. `None` starts empty | `min_value` or 0 |
| `step` | Amount the +/- buttons change it by | 1 or 0.01 |
| `format` | Display format, e.g. `"%.1f"` for one decimal | Automatic |
| `key` | Unique name. A new key gives a fresh box with the new `value` | None |
| `width` | `"stretch"` or a width in pixels | `"stretch"` |
| `disabled` | Grey out the box | `False` |

## Used in
- [My Profile page](../profile_page.md)
- [Nutrition page](../nutrition_page.md): the servings to add, and a recipe's number of servings
