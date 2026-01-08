"""Extended database methods for execution plans and per-user credentials"""

# Add these methods to DatabaseManager class in database.py

def get_provider_credentials(self, user_id: str, provider: str) -> Dict[str, str]:
    """Get all stored credentials for a provider for a user"""
    conn = self.get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Try custom integration credentials first
        cur.execute("""
            SELECT credential_type, encrypted_value
            FROM custom_integration_credentials
            WHERE user_id = %s AND integration_id IN (
                SELECT id FROM custom_integrations 
                WHERE name = %s
            )
        """, (user_id, provider))
        
        credentials = {}
        for row in cur.fetchall():
            cred_type = row['credential_type']
            decrypted = self.decrypt_value(row['encrypted_value'])
            credentials[cred_type] = decrypted
        
        return credentials
    finally:
        cur.close()
        conn.close()


def store_provider_credential(self, user_id: str, provider: str, credential_type: str,
                              value: str, expires_at=None) -> bool:
    """Store encrypted credential for a provider"""
    encrypted = self.encrypt_value(value)
    conn = self.get_connection()
    cur = conn.cursor()
    
    try:
        # For built-in providers, store in a simple table
        cur.execute("""
            INSERT INTO provider_credentials (user_id, provider, type, encrypted_value, expires_at, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (user_id, provider, type)
            DO UPDATE SET encrypted_value = %s, expires_at = %s, updated_at = NOW()
        """, (user_id, provider, credential_type, encrypted, expires_at, encrypted, expires_at))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def create_execution_log(self, plan_id: str, user_id: str, plan_name: str,
                         step_number: int, provider: str, action: str,
                         status: str, message: str, latency_ms: int = 0,
                         output_preview: str = None, error: str = None) -> str:
    """Create a structured execution log entry"""
    conn = self.get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            INSERT INTO execution_logs 
            (plan_id, user_id, plan_name, step_number, provider, action, 
             status, message, latency_ms, output_preview, error, timestamp, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id
        """, (plan_id, user_id, plan_name, step_number, provider, action, 
              status, message, latency_ms, output_preview, error))
        
        result = cur.fetchone()
        conn.commit()
        return str(result['id']) if result else None
    finally:
        cur.close()
        conn.close()


def save_execution_plan(self, user_id: str, name: str, original_prompt: str,
                       plan_json: list, plain_english_steps: list,
                       required_providers: list, trigger: dict = None) -> Dict:
    """Save an execution plan to database"""
    conn = self.get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            INSERT INTO execution_plans 
            (user_id, name, original_prompt, plan_json, plain_english_steps, 
             required_providers, trigger, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'draft', NOW(), NOW())
            RETURNING id, created_at, updated_at
        """, (user_id, name, original_prompt, json.dumps(plan_json), 
              json.dumps(plain_english_steps), json.dumps(required_providers),
              json.dumps(trigger or {})))
        
        result = cur.fetchone()
        conn.commit()
        return dict(result) if result else None
    finally:
        cur.close()
        conn.close()


def get_user_execution_plans(self, user_id: str, limit: int = 50) -> List[Dict]:
    """Get user's execution plans"""
    conn = self.get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT id, user_id, name, original_prompt, plan_json, plain_english_steps,
                   required_providers, status, created_at, updated_at
            FROM execution_plans
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user_id, limit))
        
        results = cur.fetchall()
        return [dict(row) for row in results]
    finally:
        cur.close()
        conn.close()


def get_execution_logs(self, plan_id: str, user_id: str, limit: int = 100) -> List[Dict]:
    """Get logs for an execution plan"""
    conn = self.get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT id, plan_id, step_number, provider, action, status, message,
                   latency_ms, output_preview, error, timestamp, created_at
            FROM execution_logs
            WHERE plan_id = %s AND user_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (plan_id, user_id, limit))
        
        results = cur.fetchall()
        return [dict(row) for row in results]
    finally:
        cur.close()
        conn.close()
