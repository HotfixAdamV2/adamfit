/*
    Migration: 000030_seed_muscle_group (down)

    What:
        Removes the built-in muscle groups.

    Why:
        Reverts 000030_seed_muscle_group.

    Notes:
        - User-owned groups are left alone (000029's down drops them).
*/

DELETE FROM muscle_group
WHERE user_id IS NULL;
