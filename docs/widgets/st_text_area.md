# st.text_area

A multi-line text box. Returns whatever the user typed (an empty string if nothing). Use it instead of [st.text_input](st_text_input.md) for longer text.

## Basic example
```python
instructions = st.text_area("Instructions", value=recipe["instructions"] or "", height=200)
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Text shown above the box | required |
| `value` | Starting text | `""` |
| `height` | Height in pixels | About three lines |
| `max_chars` | Maximum number of characters | None |
| `placeholder` | Grey hint shown when empty | None |
| `help` | Tooltip next to the label | None |

## Used in
- [Nutrition page](../nutrition_page.md): recipe instructions
