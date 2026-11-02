/*
    Migration: 000028_seed_equipment (down)

    What:
        Removes the seeded equipment types.

    Why:
        Reverts 000028_seed_equipment.
*/

DELETE FROM equipment;
