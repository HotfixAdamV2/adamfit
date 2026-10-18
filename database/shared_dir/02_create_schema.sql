/*
    Script: 02_create_schema.sql
    Run by: postgres (superuser), connected to "fitness"

    Purpose:
        Creates the "fit" schema. All application objects live here
        instead of the default "public" schema. Ownership and grants
        are assigned in 03_create_roles_and_security.sql.
*/

CREATE SCHEMA fit;
