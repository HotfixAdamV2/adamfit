# st.data_editor

An editable table, like a small spreadsheet. It returns the edited data, and also keeps a record of what changed in `st.session_state[key]`:

```python
{
    "edited_rows": {0: {"amount": 8.0}},   # row position -> changed columns
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
| `st.column_config.NumberColumn(label, min_value=, step=, format=, default=, disabled=)` | Number cells. `format="%.1f"` shows one decimal |
| `st.column_config.SelectboxColumn(label, options=, format_func=, default=)` | A dropdown in each cell. `format_func` turns stored values (e.g. ids) into labels |

All of them accept `width` (`"small"`, `"medium"`, `"large"` or pixels) and `required` (a new row must fill it in).

## Two ways to save
- **Straight away**: pass `on_change`. The callback reads the change record and saves it. Then give the editor a new `key` (we add a version number) so it starts fresh with the saved data. Used for the log and recipe ingredients.
- **On a button**: put the editor in a [form](st_form.md). Edits are only sent when the form's submit button is pressed. Used for the food list.

## Used in
- [Nutrition page](../nutrition_page.md)
