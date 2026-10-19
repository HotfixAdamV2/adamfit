# st.tabs

Splits content into tabs, with a row of tab labels at the top. Returns one container per tab. Anything drawn inside `with tab:` appears in that tab.

## Basic example
```python
log_tab, recipe_tab = st.tabs(["Daily log", "Recipes"], key="nutrition_tab", on_change="rerun")

if log_tab.open:
    with log_tab:
        st.write("Only runs when this tab is selected")
```

By default every tab's code runs on every rerun, even the hidden ones. With `on_change="rerun"`, the tabs remember which one is selected (so it stays open after `st.rerun()`), and each tab's `.open` is `True` or `False` so you can skip hidden tabs.

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `tabs` | List of tab labels | required |
| `default` | Label of the tab selected at first | First tab |
| `key` | Unique name. With state tracking on, `st.session_state[key]` holds the selected label | None |
| `on_change` | `"ignore"` (no state tracking), `"rerun"`, or a callback function | `"ignore"` |

## Used in
- [Nutrition page](../nutrition_page.md)
