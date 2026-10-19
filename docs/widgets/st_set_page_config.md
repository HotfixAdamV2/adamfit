# st.set_page_config

Sets page-level options such as the browser tab title and icon. It must be the first Streamlit call in the script.

## Basic example
```python
st.set_page_config(page_title="AdamFit", page_icon=":muscle:")
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `page_title` | Text shown in the browser tab | The script name |
| `page_icon` | Emoji, `:shortcode:` or image shown in the tab | Streamlit logo |
| `layout` | `"centered"` or `"wide"` | `"centered"` |
| `initial_sidebar_state` | `"auto"`, `"expanded"` or `"collapsed"` | `"auto"` |

## Used in
- [App router (`app.py`)](../streamlit_basics.md#multipage-apps-and-the-router)
