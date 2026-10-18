# st.success and st.error

Coloured message boxes. `st.success` is green and is for things that worked. `st.error` is red and is for failures. Streamlit also has `st.info` (blue) and `st.warning` (yellow), which work the same way.

## Basic example
```python
st.success("Connected to the database.")
st.error(f"Could not connect to the database: {exc}")
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `body` | The message text (supports markdown) | required |
| `icon` | Emoji or icon shown at the left of the box | A default icon |

## Used in
- [Home page](../home_page.md)
