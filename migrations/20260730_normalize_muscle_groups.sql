-- Normalize muscle_group to a fixed set of categories so the exercise form
-- can use a <select> instead of free text (which was creating near-duplicate
-- groups like 'abs' vs 'core').

-- Fold known free-text duplicates into their canonical category.
UPDATE fitness_exercise SET muscle_group = 'core' WHERE muscle_group = 'abs';

ALTER TABLE fitness_exercise
  MODIFY muscle_group ENUM('chest','back','shoulders','arms','forearms','legs','glutes','core','cardio','full_body') DEFAULT NULL;
