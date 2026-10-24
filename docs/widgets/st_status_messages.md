# st.success, st.error and st.info

Coloured message boxes. `st.success` is green and is for things that worked. `st.error` is red and is for failures. `st.info` is blue and is for neutral notes (like "no data yet"). `st.warning` (yellow) works the same way.

## Basic example
```python
st.success("Connected to the database.")
st.error(f"Could not connect to the database: {exc}")
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `body` | The message text (supports markdown) | required |
| `icon` | Emoji or icon shown at the left of the box | A default icon |

## Used in
- [Home page](../home_page.md): the "nothing logged today" note, and an `st.warning` (with a Material icon) when today's weight is missing
- [Charts over time](../charts.md): notes when there is no data to chart, or no line is chosen
- [Login page](../login_page.md): wrong password and database errors, and the result of connecting Google Health (success or error, shown with `flash`)
- [My Profile page](../profile_page.md): save and sync confirmations, Google Health errors, and empty-chart notes
- [Nutrition page](../nutrition_page.md): empty days and recipes, validation errors (including the database's "still has active foods" message when a category can't be removed), save confirmations, and an `st.warning` when other days still have unsaved changes
