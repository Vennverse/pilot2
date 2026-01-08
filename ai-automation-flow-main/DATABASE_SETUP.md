# Database Setup Guide - Global Connector

This guide walks you through setting up PostgreSQL for the global custom integration connector system.

## Prerequisites

- PostgreSQL 12+ installed
- Python 3.9+
- pip packages: `psycopg2-binary`, `cryptography`

## Step 1: Create Database and User

```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create database
CREATE DATABASE automation_platform;

-- Create user
CREATE USER automation_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
ALTER ROLE automation_user SET client_encoding TO 'utf8';
ALTER ROLE automation_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE automation_user SET default_transaction_deferrable TO on;
ALTER ROLE automation_user SET timezone TO 'UTC';

GRANT ALL PRIVILEGES ON DATABASE automation_platform TO automation_user;

-- Connect to the new database
\c automation_platform

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO automation_user;
```

## Step 2: Configure Environment Variables

Create a `.env` file in the `server/` directory:

```bash
DATABASE_URL=postgresql://automation_user:your_secure_password@localhost:5432/automation_platform

# Generate encryption key:
# python -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
ENCRYPTION_KEY=<generated_key_here>

# API Keys
AI_INTEGRATIONS_OPENAI_API_KEY=sk-...
AI_INTEGRATIONS_OPENAI_BASE_URL=https://api.openai.com/v1
```

## Step 3: Install Dependencies

```bash
cd server
pip install -r requirements.txt
```

## Step 4: Initialize Database Schema

```bash
cd server
python setup_db.py
```

This will:
- Create `custom_integrations` table
- Create `custom_integration_actions` table
- Create `custom_integration_credentials` table
- Set up indexes for performance
- Enable Row Level Security (RLS) policies
- Restrict access so users can only see their own data

## Step 5: Verify Setup

```bash
psql -U automation_user -d automation_platform -c "\dt"
```

You should see:
```
custom_integrations
custom_integration_actions
custom_integration_credentials
```

## Features

### 1. **Full CRUD Operations**
- Create custom integrations with OAuth or API key auth
- Define custom actions (endpoints) per integration
- Store encrypted credentials securely
- Update/delete integrations

### 2. **Database Security**
- All credentials encrypted with Fernet (AES-128)
- Row Level Security (RLS) ensures users see only their own data
- Encryption key stored in environment variables
- Token expiration support

### 3. **API Endpoints**

#### Get/Create Custom Integrations
```
GET  /api/custom-integrations?user_id=<user_id>
POST /api/custom-integrations?user_id=<user_id>
```

#### Get/Update/Delete Specific Integration
```
GET    /api/custom-integrations/<integration_id>?user_id=<user_id>
PUT    /api/custom-integrations/<integration_id>?user_id=<user_id>
DELETE /api/custom-integrations/<integration_id>?user_id=<user_id>
```

#### Store Credentials
```
POST /api/custom-integrations/<integration_id>/credentials?user_id=<user_id>
```

#### Test Integration
```
POST /api/custom-integrations/<integration_id>/test?user_id=<user_id>
```

### 4. **Frontend Changes**
- All custom integrations now load from database
- localStorage no longer used for integrations
- Real-time sync with backend
- Encrypted credential storage

## Usage Examples

### Create Custom Integration

```javascript
const response = await fetch('/api/custom-integrations?user_id=<user_id>', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'my_api',
    display_name: 'My Custom API',
    auth_type: 'api_key',
    oauth_config: {
      base_url: 'https://api.example.com',
      auth_header: 'Authorization',
      auth_prefix: 'Bearer'
    },
    actions: [
      {
        id: 'list_items',
        name: 'List Items',
        method: 'GET',
        endpoint: '/v1/items'
      }
    ]
  })
});
```

### Store Credentials

```javascript
await fetch(`/api/custom-integrations/<integration_id>/credentials?user_id=<user_id>`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    type: 'api_key',
    value: 'secret_api_key_here'
  })
});
```

### Test Integration

```javascript
const response = await fetch(`/api/custom-integrations/<integration_id>/test?user_id=<user_id>`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    endpoint: '/v1/items',
    method: 'GET',
    body: {}
  })
});
```

## Database Schema

### custom_integrations
- `id`: UUID (primary key)
- `user_id`: UUID (user who created it)
- `name`: VARCHAR (unique per user)
- `display_name`: VARCHAR
- `description`: TEXT
- `auth_type`: 'api_key' | 'oauth'
- `base_url`: VARCHAR
- `auth_header`: VARCHAR (e.g., 'Authorization')
- `auth_prefix`: VARCHAR (e.g., 'Bearer')
- `oauth_config`: JSONB
- `is_active`: BOOLEAN
- `created_at`, `updated_at`: TIMESTAMPS

### custom_integration_actions
- `id`: UUID (primary key)
- `integration_id`: UUID (foreign key)
- `action_id`: VARCHAR
- `action_name`: VARCHAR
- `http_method`: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
- `endpoint`: VARCHAR
- `parameters`: JSONB (array of param names)
- `created_at`, `updated_at`: TIMESTAMPS

### custom_integration_credentials
- `id`: UUID (primary key)
- `user_id`: UUID
- `integration_id`: UUID (foreign key)
- `credential_type`: 'api_key' | 'oauth_token' | 'oauth_refresh_token'
- `encrypted_value`: TEXT (encrypted)
- `token_expires_at`: TIMESTAMP
- `is_valid`: BOOLEAN
- `last_validated_at`: TIMESTAMP
- `created_at`, `updated_at`: TIMESTAMPS

## Troubleshooting

### "Database connection failed"
- Check `DATABASE_URL` in `.env`
- Verify PostgreSQL is running: `pg_isready -d automation_platform`

### "Encryption key invalid"
- Regenerate key: `python -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"`
- Update `.env` file

### "Permission denied"
- Verify user has privileges: `GRANT ALL PRIVILEGES ON DATABASE automation_platform TO automation_user;`

### "RLS policy restricts access"
- This is expected. RLS ensures users can only access their own data
- Each query automatically filters by `auth.uid()` (from Supabase Auth)

## Next Steps

1. ✅ Database schema created
2. ✅ API endpoints implemented
3. ✅ Frontend migrated to database
4. ⏭ Add execution plan persistence
5. ⏭ Add execution logs persistence
6. ⏭ Add caching layer for better performance
7. ⏭ Add audit logging
