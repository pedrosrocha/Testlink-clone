
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    username VARCHAR(50) NOT NULL UNIQUE, 
    email VARCHAR(100) NOT NULL,          
    password_hash VARCHAR(255) NOT NULL,  -- saves only the hash, not the plain tect password
    date_created DATETIME DEFAULT CURRENT_TIMESTAMP, -- The date when the user was created
    user_level ENUM('admin', 'editor', 'viewer') DEFAULT 'viewer', -- The 3 possible levels of this app.
    is_active BOOLEAN DEFAULT TRUE,     -- defines whether a user is active or not
    last_login DATETIME DEFAULT NULL    -- date of the last login
);

INSERT INTO users (username, email, password_hash, user_level)
VALUES (
  'admin user',
  'admin@example.com',
  '$2a$12$9x4DXl6yGWktDa855AQE7OUXKYW1/79u6D6IAQtd9wHhUeMg5ONXu',
  'admin'
);

CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,

    name VARCHAR(100) NOT NULL UNIQUE,              -- Name of the project
    description TEXT,                               -- Optional longer description
    status ENUM('active', 'inactive', 'archived') DEFAULT 'active',  -- Status of project

    owner_name VARCHAR(100) NOT NULL,               -- Optional link to user who owns the project
    start_date DATE,                                -- When the project started
    end_date DATE,                                  -- Optional planned end date

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,             -- Timestamp for creation
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,  -- Auto update on modification
    updated_by VARCHAR(100) NOT NULL  -- The last person to update the database info
);

CREATE TABLE IF NOT EXISTS test_suites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,  -- Foreign key to the project
    parent_suite_id INT DEFAULT NULL,  -- For nested suites
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(100) NOT NULL,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_suite_id) REFERENCES test_suites(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS test_cases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    suite_id INT NOT NULL,  -- Foreign key to test_suites
    name VARCHAR(100) NOT NULL,
    description TEXT,
    preconditions TEXT,
    expected_result TEXT,
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
    status ENUM('draft', 'final', 'deprecated') DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR (100) NOT NULL,
    last_updated_by VARCHAR (100) NOT NULL,
    current_version INT NOT NULL DEFAULT 1,
    versions VARCHAR (100) NOT NULL DEFAULT '1',

    FOREIGN KEY (suite_id) REFERENCES test_suites(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS  test_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_case_version_id INT NOT NULL,  -- FK to the test_case_versions table
    step_position INT NOT NULL,         -- Defines the order of the steps
    step_action TEXT NOT NULL,          -- What the tester should do
    expected_value TEXT NOT NULL,       -- What should happen as a result
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INT default 1,

    FOREIGN KEY (test_case_version_id) REFERENCES test_cases(id) ON DELETE CASCADE
);

CREATE INDEX idx_test_suites_project_id ON test_suites(project_id);
CREATE INDEX idx_test_suites_parent_suite_id ON test_suites(parent_suite_id);
CREATE INDEX idx_test_cases_suite_id ON test_cases(suite_id);
CREATE INDEX idx_test_steps_case_version_id ON test_steps(test_case_version_id);
CREATE INDEX idx_test_steps_step_position ON test_steps(step_position);
