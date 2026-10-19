# st.title

Shows the largest heading on the page.

## Basic example
```python
st.title("Exercises")
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `body` | The heading text (supports basic markdown) | required |
| `anchor` | Custom id so you can link to this heading | Generated from text |
| `help` | Tooltip shown next to the heading | None |

## Related: st.subheader and st.caption
- `st.subheader("Log weight")`: a smaller section heading. Same parameters as `st.title`, plus `divider` to draw a line under it.
- `st.caption("...")`: small grey text for hints and notes.

## Used in
- [Home page](../home_page.md)
- [Exercises page](../exercises_page.md)
- [Login page](../login_page.md) (also subheader and caption)
- [My Profile page](../profile_page.md) (also subheader and caption)
- [Nutrition page](../nutrition_page.md) (also subheader and caption)
