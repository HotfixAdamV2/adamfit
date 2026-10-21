# st.checkbox

A tick box. It returns `True` when ticked and `False` otherwise. Ticking or unticking it reruns the script, so other widgets can react straight away, for example to enable a button.

## Basic example
```python
confirm = st.checkbox("Yes, remove this food", key="food_confirm_delete")
if st.button("Delete food", icon=":material/delete:", disabled=not confirm, key="food_delete"):
    ...
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Text next to the box | required |
| `value` | Start ticked | `False` |
| `key` | Unique name, also where the value is stored in `st.session_state` | None |
| `help` | Tooltip shown on hover | None |
| `on_change` | Function to call before the rerun when it is ticked or unticked | Rerun only |
| `disabled` | Grey out the box | `False` |

## Used in
- [Nutrition page](../nutrition_page.md): confirming a food delete in the Edit food pop-up, and confirming a category removal in the Manage categories pop-up (one key per category, so a tick doesn't carry over)
