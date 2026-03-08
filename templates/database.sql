-- Create the database
CREATE DATABASE IF NOT EXISTS placement_management;
USE placement_management;

-- Create Departments table
CREATE TABLE departments (
    dept_id INT PRIMARY KEY AUTO_INCREMENT,
    dept_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Users table (for authentication)
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_type ENUM('student', 'faculty', 'admin') NOT NULL,
    is_email_verified BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- Create Faculty table
CREATE TABLE faculty (
    faculty_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE,
    dept_id INT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(15),
    designation VARCHAR(50),
    joining_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

-- Create Students table
CREATE TABLE students (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE,
    dept_id INT,
    roll_number VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(15),
    cgpa DECIMAL(3,2),
    batch_year INT,
    is_open_to_work BOOLEAN DEFAULT FALSE,
    work_status_approved BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

-- Create Skills table
CREATE TABLE skills (
    skill_id INT PRIMARY KEY AUTO_INCREMENT,
    skill_name VARCHAR(50) NOT NULL UNIQUE
);

-- Create Student Skills table
CREATE TABLE student_skills (
    student_id INT,
    skill_id INT,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    PRIMARY KEY (student_id, skill_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
);

-- Create Student Achievements table
CREATE TABLE student_achievements (
    achievement_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    achievement_date DATE,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- Create Work Status Requests table
CREATE TABLE work_status_requests (
    request_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    faculty_id INT,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_date TIMESTAMP NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id)
);

-- Insert Departments
INSERT INTO departments (dept_name) VALUES 
('IT'),
('ENTC'),
('MECH'),
('Civil'),
('Electrical');

-- Insert Skills
INSERT INTO skills (skill_name) VALUES 
('Programming'),
('Database Management'),
('Web Development'),
('Machine Learning'),
('Communication'),
('Problem Solving'),
('Project Management'),
('Data Analysis'),
('Circuit Design'),
('CAD/CAM'),
('Structural Analysis'),
('Power Systems');

-- Insert Admin account
INSERT INTO users (email, password_hash, user_type, is_email_verified, is_approved) VALUES
('admin@gcekarad.ac.in', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'admin', TRUE, TRUE);

-- Insert Faculty members (2 per department)
INSERT INTO users (email, password_hash, user_type, is_email_verified, is_approved) VALUES
('faculty1_it@gcekarad.ac.in', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'faculty', TRUE, TRUE),
('faculty2_it@gcekarad.ac.in', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'faculty', TRUE, TRUE),
('faculty1_entc@gcekarad.ac.in', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'faculty', TRUE, TRUE),
('faculty2_entc@gcekarad.ac.in', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'faculty', TRUE, TRUE),
('faculty1_mech@gcekarad.ac.in', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'faculty', TRUE, TRUE),
('faculty2_mech@gcekarad.ac.in', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'faculty', TRUE, TRUE),
('faculty1_civil@gcekarad.ac.in', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'faculty', TRUE, TRUE),
('faculty2_civil@gcekarad.ac.in', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'faculty', TRUE, TRUE),
('faculty1_electrical@gcekarad.ac.in', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'faculty', TRUE, TRUE),
('faculty2_electrical@gcekarad.ac.in', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'faculty', TRUE, TRUE);

-- Insert Faculty details
INSERT INTO faculty (user_id, dept_id, first_name, last_name, phone, designation, joining_date) VALUES
(2, 1, 'Rajesh', 'Kumar', '9876543210', 'Associate Professor', '2018-01-15'),
(3, 1, 'Priya', 'Sharma', '9876543211', 'Assistant Professor', '2019-03-20'),
(4, 2, 'Amit', 'Patel', '9876543212', 'Associate Professor', '2017-07-10'),
(5, 2, 'Sneha', 'Desai', '9876543213', 'Assistant Professor', '2020-01-05'),
(6, 3, 'Vikram', 'Singh', '9876543214', 'Associate Professor', '2016-11-30'),
(7, 3, 'Neha', 'Gupta', '9876543215', 'Assistant Professor', '2019-08-15'),
(8, 4, 'Arun', 'Verma', '9876543216', 'Associate Professor', '2017-04-25'),
(9, 4, 'Meera', 'Reddy', '9876543217', 'Assistant Professor', '2020-02-10'),
(10, 5, 'Suresh', 'Yadav', '9876543218', 'Associate Professor', '2018-09-01'),
(11, 5, 'Anjali', 'Mehta', '9876543219', 'Assistant Professor', '2019-06-20');

-- Create a procedure to generate sample student data
DELIMITER //
CREATE PROCEDURE generate_sample_students()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE dept_count INT DEFAULT 5;
    DECLARE current_dept INT;
    DECLARE roll_prefix VARCHAR(10);
    DECLARE user_id_start INT;
    
    -- Get the next user_id
    SELECT COALESCE(MAX(user_id), 11) + 1 INTO user_id_start FROM users;
    
    -- Generate 100 students (20 per department)
    WHILE i <= 100 DO
        -- Calculate current department (1 to 5)
        SET current_dept = ((i - 1) % dept_count) + 1;
        
        -- Set roll number prefix based on department
        CASE current_dept
            WHEN 1 THEN SET roll_prefix = 'IT';
            WHEN 2 THEN SET roll_prefix = 'EN';
            WHEN 3 THEN SET roll_prefix = 'ME';
            WHEN 4 THEN SET roll_prefix = 'CV';
            WHEN 5 THEN SET roll_prefix = 'EE';
        END CASE;
        
        -- Insert user
        INSERT INTO users (email, password_hash, user_type, is_email_verified, is_approved)
        VALUES (
            CONCAT('student', i, '@gcekarad.ac.in'),
            '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
            'student',
            TRUE,
            TRUE
        );
        
        -- Insert student
        INSERT INTO students (
            user_id,
            dept_id,
            roll_number,
            first_name,
            last_name,
            phone,
            cgpa,
            batch_year
        )
        VALUES (
            user_id_start + i - 1,
            current_dept,
            CONCAT(roll_prefix, LPAD(i, 3, '0')),
            CONCAT('Student', i),
            CONCAT('Lastname', i),
            CONCAT('98765', LPAD(i, 5, '0')),
            ROUND(RAND() * (4.00 - 6.00) + 6.00, 2),
            2024
        );
        
        -- Add random skills for each student
        INSERT INTO student_skills (student_id, skill_id, rating)
        SELECT 
            i,
            skill_id,
            FLOOR(RAND() * 5) + 1
        FROM skills
        WHERE RAND() < 0.3;
        
        -- Add some achievements
        IF RAND() < 0.5 THEN
            INSERT INTO student_achievements (student_id, title, description, achievement_date)
            VALUES (
                i,
                CONCAT('Achievement ', i),
                CONCAT('Description for achievement ', i),
                DATE_SUB(CURRENT_DATE, INTERVAL FLOOR(RAND() * 365) DAY)
            );
        END IF;
        
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;

-- Execute the procedure to generate sample students
CALL generate_sample_students();

-- Drop the procedure as it's no longer needed
DROP PROCEDURE generate_sample_students; 