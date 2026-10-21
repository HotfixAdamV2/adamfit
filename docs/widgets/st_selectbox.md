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
| `on_change` | Function to call (before the rerun) when the choice changes | None |
| `disabled` | Grey out the dropdown so it can't be changed | `False` |
| `width` | `"stretch"` to fill the row, or a width in pixels | `"stretch"` |

Pass `index=None` to start with nothing selected. Users can type in the box to search the options.

## Used in
- [My Profile page](../profile_page.md)
- [Nutrition page](../nutrition_page.md): searching foods and recipes, the Category and Sub-category filters above them (Sub-category is `disabled` until a category is picked, and the Category's `on_change` resets it), choosing a recipe, filtering the Foods tab by category, a food's category (starting empty with `index=None` for a new food, with a "+ New category" choice) and serving unit in the food pop-up, and in both pop-ups "Put it under" (a top-level category or "+ New top-level category") and the category to rename or remove
