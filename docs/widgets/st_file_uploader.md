# st.file_uploader

A box where the user drops a file or picks one from their computer. It returns an `UploadedFile` (or None until a file is chosen). Read its contents with `.getvalue()`, which gives `bytes`, and its name with `.name`.

## Basic example
```python
upload = st.file_uploader("Picture", type=["jpg", "jpeg", "png"])
if upload is not None:
    data = upload.getvalue()
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `label` | Text shown above the box | required |
| `type` | File extensions (or MIME types) allowed, e.g. `["png", "gif"]`. A best-effort browser check only | Any file |
| `accept_multiple_files` | Allow several files (then it returns a list) | `False` |
| `max_upload_size` | Largest file allowed, in megabytes (whole number) | 200 MB (`server.maxUploadSize`) |
| `key` | Unique name. Its value in `st.session_state` is read-only | None |
| `help` | Tooltip next to the label | None |
| `on_change` | Function called before the rerun when a file is added or removed | Rerun only |

`type` only checks the file name, and anyone can rename a file. Always check the contents yourself before saving them. The Exercises page reads the first bytes of the file to tell its real image type (`exercises.check_image`).

## Used in
- [Exercises page](../exercises_page.md): choosing an exercise picture
