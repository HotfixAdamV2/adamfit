# Layout: st.columns, st.container, st.expander, st.divider and st.sidebar

These don't collect input. They control **where** other elements appear.

## st.columns
Splits the space into side-by-side columns. Call widgets on a column to place them in it.
```python
col_date, col_weight = st.columns(2)          # two equal columns
col_period, col_window = st.columns([3, 2])   # 60% / 40%
col_date.date_input("Date")
```
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `spec` | Number of equal columns, or a list of relative widths | required |
| `gap` | Space between columns: `"small"`, `"medium"`, `"large"` | `"small"` |
| `vertical_alignment` | `"top"`, `"center"` or `"bottom"` | `"top"` |

## st.container
A box that holds other elements. With `horizontal=True` its contents sit side by side in a row, and wrap onto the next line on narrow screens. That makes it a simpler choice than columns for a row of controls.
```python
with st.container(horizontal=True, vertical_alignment="bottom"):
    st.selectbox("Food or recipe", ...)
    st.number_input("Servings", ..., width=150)
    st.button("Add")
```
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `horizontal` | Place contents in a row instead of a column | `False` |
| `vertical_alignment` | In a row: `"top"`, `"center"` or `"bottom"` | `"top"` |
| `border` | Draw a box around it | `False` |
| `gap` | Space between items | `"small"` |

## st.expander
A collapsible section. Good for things that are useful but not always needed.
```python
with st.expander("Delete an entry"):
    ...
```
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Text on the header | required |
| `expanded` | Start open | `False` |
| `icon` | Icon on the header | None |

## st.divider
A thin horizontal line between two sections.
```python
st.divider()
```

## st.sidebar
The panel on the left. Anything drawn inside `with st.sidebar:` goes there instead of the main page.
```python
with st.sidebar:
    st.caption("Logged in as adam")
```

## Used in
- [App router (`app.py`)](../streamlit_basics.md#multipage-apps-and-the-router): sidebar
- [Home page](../home_page.md): a horizontal container for the macro tiles (inside `ui.macro_tiles`)
- [My Profile page](../profile_page.md): columns, expanders (including the Google Health sync expander with a sync `icon`), and a horizontal container for the Connect / Refresh status buttons
- [Nutrition page](../nutrition_page.md): horizontal containers (the filter row, the add row and the Save / Revert row), columns, the Edit recipe details expander, a divider above Delete food in the food pop-up, a bordered container around the new-category boxes, and in the Manage categories pop-up a closed "Built-in categories" expander (with a lock `icon`) and dividers between its sections
