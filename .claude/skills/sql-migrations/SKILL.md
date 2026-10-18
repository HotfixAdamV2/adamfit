---
name: sql-migrations
description: How to write migration scripts and CREATE TABLE statements (header comment, sequences instead of SERIAL, constraints after fields, script contents). Use when adding or editing files in database/migrations/.
---

# Migration Scripts and Table Creation

Also follow the `sql-formatting` and `sql-naming` skills.

## Files
- golang-migrate pairs in `database/migrations/`: `NNNNNN_description.up.sql` and `.down.sql`, numbered sequentially.
- Every script starts with a multi-line `/* ... */` comment stating **what** it does and **why** it is needed.
- Migrations run as `master_usr` with search path `fit`. Do not schema-qualify and never use `public`.
- Always write a working `.down.sql`.

## Tables
- Never use `SERIAL` or `GENERATED ... AS IDENTITY` for auto-incrementing keys. Create a sequence and use `DEFAULT nextval('seq_...')`.
- Define all columns and constraints inside the one `CREATE TABLE`, with constraints after the fields.
- Add `ALTER SEQUENCE ... OWNED BY table.column` so the sequence drops with the table.

A new-table script contains, in order: sequence creation, table definition, index creation, grants.

```sql
-- Create sequence
CREATE SEQUENCE seq_mytable_user_id AS INT
    INCREMENT BY 1
    MINVALUE 1
    START WITH 1
    NO CYCLE;

-- Create the table
CREATE TABLE mytable (
    -- Fields
    user_id INTEGER NOT NULL DEFAULT nextval('seq_mytable_user_id'),
    user_name VARCHAR(25) NOT NULL,
    user_phone VARCHAR(15),
    -- Constraints
    CONSTRAINT pk_mytable_user_id PRIMARY KEY (user_id),
    CONSTRAINT unq_mytable_user_name UNIQUE (user_name)
);

ALTER SEQUENCE seq_mytable_user_id OWNED BY mytable.user_id;

-- Create an index
CREATE INDEX idx_mytable_user_phone ON mytable (user_phone);

-- Give grants
GRANT SELECT ON mytable TO some_role;
```

## Triggers
A trigger script contains both, in order: the trigger function (`fx_trg_...`), then the trigger (`trg_...`) that attaches it.
