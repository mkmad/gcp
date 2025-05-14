-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    environment VARCHAR(50) NOT NULL
);

-- Create roles table
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT
);

-- Create user_roles table
CREATE TABLE user_roles (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(id),
    environment VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_email, role_id, environment)
);

-- Create resources table
CREATE TABLE resources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    environment VARCHAR(50) NOT NULL,
    sensitive_data BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on email and environment
CREATE INDEX idx_users_email_env ON users(email, environment);
CREATE INDEX idx_user_roles_env ON user_roles(environment);
CREATE INDEX idx_resources_env ON resources(environment);

-- Insert default roles
INSERT INTO roles (name, description) VALUES
    ('admin', 'Full access to all resources'),
    ('editor', 'Can view and edit resources'),
    ('viewer', 'Can only view resources');

-- Clear existing resources
TRUNCATE resources CASCADE;

-- Insert sample resources with clear role-based visibility
INSERT INTO resources (name, description, environment, sensitive_data) VALUES
    -- Sensitive Data (Admin Only)
    ('Customer PII Data', 'Personal identifiable information of customers', 'dev', true),
    ('Financial Reports', 'Company financial statements and forecasts', 'dev', true),
    ('Employee Records', 'HR data and employee personal information', 'dev', true),
    
    -- Mixed Sensitivity (Admin + Editor)
    ('Analytics Dashboard', 'Business metrics and KPIs', 'dev', true),
    ('Sales Pipeline', 'Current sales opportunities and forecasts', 'dev', true),
    
    -- Non-Sensitive (All Roles)
    ('Public Blog Posts', 'Company blog content', 'dev', false),
    ('Product Catalog', 'List of available products', 'dev', false),
    ('Company News', 'Public company announcements', 'dev', false),
    ('Help Documentation', 'Public product documentation', 'dev', false);

-- Add the same resources for staging environment
INSERT INTO resources (name, description, environment, sensitive_data)
SELECT 
    name,
    description,
    'staging' as environment,
    sensitive_data
FROM resources WHERE environment = 'dev';

-- Function to add user role
CREATE OR REPLACE FUNCTION add_user_role(
    p_email VARCHAR(255),
    p_role_name VARCHAR(50),
    p_environment VARCHAR(50)
) RETURNS void AS $$
BEGIN
    -- First ensure the user exists
    INSERT INTO users (email, environment)
    VALUES (p_email, p_environment)
    ON CONFLICT (email) DO NOTHING;

    -- Then add the role
    INSERT INTO user_roles (user_email, role_id, environment)
    SELECT p_email, r.id, p_environment
    FROM roles r
    WHERE r.name = p_role_name
    ON CONFLICT (user_email, role_id, environment) DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- Optional: Row-level permissions for future extensibility
CREATE TABLE IF NOT EXISTS row_permissions (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    resource_id INTEGER REFERENCES resources(id),
    can_view BOOLEAN DEFAULT false,
    can_edit BOOLEAN DEFAULT false,
    environment VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_email, resource_id, environment)
);

-- MIGRATION NOTE: If you want to use row-level permissions, join this table in your backend queries. 


-- Assign 'admin' role to your user in 'dev' environment
SELECT add_user_role('mohan@mkmad.com', 'admin', 'dev');

-- Assign 'viewer' role to your user in 'dev' environment
SELECT add_user_role('kiruthika@mkmad.com', 'viewer', 'dev');
