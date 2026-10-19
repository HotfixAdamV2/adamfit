/*
    Script: 03_create_roles_and_security.sql
    Run by: postgres (superuser), connected to "fitness"
    Expects: psql variable master_password

    Purpose:
        Sets up the application's role and login user, locks down the
        "public" schema, and makes "fit" the working schema.

        - "master" is a group role that owns the "fit" schema.
        - "master_usr" is the login user. On every login it assumes the
          "master" role, so objects it creates (including migrations) are
          owned by "master".
*/

-- Role and user
CREATE ROLE master NOLOGIN;

CREATE ROLE master_usr LOGIN PASSWORD :'master_password';

GRANT master TO master_usr;

-- Every login by master_usr assumes the master role and starts in the fit schema
ALTER ROLE master_usr SET ROLE master;
ALTER ROLE master_usr SET search_path = fit;

-- Lock down the public schema and remove it from the search path
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE fitness FROM PUBLIC;
GRANT CONNECT ON DATABASE fitness TO master;

-- Allow temporary tables (session-only scratch tables, e.g. for staging
-- data inside a migration). They live in a private pg_temp schema, not public.
GRANT TEMPORARY ON DATABASE fitness TO master;

ALTER DATABASE fitness SET search_path = fit;

-- The master role owns the fit schema and has full control of it
ALTER SCHEMA fit OWNER TO master;
GRANT ALL ON SCHEMA fit TO master;

ALTER DEFAULT PRIVILEGES IN SCHEMA fit GRANT ALL ON TABLES TO master;
ALTER DEFAULT PRIVILEGES IN SCHEMA fit GRANT ALL ON SEQUENCES TO master;
ALTER DEFAULT PRIVILEGES IN SCHEMA fit GRANT ALL ON FUNCTIONS TO master;
