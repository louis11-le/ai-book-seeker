CREATE TABLE books (
  id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(255) NOT NULL,
  author VARCHAR(255) NOT NULL,
  description TEXT,
  age_range VARCHAR(10) NOT NULL,
  purpose ENUM('learning', 'entertainment') NOT NULL,
  genre VARCHAR(100),
  price DECIMAL(6,2) NOT NULL,
  tags TEXT,
  rating DECIMAL(2,1) DEFAULT 0.0
);

-- Sample data for testing
INSERT INTO books (title, author, description, age_range, purpose, genre, price, tags)
VALUES
('Learn to Read: Level 1', 'John Smith', 'A phonics-based reading book for beginners', '5-7', 'learning', 'education', 19.99, 'phonics,beginner,reading'),
('Reading Adventures for Kids', 'Mary Johnson', 'Fun stories for early readers', '6-8', 'learning', 'fiction', 24.99, 'early readers,fun,stories'),
('The Magic World', 'Emma Davis', 'Fantasy adventures for children', '7-10', 'entertainment', 'fantasy', 14.99, 'magic,adventure,fantasy'),
('Science for Young Minds', 'David Brown', 'Introduction to basic science concepts', '8-12', 'learning', 'science', 29.99, 'science,educational,experiments'),
('Bedtime Stories Collection', 'Susan White', 'Collection of calming bedtime stories', '4-8', 'entertainment', 'fiction', 17.99, 'bedtime,stories,relaxing'),
('Math is Fun', 'Robert Green', 'Making mathematics enjoyable for children', '9-12', 'learning', 'education', 22.99, 'math,puzzles,games'),
('The Adventures of Tom', 'James Wilson', 'Exciting adventures of a young boy', '10-14', 'entertainment', 'adventure', 15.99, 'adventure,exciting,young adult'),
('Animal Kingdom', 'Patricia Moore', 'Discover amazing facts about animals', '6-10', 'learning', 'nature', 26.99, 'animals,facts,nature'),
('Fairy Tales Reimagined', 'Karen Taylor', 'Classic fairy tales with modern twists', '7-11', 'entertainment', 'fantasy', 18.99, 'fairy tales,modern,reimagined'),
('Learning to Code for Kids', 'Michael Lee', 'Introduction to programming for children', '10-14', 'learning', 'technology', 32.99, 'coding,programming,technology')
;
