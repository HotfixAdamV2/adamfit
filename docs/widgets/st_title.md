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
| `text_alignment` | `"left"`, `"center"`, `"right"` or `"justify"`. Also works on `st.caption` | `"left"` |

## Related: st.subheader and st.caption
- `st.subheader("Log weight")`: a smaller section heading. Same parameters as `st.title`, plus `divider` to draw a line under it.
- `st.caption("...")`: small grey text for hints and notes. Inside a horizontal row, `width="content"` keeps it only as wide as its text (default `"stretch"`).

## Used in
- [Home page](../home_page.md) (centred title and caption, using `text_alignment="center"`, and a subheader above each chart)
- [Charts over time](../charts.md) (a subheader at the top of each chart card, and a caption while a custom range is half picked)
- [Exercises page](../exercises_page.md)
- [Login page](../login_page.md) (also subheader and caption)
- [My Profile page](../profile_page.md) (also subheader and caption)
- [Nutrition page](../nutrition_page.md) (also subheader and caption, including `width="content"` captions in the add row and for the "3 unsaved changes" note)
