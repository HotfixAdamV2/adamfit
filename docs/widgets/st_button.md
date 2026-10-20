# st.button

A clickable button. It returns `True` only on the run right after it was clicked, and `False` on every other run.

## Basic example
```python
if st.button("Log out", icon=":material/logout:"):
    auth.log_out()
    st.rerun()
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Button text | required |
| `type` | `"primary"`, `"secondary"` or `"tertiary"` | `"secondary"` |
| `icon` | Emoji or `:material/name:` icon | None |
| `on_click` | Function to call before the rerun | None |
| `disabled` | Grey out the button | `False` |
| `args` | Values passed to the `on_click` function | None |
| `help` | Tooltip shown on hover | None |
| `key` | Unique name. Needed when two buttons would otherwise look the same to Streamlit (same label on one page) | None |

Inside a form, use [st.form_submit_button](st_form.md) instead.

## Used in
- [App router (`app.py`)](../streamlit_basics.md#multipage-apps-and-the-router): the Log out button
- [My Profile page](../profile_page.md): deleting an entry
- [Nutrition page](../nutrition_page.md): Add, previous/next day, Save changes and Revert changes (both `disabled` when nothing is unsaved), confirming a recipe delete, Add food (opens the pop-up through `on_click` and `args`), Save and Cancel in the food pop-up, Delete food (`disabled` until the confirm box is ticked), Manage categories (secondary, opens its pop-up through `on_click`), and Add category, Rename, Remove category (`disabled` until ticked; `on_click` with `args`) and Done in that pop-up
