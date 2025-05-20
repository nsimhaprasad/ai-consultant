-- Migration to add tenants and associate users and API keys with tenants

-- Create UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tenants table
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add tenant_id to users table
ALTER TABLE users ADD COLUMN tenant_id UUID REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);

-- Add tenant_id to api_keys table
ALTER TABLE api_keys ADD COLUMN tenant_id UUID REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant_id ON api_keys(tenant_id);

-- Create a default tenant for existing data
INSERT INTO tenants (name, slug) VALUES ('Default Tenant', 'default');

-- Update existing users and api_keys to use the default tenant
UPDATE users SET tenant_id = (SELECT id FROM tenants WHERE slug = 'default');
UPDATE api_keys SET tenant_id = (SELECT id FROM tenants WHERE slug = 'default');

-- Make tenant_id NOT NULL after migrating existing data
ALTER TABLE users ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE api_keys ALTER COLUMN tenant_id SET NOT NULL;
