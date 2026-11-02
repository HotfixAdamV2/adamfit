# st.image

Shows a picture. It accepts a file path, a web address, or the picture's bytes (for example straight from the database or from [st.file_uploader](st_file_uploader.md)).

## Basic example
```python
st.image(current["image_data"], caption=current["file_name"], width=300, alt=f"Picture for {name}")
```

## Parameters
| Parameter | What it does | Default |
|-----------|--------------|---------|
| `image` | The picture: path, URL or bytes (or a list of them) | required |
| `caption` | Small text under the picture | None |
| `width` | `"content"` (natural size, never wider than the page), `"stretch"` (fill the space) or a number of pixels | `"content"` |
| `alt` | Name read out by screen readers. Use `""` only for decorative pictures | None |

Inside a column, the default `width="content"` keeps a small picture at its own size and shrinks a big one to fit the column. The Exercises details panel relies on this:
```python
st.image(image["image_data"], alt=f"Picture for {row['exercise_name']}")
```

## Used in
- [Exercises page](../exercises_page.md): the picture in the details panel (in the right-hand column), and the current picture and a preview of a newly chosen one in the Edit exercise pop-up
