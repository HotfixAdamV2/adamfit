# st.popover

A button that opens a small floating panel. Anything drawn inside `with st.popover(...):` appears in the panel. Good for short forms and "are you sure?" confirmations that shouldn't take up space on the page.

## Basic example
```python
with st.popover("Delete recipe", icon=":material/delete:"):
    st.write("Remove this recipe?")
    if st.button("Yes, delete it", type="primary"):
        ...
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Text on the button | required |
| `icon` | Emoji or `:material/name:` icon | None |
| `type` | `"primary"`, `"secondary"` or `"tertiary"` | `"secondary"` |
| `help` | Tooltip on the button | None |
| `disabled` | Grey out the button | `False` |

## Used in
- [Nutrition page](../nutrition_page.md): the New recipe form and the delete confirmation
