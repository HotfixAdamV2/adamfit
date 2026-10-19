# st.selectbox

A dropdown that lets the user pick one option. Returns the chosen option (the original Python value, not its label).

## Basic example
```python
sex_options = [None, "male", "female"]
sex = st.selectbox(
    "Sex",
    sex_options,
    index=sex_options.index(user["sex"]),
    format_func=lambda s: "Not set" if s is None else s.title(),
)
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Text shown above the dropdown | required |
| `options` | The choices (any values: strings, dates, None...) | required |
| `index` | Position of the option selected at first | `0` |
| `format_func` | Function that turns each option into the text shown | `str` |
| `placeholder` | Text shown when nothing is selected | `"Choose an option"` |
| `key` | Unique name. Lets code read or set the choice via `st.session_state[key]` (setting only works before the widget is drawn) | None |

Pass `index=None` to start with nothing selected. Users can type in the box to search the options.

## Used in
- [My Profile page](../profile_page.md)
- [Nutrition page](../nutrition_page.md): searching foods and recipes, choosing a recipe, filtering by category
