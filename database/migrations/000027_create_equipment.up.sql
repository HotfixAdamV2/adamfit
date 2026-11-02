/*
    Migration: 000027_create_equipment (up)

    What:
        Creates the equipment lookup table: what an exercise is done with
        (barbell, dumbbell, machine, ...).

    Why:
        standard_exercise and exercise (000031, 000034) reference this
        table with a foreign key, so the exercise list can be filtered by
        equipment and a new kind of equipment is one INSERT.

    Notes:
        - equipment_code is a natural primary key (no sequence), like
          serving_unit.unit_code. It is the value stored in
          standard_exercise.equipment and exercise.equipment.
        - sort_order is the order the app lists equipment in.
*/

-- Create the table
CREATE TABLE equipment (
    -- Fields
    equipment_code VARCHAR(20) NOT NULL,
    equipment_name VARCHAR(30) NOT NULL,
    sort_order SMALLINT NOT NULL DEFAULT 0,
    -- Constraints
    CONSTRAINT pk_equipment_equipment_code PRIMARY KEY (equipment_code),
    CONSTRAINT unq_equipment_equipment_name UNIQUE (equipment_name)
);

-- Give grants
-- None needed: the master role owns the table.
