-- Add user_id column to images table
ALTER TABLE images ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);

-- Add user_id column to comments table
ALTER TABLE comments ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);

-- Add foreign key constraints
ALTER TABLE images ADD CONSTRAINT fk_images_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE comments ADD CONSTRAINT fk_comments_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;