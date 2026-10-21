# st.write

A flexible "show this" function. Strings are rendered as markdown, and other values (tables, dictionaries, charts) are displayed in a suitable way.

## Basic example
```python
st.write("Welcome to my personal fitness app.")
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `*args` | One or more things to display | required |
| `unsafe_allow_html` | Allow raw HTML in strings. Avoid unless needed | `False` |

## Used in
- Not used on any page at the moment. Pages use [st.markdown](st_markdown.md) for plain text.
