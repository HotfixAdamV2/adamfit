---
name: sql-naming
description: Naming conventions for database objects (sequences, views, functions, triggers, indexes, constraints). Use when creating any database object.
---

# SQL Naming Conventions

| Object | Prefix / format | Example |
|--------|-----------------|---------|
| Sequence | `seq_{table}_{column}` | `seq_mytable_user_id` |
| View | `vw_` | `vw_active_users` |
| Function | `fx_` | `fx_calc_bmi` |
| Stored procedure | `sproc_` | `sproc_archive_workouts` |
| Trigger function | `fx_trg_` | `fx_trg_set_updated_at` |
| Trigger | `trg_` | `trg_mytable_set_updated_at` |
| Index | `idx_{table}_{column}` | `idx_mytable_user_phone` |
| Unique index/constraint | `unq_{table}_{column}` | `unq_mytable_user_name` |
| Primary key | `pk_{table}_{column}` | `pk_mytable_user_id` |
| Foreign key | `fk_{table}_{column}` | `fk_workout_user_id` |
| Check constraint | `chk_{table}_{column}` | `chk_mytable_age` |

Rules:
- Constraint names always follow `{type}_{table_name}_` and normally end with the column name.
- NOT NULL constraints do not need names.
- Always name constraints explicitly in `CREATE TABLE`.
