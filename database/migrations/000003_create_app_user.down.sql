/*
    Migration: 000003_create_app_user (down)

    What:
        Drops the app_user table and its sequence.

    Why:
        Reverts 000003_create_app_user.
*/

DROP TABLE app_user;
