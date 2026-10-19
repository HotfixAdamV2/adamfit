# st.metric

Shows one number in large text with a label, and optionally a small "delta" underneath showing how much it changed.

## Basic example
```python
st.metric("Current weight", "198.4 lb", delta="+0.6 lb", delta_color="off")
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Text above the number | required |
| `value` | The number (or text) to show | required |
| `delta` | Change to show underneath. Starts with `-` for down | None |
| `delta_color` | `"normal"` (up green, down red), `"inverse"` (up red), or `"off"` (grey) | `"normal"` |
| `help` | Tooltip next to the label | None |
| `border` | Draw a box around the metric | `False` |

We use `delta_color="off"` for weight because whether going up is "good" depends on your goal.

## Used in
- [Home page](../home_page.md): today's macro totals (with `border=True`), in the order fat, carbs, protein, fiber, calories
- [My Profile page](../profile_page.md)
- [Nutrition page](../nutrition_page.md): the Daily log's totals and a recipe's macros per serving (with `border=True`)
