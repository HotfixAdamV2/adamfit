# st.text_input

A single-line text box. Returns whatever the user typed (an empty string if nothing).

## Basic example
```python
password = st.text_input("Password", type="password", autocomplete="current-password")
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Text shown above the box | required |
| `value` | Starting text | `""` |
| `type` | `"default"`, or `"password"` to hide what is typed | `"default"` |
| `autocomplete` | Hint for the browser's autofill (e.g. `"username"`) | None |
| `max_chars` | Maximum number of characters | None |
| `placeholder` | Grey hint shown when empty | None |

## Used in
- [Login page](../login_page.md)
- [Nutrition page](../nutrition_page.md): recipe name, serving label, food search, the food name in the food pop-up, and new category names and renames (`max_chars=50`, the database limit)
