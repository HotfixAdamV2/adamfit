# st.markdown

Shows text formatted with Markdown: `**bold**`, `*italics*`, lists, links and so on. Prefer it over [st.write](st_write.md) when you are only showing text.

## Basic example
```python
st.markdown("**Ingredients**")
st.markdown(recipe["instructions"])   # "1. Cook the rice\n2. ..." becomes a numbered list
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `body` | The Markdown text | required |
| `help` | Tooltip shown next to the text | None |
| `unsafe_allow_html` | Allow raw HTML. Avoid unless needed | `False` |

## Used in
- [Nutrition page](../nutrition_page.md): section labels and recipe instructions
