/*
    Migration: 000022_create_google_health_connection (down)

    What:
        Drops the google_health_connection table, its constraints and
        trigger.

    Why:
        Reverts 000022_create_google_health_connection.

    Notes:
        - Stored Google tokens are deleted with the table. Users must
          reconnect to Google Health after migrating up again.
*/

DROP TABLE google_health_connection;
