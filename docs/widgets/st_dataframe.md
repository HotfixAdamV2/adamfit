# st.dataframe

Displays tabular data as an interactive table. Users can sort columns, resize them and search. It accepts a pandas DataFrame, or simpler data such as a list of dictionaries.

## Basic example
```python
rows = [{"exercise_name": "Deadlift", "muscle_group": "Back"}]
st.dataframe(rows, hide_index=True)
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `data` | The table contents (list of dicts, DataFrame, ...) | required |
| `hide_index` | Hides the row-number column when `True` | Automatic |
| `width` | Table width: `"stretch"`, `"content"` or pixels | `"stretch"` |
| `height` | Table height in pixels, or `"auto"` | `"auto"` |
| `column_config` | Customises individual columns (labels, formats) | None |
| `column_order` | Which columns to show, and in what order | All columns |
| `alt` | Name read out by screen readers | None |

## Customising columns with `column_config`
```python
st.dataframe(
    view[["weigh_date", "weight"]],
    hide_index=True,
    column_config={
        "weigh_date": st.column_config.DateColumn("Date", format="MMM D, YYYY"),
        "weight": st.column_config.NumberColumn("Weight (lb)", format="%.1f"),
    },
)
```
Each entry renames a column and controls how its values are displayed.

## A button on every row (`ButtonColumn`)
`st.column_config.ButtonColumn` turns a column into buttons. Each cell's text is that row's button label, and `:material/name:` icons work. When a button is pressed, `on_click` runs before the next run. During that run, `st.session_state[key]` holds the click: `row` is the row's **position** (0, 1, 2...) in the table you passed in, not its index value, and `label` is the button text. The click then resets to `None` by itself, so nothing needs clearing afterwards. `key` is required, or the buttons do nothing.
```python
view = view.assign(unit_label=view["serving_unit"].map(unit_label), edit=":material/edit: Edit")


def open_clicked_food() -> None:
    click = st.session_state["food_edit_click"]
    open_food_dialog(int(view.index[click.row]))


st.dataframe(
    view,
    column_order=["edit", "food_name", ...],
    column_config={
        "edit": st.column_config.ButtonColumn(
            "Edit", type="tertiary", on_click=open_clicked_food, key="food_edit_click"
        ),
        ...
    },
)
```
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Column header | The column name |
| `type` | `"primary"`, `"secondary"` or `"tertiary"` (plain text, no border) | `"secondary"` |
| `on_click` | Function to call before the rerun when a button is pressed | None |
| `args` / `kwargs` | Extra values passed to `on_click` | None |
| `key` | Where the click (`row`, `label`) is stored. Required for clicks to work | None |
| `width` | `"small"`, `"medium"`, `"large"` or pixels | Fits the contents |
| `pinned` | Keep the column visible when scrolling sideways | Automatic |

`st.dataframe` can also let users select rows (`on_select`, `selection_mode`). A selection stays selected across reruns until the user changes it, so it suits "remember which rows are picked". For a one-off action like opening a pop-up, a button column is simpler.

## Used in
- [Exercises page](../exercises_page.md)
- [My Profile page](../profile_page.md)
- [Nutrition page](../nutrition_page.md): the Total row under a recipe's ingredients table, and the Foods tab's food list, where each row's Edit button (a `ButtonColumn`) opens the Edit food pop-up
