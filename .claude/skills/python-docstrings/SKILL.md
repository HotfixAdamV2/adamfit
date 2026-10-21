---
name: python-docstrings
description: Write NumPy-style docstrings with type hints for every Python function and class. Use whenever Python code is created or edited.
---

# Python Docstrings

Every function, method and class gets a NumPy-style docstring, and every function has type hints on all parameters and the return value.

Rules:
- First line is a brief description of what it does, as a command ("Fetch ...", "Return ...").
- Add `Parameters`, `Returns` (and `Raises` when relevant) sections. Omit sections that do not apply.
- Parameter lines are `name : type`, matching the type hints.
- Classes document their constructor arguments under `Parameters` and public attributes under `Attributes`.
- Add a short module docstring at the top of each file.

Example:

```python
def get_exercises(muscle_group: str | None = None) -> list[dict]:
    """
    Fetch exercises, optionally filtered by muscle group.

    Parameters
    ----------
    muscle_group : str | None, optional
        Only return exercises for this muscle group. Returns all when None.

    Returns
    -------
    list[dict]
        One dictionary per exercise, keyed by column name.
    """
```
