# st.dataframe

Displays tabular data as an interactive table. Users can sort columns, resize them and search. It accepts a pandas DataFrame, or simpler data such as a list of dictionaries.

## Basic example
```python
rows = [{"exercise_name": "Deadlift", "equipment": "Barbell"}]
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

## Selecting rows (`on_select`)
With `on_select` set, clicking a row selects it and reruns the app. `selection_mode="single-row"` allows one row at a time. Give the table a `key`: the selection is then kept in `st.session_state[key]` across reruns, as `{"selection": {"rows": [...], ...}}`. `rows` holds row **positions** (0, 1, 2...) in the table you passed in, not index values, and they stay the same if the user sorts in the browser.

A position points at a different row once the filters or the data change. So the Exercises page passes a callback as `on_select`, which turns the position into an exercise id straight away, and it re-points the selection at that id's new row before drawing the table. A selection can be set this way, before the table is drawn:
```python
st.session_state[TABLE_KEY] = {"selection": {"rows": selected_rows}}
st.dataframe(
    table,
    hide_index=True,
    alt="Your exercises",
    key=TABLE_KEY,
    on_select=remember_selection,
    selection_mode="single-row",
    ...
)
```
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `on_select` | `"ignore"` (no selection), `"rerun"`, or a function to call before the rerun | `"ignore"` |
| `selection_mode` | `"single-row"`, `"multi-row"`, `"single-row-required"`, or column / cell modes | `"multi-row"` |
| `selection_default` | The selection on first draw, e.g. `{"selection": {"rows": [0]}}` | None |
| `key` | Where the selection is kept. Needed to keep or set it | None |

A selection stays selected across reruns until the user changes it, so it suits "remember which row is picked". For a one-off action like opening a pop-up, a button column is simpler. Mixing the two in one table is awkward, because clicking a button cell may also select the row.

## Used in
- [Exercises page](../exercises_page.md): the exercise table, with single-row selection (the selected exercise is shown in a panel below) and a `CheckboxColumn` showing which exercises have a picture
- [My Profile page](../profile_page.md)
- [Nutrition page](../nutrition_page.md): the Total row under a recipe's ingredients table, and the Foods tab's food list, where each row's Edit button (a `ButtonColumn`) opens the Edit food pop-up
