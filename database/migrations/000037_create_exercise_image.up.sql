/*
    Migration: 000037_create_exercise_image (up)

    What:
        Creates the exercise_image table: at most one picture per
        exercise, stored in the database, and attaches
        fx_trg_set_updated_at.

    Why:
        Users can attach a picture (e.g. a form diagram) to their own
        exercises. Keeping the bytes in a separate table keeps the
        exercise table small, so listing exercises never reads image data.

    Notes:
        - exercise_id is both the primary key and the foreign key, so an
          exercise has zero or one image. Replace a picture with
              INSERT ... ON CONFLICT (exercise_id) DO UPDATE ...
          and remove it with DELETE.
        - ON DELETE CASCADE removes the image with the exercise (and so
          with the user). Soft-deleting an exercise keeps the image.
        - chk_exercise_image_mime_type allows image/jpeg, image/png,
          image/webp and image/gif.
        - chk_exercise_image_image_data requires 1 byte to 5 MB
          (5242880 bytes). The app should check the size before
          uploading so it can show a friendly message.
        - file_name is the original upload name, for display only.
*/

-- Create the table
CREATE TABLE exercise_image (
    -- Fields
    exercise_id INTEGER NOT NULL,
    image_data BYTEA NOT NULL,
    mime_type VARCHAR(20) NOT NULL,
    file_name VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    CONSTRAINT pk_exercise_image_exercise_id PRIMARY KEY (exercise_id),
    CONSTRAINT fk_exercise_image_exercise_id FOREIGN KEY (exercise_id)
        REFERENCES exercise (exercise_id) ON DELETE CASCADE,
    CONSTRAINT chk_exercise_image_mime_type
        CHECK (mime_type IN ('image/jpeg', 'image/png', 'image/webp', 'image/gif')),
    CONSTRAINT chk_exercise_image_image_data
        CHECK (OCTET_LENGTH(image_data) BETWEEN 1 AND 5242880)
);

-- Trigger assignments
CREATE TRIGGER trg_exercise_image_set_updated_at
    BEFORE UPDATE ON exercise_image
    FOR EACH ROW
    EXECUTE FUNCTION fx_trg_set_updated_at();

-- Give grants
-- None needed: the master role owns the table.
