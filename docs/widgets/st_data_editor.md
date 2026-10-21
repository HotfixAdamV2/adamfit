# st.data_editor

An editable table, like a small spreadsheet. It returns the edited data, and also keeps a record of what changed in `st.session_state[key]`:

```python
{
    "edited_rows": {0: {"servings": 2.0}}, # row position -> changed columns
    "added_rows": [{"food_name": "My shake", ...}],
    "deleted_rows": [2],                     # row positions
}
```

Row numbers are **positions** in the table you passed in (0, 1, 2...), not database ids. Keep a list of ids in the same order to look them up.

## Basic example
```python
st.data_editor(
    scaled,
    hide_index=True,
    num_rows="delete",
    column_config={"item_name": st.column_config.TextColumn("Item", disabled=True)},
    key=editor_key,
    on_change=_save,
    alt="Food log",
)
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `data` | The table to edit (usually a DataFrame) | required |
| `num_rows` | `"fixed"`, `"dynamic"` (add and delete), `"add"` or `"delete"` | `"fixed"` |
| `disabled` | `True` for read-only, or a list of read-only column names | `False` |
| `column_config` | Labels, formats, limits and editor types per column (see below) | None |
| `hide_index` | Hide the index column. With `num_rows="dynamic"` this only works if the index is a plain 0, 1, 2... | Automatic |
| `key` | Unique name, also where the change record is stored | None |
| `on_change` | Function to call (before the rerun) when anything is edited | None |
| `alt` | Name read out by screen readers | None |

## Column types used
| Column config | What it does |
|---------------|--------------|
| `st.column_config.TextColumn(label, max_chars=, required=, disabled=)` | Text cells |
| `st.column_config.NumberColumn(label, min_value=, step=, format=, default=, disabled=)` | Number cells. `format="%.2f"` shows two decimals, `step=0.25` sets the +/- step |
| `st.column_config.SelectboxColumn(label, options=, format_func=, default=)` | A dropdown in each cell. `format_func` turns stored values (e.g. ids) into labels |

`st.column_config.ButtonColumn` (a button on every row) also works in `st.data_editor`. See [st.dataframe](st_dataframe.md#a-button-on-every-row-buttoncolumn).

All of them accept `width` (`"small"`, `"medium"`, `"large"` or pixels) and `required` (a new row must fill it in).

## Batching changes
- **Stage, then save on a button**: pass `on_change`. The callback reads the change record and copies it into our own "changes" dictionary in `st.session_state`, without touching the database. Then the editor gets a new `key` (we add a version number) so it starts fresh, and the page redraws it from the database rows with the staged changes applied. **Save changes** writes them all in one transaction, **Revert changes** throws them away. Used for the daily log and recipe ingredients, because adding a row happens outside the editor (in the add row above it) and has to be staged in the same place.
- **In a form** (not used at the moment): put the editor in a [form](st_form.md). Edits are only sent when the form's submit button is pressed.

## Used in
- [Nutrition page](../nutrition_page.md): the Daily log and recipe ingredient tables (inside `ui.entries_editor`). The Foods tab uses a read-only [st.dataframe](st_dataframe.md) with an Edit button per row, and a pop-up, instead.
