/*
    Migration: 000033_seed_standard_exercise (up)

    What:
        Inserts the starter list of 56 standard exercises (46 strength,
        10 cardio) with short instructions, and tags each strength
        exercise with its primary and secondary muscle groups in
        standard_exercise_muscle_group.

    Why:
        Users should not have to type in common exercises before they can
        start logging workouts. Each user gets an editable copy of this
        list (see 000038).

    Notes:
        - Cardio exercises have no muscle tags.
        - Muscle groups are looked up by name rather than hard-coded ids.
          The tags are staged in a temporary table first, and the script
          stops with an error if any exercise or muscle name in it does
          not match, so a typo cannot silently drop a tag.
*/

-- Exercises
INSERT INTO standard_exercise (
    exercise_name,
    exercise_type,
    equipment,
    instructions
)
VALUES
    -- Legs
    ('Barbell Back Squat', 'strength', 'barbell', 'Rest the bar across your upper back and stand with feet about shoulder-width apart. Brace your core, then sit your hips back and down until your thighs are at least parallel to the floor. Keep your chest up and knees tracking over your toes, then drive back up to standing.'),
    ('Front Squat', 'strength', 'barbell', 'Rest the bar on the front of your shoulders with elbows high and upper arms close to parallel to the floor. Squat straight down, keeping your torso upright and elbows up. Drive through your whole foot to stand back up.'),
    ('Goblet Squat', 'strength', 'kettlebell', 'Hold a kettlebell by the horns close to your chest. Squat down between your knees, keeping your chest tall and heels on the floor. Pause at the bottom, then stand back up.'),
    ('Deadlift', 'strength', 'barbell', 'Stand with the bar over your mid-foot, then hinge down and grip it just outside your legs. Brace your core, flatten your back and push the floor away to stand up tall with the bar close to your body. Lower it under control by pushing your hips back.'),
    ('Romanian Deadlift', 'strength', 'barbell', 'Hold the bar at hip height with a shoulder-width grip and soft knees. Push your hips back and slide the bar down your thighs until you feel a strong stretch in your hamstrings, keeping your back flat. Squeeze your glutes to return to standing.'),
    ('Leg Press', 'strength', 'machine', 'Sit in the machine with your feet shoulder-width apart on the platform. Release the safeties and lower the platform until your knees reach about 90 degrees, without letting your lower back lift off the pad. Press back up without locking your knees.'),
    ('Leg Extension', 'strength', 'machine', 'Sit with the pad resting on your lower shins and your knees in line with the machine''s pivot. Straighten your legs fully and squeeze your quads at the top. Lower slowly under control.'),
    ('Lying Leg Curl', 'strength', 'machine', 'Lie face down with the pad just above your heels and your knees just off the bench. Curl your heels toward your glutes, keeping your hips pressed into the pad. Lower slowly to the start.'),
    ('Walking Lunge', 'strength', 'dumbbell', 'Hold a dumbbell in each hand at your sides. Step forward and lower until both knees are bent to about 90 degrees, with the back knee just above the floor. Push through the front foot and bring the back leg through into the next step.'),
    ('Bulgarian Split Squat', 'strength', 'dumbbell', 'Stand a stride in front of a bench and rest the top of your back foot on it, holding a dumbbell in each hand. Lower straight down until your front thigh is about parallel to the floor. Drive through the front heel to stand back up, then switch legs after the set.'),
    ('Hip Thrust', 'strength', 'barbell', 'Sit with your upper back against a bench and a padded bar across your hips, feet flat and shoulder-width apart. Drive through your heels to lift your hips until your body is straight from shoulders to knees. Squeeze your glutes at the top, then lower under control.'),
    ('Standing Calf Raise', 'strength', 'machine', 'Stand with the balls of your feet on the platform and the pads on your shoulders. Lower your heels as far as is comfortable for a full stretch. Rise up onto your toes as high as you can and pause before lowering.'),
    ('Seated Calf Raise', 'strength', 'machine', 'Sit with the balls of your feet on the platform and the pad resting on your lower thighs. Lower your heels for a full stretch, then press up onto your toes as high as you can. Pause at the top before lowering.'),
    ('Hip Adductor Machine', 'strength', 'machine', 'Sit in the machine with the pads against the inside of your knees and your legs spread. Squeeze your legs together in a smooth arc. Return slowly to the start position.'),
    ('Hip Abductor Machine', 'strength', 'machine', 'Sit in the machine with the pads against the outside of your knees and your legs together. Push your legs apart as far as is comfortable. Return slowly to the start position.'),
    ('Kettlebell Swing', 'strength', 'kettlebell', 'Stand with feet a little wider than shoulder-width and the kettlebell slightly in front of you. Hike it back between your legs, then snap your hips forward to swing it to chest height with straight arms. Let it fall back between your legs and repeat, keeping the movement driven by your hips, not your arms.'),
    ('Back Extension', 'strength', 'bodyweight', 'Set yourself in a back extension bench with the pad just below your hips and your feet locked in. Lower your torso by bending at the hips, keeping your back flat. Raise back up until your body is in a straight line, squeezing your glutes.'),
    -- Chest
    ('Barbell Bench Press', 'strength', 'barbell', 'Lie on a flat bench with your eyes under the bar and grip it slightly wider than shoulder-width. Unrack it, then lower it under control to your mid-chest with elbows about 45 degrees from your body. Press it back up to straight arms, keeping your feet planted and shoulder blades pulled together.'),
    ('Dumbbell Bench Press', 'strength', 'dumbbell', 'Lie on a flat bench holding a dumbbell in each hand at chest level, palms facing your feet. Press the dumbbells up until your arms are straight above your chest. Lower them slowly back to the sides of your chest.'),
    ('Incline Dumbbell Press', 'strength', 'dumbbell', 'Set a bench to about 30 to 45 degrees and lie back with a dumbbell in each hand at your upper chest. Press the dumbbells up and slightly together until your arms are straight. Lower them slowly to the start.'),
    ('Machine Chest Press', 'strength', 'machine', 'Adjust the seat so the handles line up with your mid-chest. Press the handles forward until your arms are straight but not locked. Return slowly until you feel a stretch across your chest.'),
    ('Cable Fly', 'strength', 'cable', 'Set both pulleys at about shoulder height and hold a handle in each hand, stepping forward into a split stance. With a slight bend in your elbows, bring your hands together in front of your chest in a wide arc. Open back up slowly until you feel a stretch across your chest.'),
    ('Push-Up', 'strength', 'bodyweight', 'Start in a high plank with your hands slightly wider than shoulder-width. Keeping your body in a straight line, lower your chest to just above the floor. Push back up to straight arms.'),
    ('Dip', 'strength', 'bodyweight', 'Support yourself on parallel bars with straight arms. Lower your body by bending your elbows until your upper arms are about parallel to the floor, leaning slightly forward to work the chest more. Press back up to straight arms.'),
    -- Shoulders
    ('Overhead Press', 'strength', 'barbell', 'Stand holding the bar at shoulder height with a grip just outside your shoulders. Brace your core and glutes, then press the bar straight overhead, moving your head back slightly to let it pass. Lock out with the bar over your mid-foot, then lower it to your shoulders.'),
    ('Dumbbell Shoulder Press', 'strength', 'dumbbell', 'Sit on an upright bench holding a dumbbell in each hand at shoulder height, palms facing forward. Press the dumbbells overhead until your arms are straight. Lower them slowly back to shoulder height.'),
    ('Lateral Raise', 'strength', 'dumbbell', 'Stand holding a dumbbell in each hand at your sides with a slight bend in your elbows. Raise your arms out to the sides until they are level with your shoulders. Lower slowly, without swinging.'),
    ('Rear Delt Fly', 'strength', 'dumbbell', 'Hinge forward at the hips with a flat back, holding a dumbbell in each hand below your chest. With a slight bend in your elbows, raise your arms out to the sides until they are level with your body. Lower slowly to the start.'),
    ('Face Pull', 'strength', 'cable', 'Set a rope on a cable at upper-chest height or higher and grab it with both hands, palms facing in. Pull the rope toward your face, splitting the ends and driving your elbows out and back. Squeeze your upper back, then return slowly.'),
    ('Band Pull-Apart', 'strength', 'band', 'Hold a resistance band in front of you at shoulder height with straight arms and hands about shoulder-width apart. Pull the band apart by moving your hands out to the sides until it touches your chest. Return slowly to the start.'),
    ('Barbell Shrug', 'strength', 'barbell', 'Stand holding a barbell in front of your thighs with a shoulder-width grip. Lift your shoulders straight up toward your ears as high as you can. Pause, then lower slowly without rolling your shoulders.'),
    -- Back
    ('Pull-Up', 'strength', 'bodyweight', 'Hang from a bar with an overhand grip slightly wider than your shoulders. Pull yourself up by driving your elbows down until your chin is over the bar. Lower yourself under control to a full hang.'),
    ('Chin-Up', 'strength', 'bodyweight', 'Hang from a bar with an underhand grip about shoulder-width apart. Pull yourself up until your chin is over the bar, keeping your elbows close to your body. Lower yourself under control to a full hang.'),
    ('Lat Pulldown', 'strength', 'cable', 'Sit with your thighs under the pads and grip the bar slightly wider than your shoulders. Pull the bar down to your upper chest, driving your elbows down and back. Let the bar rise slowly until your arms are straight.'),
    ('Barbell Row', 'strength', 'barbell', 'Hold a barbell with an overhand grip and hinge forward until your torso is close to parallel to the floor, back flat. Row the bar to your lower chest or upper stomach, squeezing your shoulder blades together. Lower it under control to straight arms.'),
    ('Dumbbell Row', 'strength', 'dumbbell', 'Place one knee and the same-side hand on a bench, holding a dumbbell in the other hand with your arm straight. Row the dumbbell toward your hip, keeping your elbow close to your body. Lower it slowly, then switch sides after the set.'),
    ('Seated Cable Row', 'strength', 'cable', 'Sit at the cable row station with your feet on the platform and knees slightly bent, holding the handle with straight arms. Pull the handle to your stomach while keeping your torso upright and squeezing your shoulder blades together. Return slowly until your arms are straight.'),
    -- Arms
    ('Barbell Curl', 'strength', 'barbell', 'Stand holding a barbell with an underhand, shoulder-width grip and arms straight. Curl the bar up toward your shoulders, keeping your elbows at your sides. Lower slowly to straight arms.'),
    ('Dumbbell Curl', 'strength', 'dumbbell', 'Stand holding a dumbbell in each hand at your sides, palms facing forward. Curl the dumbbells up toward your shoulders without moving your elbows forward. Lower slowly to straight arms.'),
    ('Hammer Curl', 'strength', 'dumbbell', 'Stand holding a dumbbell in each hand at your sides, palms facing each other. Curl the dumbbells up toward your shoulders, keeping your palms facing in and elbows at your sides. Lower slowly to straight arms.'),
    ('Triceps Pushdown', 'strength', 'cable', 'Stand facing a high cable holding a bar or rope with your elbows tucked at your sides. Push the handle down until your arms are fully straight, squeezing your triceps. Let it rise slowly until your forearms are just above parallel to the floor.'),
    ('Skull Crusher', 'strength', 'barbell', 'Lie on a flat bench holding an EZ-bar or barbell above your chest with straight arms. Bend only at the elbows to lower the bar toward your forehead. Straighten your arms to press it back up.'),
    -- Core
    ('Plank', 'strength', 'bodyweight', 'Rest on your forearms and toes with your elbows under your shoulders. Keep your body in a straight line from head to heels by bracing your abs and squeezing your glutes. Hold the position for time without letting your hips sag.'),
    ('Hanging Leg Raise', 'strength', 'bodyweight', 'Hang from a pull-up bar with straight arms. Keeping your legs as straight as you can, raise them in front of you to at least hip height, curling your pelvis up at the top. Lower slowly without swinging.'),
    ('Cable Crunch', 'strength', 'cable', 'Kneel facing a high cable holding a rope beside your head. Crunch down by curling your spine and bringing your elbows toward your knees, keeping your hips still. Return slowly to the start.'),
    ('Russian Twist', 'strength', 'bodyweight', 'Sit with your knees bent and lean back slightly with a straight back, feet on the floor or raised. Rotate your torso to one side, then the other, touching your hands to the floor beside your hips. Hold a weight to make it harder.'),
    -- Cardio
    ('Treadmill Run', 'cardio', 'machine', 'Run on a treadmill at a steady pace or in intervals. Start with a few minutes of walking or easy jogging to warm up. Setting a 1 percent incline better matches outdoor running.'),
    ('Outdoor Run', 'cardio', 'none', 'Run outdoors at a steady pace or in intervals. Warm up with a few minutes of easy jogging and cool down with a walk. Keep an easy, conversational pace for most runs.'),
    ('Stationary Bike', 'cardio', 'machine', 'Ride an upright or recumbent stationary bike. Set the seat so your knee is slightly bent at the bottom of each pedal stroke. Adjust the resistance for steady riding or intervals.'),
    ('Outdoor Cycling', 'cardio', 'none', 'Ride a bike outdoors at a steady pace or in intervals. Wear a helmet and check your tyres and brakes before you set off. Track time and distance for each ride.'),
    ('Rowing Machine', 'cardio', 'machine', 'Strap your feet in and grab the handle with straight arms. Drive with your legs first, then lean back slightly and pull the handle to your lower ribs. Reverse the order on the way back: arms, then body, then legs.'),
    ('Elliptical', 'cardio', 'machine', 'Stand on the pedals and hold the moving handles. Move in a smooth, gliding stride, pushing and pulling with your arms as well as your legs. Adjust the resistance and incline to change the intensity.'),
    ('Stair Climber', 'cardio', 'machine', 'Step onto the machine and choose a steady pace. Stand tall and use the rails only lightly for balance, letting your legs do the work. Increase the speed or use intervals to make it harder.'),
    ('Jump Rope', 'cardio', 'none', 'Hold a handle in each hand with the rope behind you. Swing the rope over your head using your wrists, and hop just high enough for it to pass under your feet. Land softly on the balls of your feet.'),
    ('Swimming', 'cardio', 'none', 'Swim laps at a steady pace in any stroke, such as freestyle or breaststroke. Warm up with a few easy lengths before picking up the pace. Track time and distance for each session.'),
    ('Walking', 'cardio', 'none', 'Walk at a brisk pace, outdoors or indoors. Stand tall, swing your arms naturally and land on your heel, rolling through to your toes. Track time and distance, or steps.');

-- Stage the muscle tags: exercise name, muscle group name, is_primary
CREATE TEMPORARY TABLE tmp_standard_exercise_tag (
    exercise_name VARCHAR(100) NOT NULL,
    muscle_group_name VARCHAR(50) NOT NULL,
    is_primary BOOLEAN NOT NULL
);

INSERT INTO tmp_standard_exercise_tag (
    exercise_name,
    muscle_group_name,
    is_primary
)
VALUES
    -- Legs
    ('Barbell Back Squat', 'Quads', TRUE),
    ('Barbell Back Squat', 'Glutes', TRUE),
    ('Barbell Back Squat', 'Hamstrings', FALSE),
    ('Barbell Back Squat', 'Adductors', FALSE),
    ('Barbell Back Squat', 'Lower Back', FALSE),
    ('Barbell Back Squat', 'Abs', FALSE),
    ('Front Squat', 'Quads', TRUE),
    ('Front Squat', 'Glutes', FALSE),
    ('Front Squat', 'Upper Back', FALSE),
    ('Front Squat', 'Abs', FALSE),
    ('Goblet Squat', 'Quads', TRUE),
    ('Goblet Squat', 'Glutes', TRUE),
    ('Goblet Squat', 'Adductors', FALSE),
    ('Goblet Squat', 'Abs', FALSE),
    ('Deadlift', 'Hamstrings', TRUE),
    ('Deadlift', 'Glutes', TRUE),
    ('Deadlift', 'Lower Back', TRUE),
    ('Deadlift', 'Quads', FALSE),
    ('Deadlift', 'Traps', FALSE),
    ('Deadlift', 'Lats', FALSE),
    ('Deadlift', 'Forearms', FALSE),
    ('Romanian Deadlift', 'Hamstrings', TRUE),
    ('Romanian Deadlift', 'Glutes', TRUE),
    ('Romanian Deadlift', 'Lower Back', FALSE),
    ('Romanian Deadlift', 'Forearms', FALSE),
    ('Leg Press', 'Quads', TRUE),
    ('Leg Press', 'Glutes', TRUE),
    ('Leg Press', 'Hamstrings', FALSE),
    ('Leg Press', 'Adductors', FALSE),
    ('Leg Extension', 'Quads', TRUE),
    ('Lying Leg Curl', 'Hamstrings', TRUE),
    ('Lying Leg Curl', 'Calves', FALSE),
    ('Walking Lunge', 'Quads', TRUE),
    ('Walking Lunge', 'Glutes', TRUE),
    ('Walking Lunge', 'Hamstrings', FALSE),
    ('Walking Lunge', 'Adductors', FALSE),
    ('Walking Lunge', 'Calves', FALSE),
    ('Bulgarian Split Squat', 'Quads', TRUE),
    ('Bulgarian Split Squat', 'Glutes', TRUE),
    ('Bulgarian Split Squat', 'Hamstrings', FALSE),
    ('Bulgarian Split Squat', 'Adductors', FALSE),
    ('Hip Thrust', 'Glutes', TRUE),
    ('Hip Thrust', 'Hamstrings', FALSE),
    ('Hip Thrust', 'Quads', FALSE),
    ('Standing Calf Raise', 'Calves', TRUE),
    ('Seated Calf Raise', 'Calves', TRUE),
    ('Hip Adductor Machine', 'Adductors', TRUE),
    ('Hip Abductor Machine', 'Abductors', TRUE),
    ('Hip Abductor Machine', 'Glutes', FALSE),
    ('Kettlebell Swing', 'Glutes', TRUE),
    ('Kettlebell Swing', 'Hamstrings', TRUE),
    ('Kettlebell Swing', 'Lower Back', FALSE),
    ('Kettlebell Swing', 'Abs', FALSE),
    ('Kettlebell Swing', 'Front Delts', FALSE),
    ('Kettlebell Swing', 'Forearms', FALSE),
    ('Back Extension', 'Lower Back', TRUE),
    ('Back Extension', 'Glutes', FALSE),
    ('Back Extension', 'Hamstrings', FALSE),
    -- Chest
    ('Barbell Bench Press', 'Chest', TRUE),
    ('Barbell Bench Press', 'Front Delts', FALSE),
    ('Barbell Bench Press', 'Triceps', FALSE),
    ('Dumbbell Bench Press', 'Chest', TRUE),
    ('Dumbbell Bench Press', 'Front Delts', FALSE),
    ('Dumbbell Bench Press', 'Triceps', FALSE),
    ('Incline Dumbbell Press', 'Chest', TRUE),
    ('Incline Dumbbell Press', 'Front Delts', TRUE),
    ('Incline Dumbbell Press', 'Triceps', FALSE),
    ('Machine Chest Press', 'Chest', TRUE),
    ('Machine Chest Press', 'Front Delts', FALSE),
    ('Machine Chest Press', 'Triceps', FALSE),
    ('Cable Fly', 'Chest', TRUE),
    ('Cable Fly', 'Front Delts', FALSE),
    ('Push-Up', 'Chest', TRUE),
    ('Push-Up', 'Front Delts', FALSE),
    ('Push-Up', 'Triceps', FALSE),
    ('Push-Up', 'Abs', FALSE),
    ('Dip', 'Chest', TRUE),
    ('Dip', 'Triceps', TRUE),
    ('Dip', 'Front Delts', FALSE),
    -- Shoulders
    ('Overhead Press', 'Front Delts', TRUE),
    ('Overhead Press', 'Side Delts', FALSE),
    ('Overhead Press', 'Triceps', FALSE),
    ('Overhead Press', 'Traps', FALSE),
    ('Overhead Press', 'Abs', FALSE),
    ('Dumbbell Shoulder Press', 'Front Delts', TRUE),
    ('Dumbbell Shoulder Press', 'Side Delts', FALSE),
    ('Dumbbell Shoulder Press', 'Triceps', FALSE),
    ('Lateral Raise', 'Side Delts', TRUE),
    ('Lateral Raise', 'Traps', FALSE),
    ('Rear Delt Fly', 'Rear Delts', TRUE),
    ('Rear Delt Fly', 'Upper Back', FALSE),
    ('Face Pull', 'Rear Delts', TRUE),
    ('Face Pull', 'Upper Back', FALSE),
    ('Face Pull', 'Traps', FALSE),
    ('Band Pull-Apart', 'Rear Delts', TRUE),
    ('Band Pull-Apart', 'Upper Back', FALSE),
    ('Band Pull-Apart', 'Traps', FALSE),
    ('Barbell Shrug', 'Traps', TRUE),
    ('Barbell Shrug', 'Forearms', FALSE),
    -- Back
    ('Pull-Up', 'Lats', TRUE),
    ('Pull-Up', 'Upper Back', FALSE),
    ('Pull-Up', 'Biceps', FALSE),
    ('Pull-Up', 'Forearms', FALSE),
    ('Chin-Up', 'Lats', TRUE),
    ('Chin-Up', 'Biceps', TRUE),
    ('Chin-Up', 'Upper Back', FALSE),
    ('Chin-Up', 'Forearms', FALSE),
    ('Lat Pulldown', 'Lats', TRUE),
    ('Lat Pulldown', 'Upper Back', FALSE),
    ('Lat Pulldown', 'Biceps', FALSE),
    ('Barbell Row', 'Upper Back', TRUE),
    ('Barbell Row', 'Lats', TRUE),
    ('Barbell Row', 'Rear Delts', FALSE),
    ('Barbell Row', 'Biceps', FALSE),
    ('Barbell Row', 'Lower Back', FALSE),
    ('Dumbbell Row', 'Lats', TRUE),
    ('Dumbbell Row', 'Upper Back', TRUE),
    ('Dumbbell Row', 'Rear Delts', FALSE),
    ('Dumbbell Row', 'Biceps', FALSE),
    ('Seated Cable Row', 'Upper Back', TRUE),
    ('Seated Cable Row', 'Lats', TRUE),
    ('Seated Cable Row', 'Rear Delts', FALSE),
    ('Seated Cable Row', 'Biceps', FALSE),
    -- Arms
    ('Barbell Curl', 'Biceps', TRUE),
    ('Barbell Curl', 'Forearms', FALSE),
    ('Dumbbell Curl', 'Biceps', TRUE),
    ('Dumbbell Curl', 'Forearms', FALSE),
    ('Hammer Curl', 'Biceps', TRUE),
    ('Hammer Curl', 'Forearms', TRUE),
    ('Triceps Pushdown', 'Triceps', TRUE),
    ('Skull Crusher', 'Triceps', TRUE),
    -- Core
    ('Plank', 'Abs', TRUE),
    ('Plank', 'Obliques', FALSE),
    ('Plank', 'Lower Back', FALSE),
    ('Hanging Leg Raise', 'Abs', TRUE),
    ('Hanging Leg Raise', 'Hip Flexors', TRUE),
    ('Hanging Leg Raise', 'Obliques', FALSE),
    ('Hanging Leg Raise', 'Forearms', FALSE),
    ('Cable Crunch', 'Abs', TRUE),
    ('Cable Crunch', 'Obliques', FALSE),
    ('Russian Twist', 'Obliques', TRUE),
    ('Russian Twist', 'Abs', FALSE),
    ('Russian Twist', 'Hip Flexors', FALSE);

-- Stop if any staged name does not match an exercise or a built-in group
DO $$
DECLARE
    unmatched_list TEXT;
BEGIN
    SELECT
        STRING_AGG(t.exercise_name || ' / ' || t.muscle_group_name, '; ')
    INTO unmatched_list
    FROM tmp_standard_exercise_tag AS t
    LEFT JOIN standard_exercise AS se
        ON se.exercise_name = t.exercise_name
    LEFT JOIN muscle_group AS mg
        ON mg.muscle_group_name = t.muscle_group_name
        AND mg.user_id IS NULL
    WHERE se.standard_exercise_id IS NULL
        OR mg.muscle_group_id IS NULL;

    IF unmatched_list IS NOT NULL THEN
        RAISE EXCEPTION 'Unmatched exercise or muscle group names in 000033: %', unmatched_list;
    END IF;
END;
$$;

-- Muscle tags
INSERT INTO standard_exercise_muscle_group (
    standard_exercise_id,
    muscle_group_id,
    is_primary
)
SELECT
    se.standard_exercise_id,
    mg.muscle_group_id,
    t.is_primary
FROM tmp_standard_exercise_tag AS t
INNER JOIN standard_exercise AS se
    ON se.exercise_name = t.exercise_name
INNER JOIN muscle_group AS mg
    ON mg.muscle_group_name = t.muscle_group_name
    AND mg.user_id IS NULL;

DROP TABLE tmp_standard_exercise_tag;
