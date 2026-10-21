/*
    Migration: 000004_create_user_weight (down)

    What:
        Drops the user_weight table and its sequence.

    Why:
        Reverts 000004_create_user_weight.
*/

DROP TABLE user_weight;
