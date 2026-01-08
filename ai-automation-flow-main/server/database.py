"""Database utilities for custom integrations and execution plans"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from cryptography.fernet import Fernet
import base64

class DatabaseManager:
    def __init__(self):
        self.conn_string = os.environ.get(
            'DATABASE_URL',
            'postgresql://user:password@localhost:5432/automation_platform'
        )
        # Get encryption key from environment or create one
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            # Generate a key if not provided
            key = base64.urlsafe_b64encode(os.urandom(32)).decode()
        self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.conn_string)
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt sensitive values"""
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt sensitive values"""
        return self.cipher.decrypt(encrypted_value.encode()).decode()
    
    # Custom Integrations CRUD
    def create_custom_integration(self, user_id: str, name: str, display_name: str, 
                                 auth_type: str, base_url: str, auth_header: str = "Authorization",
                                 auth_prefix: str = "Bearer", description: str = None,
                                 oauth_config: Dict = None) -> Dict:
        """Create a new custom integration"""
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                INSERT INTO custom_integrations 
                (user_id, name, display_name, auth_type, base_url, auth_header, 
                 auth_prefix, description, oauth_config, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id, user_id, name, display_name, auth_type, base_url, 
                          auth_header, auth_prefix, description, oauth_config, created_at
            """, (user_id, name, display_name, auth_type, base_url, auth_header, 
                  auth_prefix, description, json.dumps(oauth_config or {})))
            
            result = cur.fetchone()
            conn.commit()
            return dict(result) if result else None
        finally:
            cur.close()
            conn.close()
    
    def get_custom_integrations(self, user_id: str) -> List[Dict]:
        """Get all custom integrations for a user"""
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT id, user_id, name, display_name, auth_type, base_url,
                       auth_header, auth_prefix, description, oauth_config, 
                       is_active, created_at, updated_at
                FROM custom_integrations
                WHERE user_id = %s AND is_active = true
                ORDER BY created_at DESC
            """, (user_id,))
            
            results = cur.fetchall()
            return [dict(row) for row in results]
        finally:
            cur.close()
            conn.close()
    
    def get_custom_integration(self, integration_id: str, user_id: str) -> Optional[Dict]:
        """Get a specific custom integration"""
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT id, user_id, name, display_name, auth_type, base_url,
                       auth_header, auth_prefix, description, oauth_config,
                       is_active, created_at, updated_at
                FROM custom_integrations
                WHERE id = %s AND user_id = %s
            """, (integration_id, user_id))
            
            result = cur.fetchone()
            return dict(result) if result else None
        finally:
            cur.close()
            conn.close()
    
    def update_custom_integration(self, integration_id: str, user_id: str, **kwargs) -> Optional[Dict]:
        """Update a custom integration"""
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Build dynamic UPDATE query
            allowed_fields = ['display_name', 'description', 'auth_type', 'base_url', 
                            'auth_header', 'auth_prefix', 'oauth_config', 'is_active']
            update_fields = []
            values = []
            
            for field in allowed_fields:
                if field in kwargs:
                    update_fields.append(f"{field} = %s")
                    value = kwargs[field]
                    if field == 'oauth_config' and isinstance(value, dict):
                        values.append(json.dumps(value))
                    else:
                        values.append(value)
            
            if not update_fields:
                return self.get_custom_integration(integration_id, user_id)
            
            update_fields.append("updated_at = NOW()")
            values.extend([integration_id, user_id])
            
            query = f"""
                UPDATE custom_integrations
                SET {', '.join(update_fields)}
                WHERE id = %s AND user_id = %s
                RETURNING id, user_id, name, display_name, auth_type, base_url,
                          auth_header, auth_prefix, description, oauth_config,
                          is_active, created_at, updated_at
            """
            
            cur.execute(query, values)
            result = cur.fetchone()
            conn.commit()
            return dict(result) if result else None
        finally:
            cur.close()
            conn.close()
    
    def delete_custom_integration(self, integration_id: str, user_id: str) -> bool:
        """Delete a custom integration"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                DELETE FROM custom_integrations
                WHERE id = %s AND user_id = %s
            """, (integration_id, user_id))
            
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()
    
    # Custom Integration Actions CRUD
    def create_integration_action(self, integration_id: str, action_id: str, action_name: str,
                                 http_method: str, endpoint: str, description: str = None,
                                 parameters: List = None) -> Dict:
        """Create an action for a custom integration"""
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                INSERT INTO custom_integration_actions
                (integration_id, action_id, action_name, http_method, endpoint, 
                 description, parameters, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id, integration_id, action_id, action_name, http_method,
                          endpoint, description, parameters, created_at, updated_at
            """, (integration_id, action_id, action_name, http_method, endpoint,
                  description, json.dumps(parameters or [])))
            
            result = cur.fetchone()
            conn.commit()
            return dict(result) if result else None
        finally:
            cur.close()
            conn.close()
    
    def get_integration_actions(self, integration_id: str) -> List[Dict]:
        """Get all actions for an integration"""
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT id, integration_id, action_id, action_name, http_method,
                       endpoint, description, parameters, created_at, updated_at
                FROM custom_integration_actions
                WHERE integration_id = %s
                ORDER BY created_at ASC
            """, (integration_id,))
            
            results = cur.fetchall()
            return [dict(row) for row in results]
        finally:
            cur.close()
            conn.close()
    
    def delete_integration_action(self, action_id: str, integration_id: str) -> bool:
        """Delete an action from an integration"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                DELETE FROM custom_integration_actions
                WHERE id = %s AND integration_id = %s
            """, (action_id, integration_id))
            
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()
    
    # Credentials CRUD
    def store_credential(self, user_id: str, integration_id: str, credential_type: str, 
                        value: str, expires_at: datetime = None) -> Dict:
        """Store encrypted credentials"""
        encrypted_value = self.encrypt_value(value)
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                INSERT INTO custom_integration_credentials
                (user_id, integration_id, credential_type, encrypted_value, 
                 token_expires_at, is_valid, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, true, NOW(), NOW())
                ON CONFLICT (user_id, integration_id, credential_type)
                DO UPDATE SET encrypted_value = %s, token_expires_at = %s,
                              is_valid = true, updated_at = NOW()
                RETURNING id, user_id, integration_id, credential_type, token_expires_at, is_valid
            """, (user_id, integration_id, credential_type, encrypted_value, 
                  expires_at, encrypted_value, expires_at))
            
            result = cur.fetchone()
            conn.commit()
            return dict(result) if result else None
        finally:
            cur.close()
            conn.close()
    
    def get_credential(self, user_id: str, integration_id: str, credential_type: str) -> Optional[str]:
        """Get and decrypt a credential"""
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT encrypted_value, is_valid, token_expires_at
                FROM custom_integration_credentials
                WHERE user_id = %s AND integration_id = %s AND credential_type = %s
            """, (user_id, integration_id, credential_type))
            
            result = cur.fetchone()
            if not result:
                return None
            
            # Check if token is expired
            if result['token_expires_at'] and result['token_expires_at'] < datetime.now(result['token_expires_at'].tzinfo):
                return None
            
            if result['is_valid']:
                return self.decrypt_value(result['encrypted_value'])
            return None
        finally:
            cur.close()
            conn.close()
    
    def invalidate_credential(self, user_id: str, integration_id: str, credential_type: str) -> bool:
        """Mark a credential as invalid"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                UPDATE custom_integration_credentials
                SET is_valid = false, updated_at = NOW()
                WHERE user_id = %s AND integration_id = %s AND credential_type = %s
            """, (user_id, integration_id, credential_type))
            
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()
    
    def store_learning(self, user_id: str, workflow_id: str, learning: Dict[str, Any], 
                      feedback: str = "", rating: int = 0) -> bool:
        """
        Store learning insights from workflow execution.
        This helps improve future workflow generation for similar requests.
        """
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            # Create learning_history table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS learning_history (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    workflow_id VARCHAR(255) NOT NULL,
                    learning_data JSONB NOT NULL,
                    feedback TEXT,
                    rating INT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            cur.execute("""
                INSERT INTO learning_history 
                (user_id, workflow_id, learning_data, feedback, rating)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, workflow_id, json.dumps(learning), feedback, rating))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error storing learning: {e}")
            return False
        finally:
            cur.close()
            conn.close()


# Global instance
db_manager = DatabaseManager()
