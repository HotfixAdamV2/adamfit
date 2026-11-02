/*
    Migration: 000027_create_equipment (down)

    What:
        Drops the equipment table.

    Why:
        Reverts 000027_create_equipment.
*/

DROP TABLE equipment;
