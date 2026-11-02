/*
    Migration: 000029_create_muscle_group (down)

    What:
        Drops the muscle_group table, its sequence, index and trigger.

    Why:
        Reverts 000029_create_muscle_group.

    Notes:
        - Data loss: every user-created muscle group is deleted.
*/

DROP TABLE muscle_group;
