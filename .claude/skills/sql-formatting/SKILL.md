---
name: sql-formatting
description: SQL layout and keyword style (capitalized keywords, indentation, CTEs, inserts). Use whenever writing or editing SQL.
---

# SQL Formatting

- All SQL keywords are UPPERCASE (`SELECT`, `FROM`, `AS`, `INSERT INTO`, `WITH`, `NOT NULL`, ...). Identifiers are lowercase snake_case.
- Indent 4 spaces. One column per line in `SELECT` lists and column lists.
- A CTE body is indented under its name. `WITH` stands alone on its line.
- Parenthesised column lists in `INSERT INTO` put each column on its own line, with the closing `)` on its own line.
- Use `--` for short comments.

Example:

```sql
WITH
    mycte AS (
        SELECT
            user_id,
            user_name,
            user_email
        FROM mytable
    )
INSERT INTO my_other_table (
    user_id,
    user_name,
    user_email,
    insert_timestamp
)
SELECT
    user_id,
    user_name,
    user_email,
    CURRENT_TIMESTAMP
FROM mycte
```
