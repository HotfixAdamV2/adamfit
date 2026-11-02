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
| `help` | Tooltip shown next to the label | None |
| `disabled` | Greys the box out so nothing can be typed | `False` |
| `width` | `"stretch"` (fill the row) or a width in pixels, e.g. `150` | `"stretch"` |

## Used in
- [Exercises page](../exercises_page.md): the Search filter, the exercise name (`max_chars=100`), and new and renamed muscle group names (`max_chars=50`)
- [Login page](../login_page.md)
- [Nutrition page](../nutrition_page.md): the servings to add in the item picker (a number or a sum such as `4.2/1.5`, `max_chars=50`, `width=150`, with a `help` tooltip), recipe name, serving label, food search, the food name in the food pop-up, and new category names and renames (`max_chars=50`, the database limit)
