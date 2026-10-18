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

## Used in
- [Exercises page](../exercises_page.md)
