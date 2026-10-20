# st.form and st.form_submit_button

Groups several inputs so that changing them does **not** rerun the script. Nothing happens until the submit button is pressed, and then the script reruns once with all the values. Use it whenever the user fills in several fields and then clicks "Save".

## Basic example
```python
with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Log in")

if submitted:
    ...  # use username and password
```

`st.form_submit_button` returns `True` only on the run right after it was clicked.

## Parameters
**st.form**
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `key` | Unique name for the form | required |
| `clear_on_submit` | Reset all inputs after submitting | `False` |
| `enter_to_submit` | Pressing Enter in a field submits the form | `True` |
| `border` | Draw a box around the form | `True` |

**st.form_submit_button**
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Button text | `"Submit"` |
| `type` | `"primary"` (highlighted), `"secondary"` or `"tertiary"` | `"secondary"` |
| `on_click` | Function to call before the rerun | None |

## Used in
- [Login page](../login_page.md)
- [My Profile page](../profile_page.md)
- [Nutrition page](../nutrition_page.md): the New recipe and recipe details forms. The food pop-up is *not* a form, so that choosing "+ New category" can show extra boxes straight away (see [st.dialog](st_dialog.md))
