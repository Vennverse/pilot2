#!/usr/bin/env python3
"""
Validation script for AI Automation Flow v2.0 refactoring
Checks that all required files exist and have correct structure
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and is not empty"""
    path = Path(filepath)
    if path.exists() and path.stat().st_size > 0:
        size = path.stat().st_size
        print(f"✅ {description}: {filepath} ({size:,} bytes)")
        return True
    else:
        print(f"❌ {description}: MISSING or EMPTY - {filepath}")
        return False

def check_file_contains(filepath, search_text, description):
    """Check if a file contains specific text"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if search_text in content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description}: Text not found")
                return False
    except Exception as e:
        print(f"❌ {description}: Error reading file - {e}")
        return False

def main():
    print("=" * 70)
    print("AI AUTOMATION FLOW v2.0 - REFACTORING VALIDATION")
    print("=" * 70)
    print()
    
    server_dir = Path(__file__).parent
    os.chdir(server_dir)
    
    checks_passed = 0
    checks_total = 0
    
    # ============= CORE APPLICATION FILES =============
    print("📋 CORE APPLICATION FILES")
    print("-" * 70)
    
    files_to_check = [
        ("app.py", "Main Flask application (refactored)"),
        ("app_OLD_MONOLITHIC_BACKUP.py", "Backup of old monolithic app.py"),
        ("execution_engine.py", "Execution engine with provider registry"),
        ("scheduler.py", "APScheduler integration"),
        ("provider_registry.py", "Provider registry system"),
        ("database.py", "Database manager"),
        ("database_manager.py", "Database manager alias"),
    ]
    
    for filename, description in files_to_check:
        checks_total += 1
        if check_file_exists(filename, description):
            checks_passed += 1
    
    print()
    
    # ============= PROVIDER FILES =============
    print("📋 PROVIDER FILES")
    print("-" * 70)
    
    provider_files = [
        ("providers/__init__.py", "Provider auto-loader"),
        ("providers/ai.py", "AI providers (OpenAI, Groq, etc.)"),
        ("providers/http.py", "HTTP providers (webhooks, custom APIs)"),
    ]
    
    for filename, description in provider_files:
        checks_total += 1
        if check_file_exists(filename, description):
            checks_passed += 1
    
    print()
    
    # ============= MIGRATION FILES =============
    print("📋 MIGRATION & DOCUMENTATION")
    print("-" * 70)
    
    doc_files = [
        ("migrations/002_provider_credentials_and_logs.sql", "Database migration"),
        ("requirements.txt", "Python dependencies"),
        ("setup_db.py", "Database setup script"),
    ]
    
    for filename, description in doc_files:
        checks_total += 1
        if check_file_exists(filename, description):
            checks_passed += 1
    
    print()
    
    # ============= CODE STRUCTURE VALIDATION =============
    print("📋 CODE STRUCTURE VALIDATION")
    print("-" * 70)
    
    structure_checks = [
        ("app.py", "from execution_engine import execute_step, execute_plan", 
         "app.py imports execution_engine"),
        ("app.py", "from scheduler import init_scheduler", 
         "app.py imports scheduler"),
        ("app.py", "from provider_registry import registry", 
         "app.py imports registry"),
        ("app.py", "from database_manager import DatabaseManager", 
         "app.py imports DatabaseManager"),
        ("app.py", "def initialize_app():", 
         "app.py has initialize_app hook"),
        ("app.py", "@app.before_request", 
         "app.py has before_request decorator"),
        ("execution_engine.py", "def execute_step(", 
         "execution_engine.py has execute_step function"),
        ("execution_engine.py", "def execute_plan(", 
         "execution_engine.py has execute_plan function"),
        ("scheduler.py", "def init_scheduler(app):", 
         "scheduler.py has init_scheduler function"),
        ("scheduler.py", "scheduler.start()", 
         "scheduler.py calls scheduler.start()"),
        ("provider_registry.py", "class ProviderRegistry:", 
         "provider_registry.py has ProviderRegistry class"),
        ("provider_registry.py", "class ProviderResult:", 
         "provider_registry.py has ProviderResult dataclass"),
    ]
    
    for filepath, search_text, description in structure_checks:
        checks_total += 1
        if check_file_contains(filepath, search_text, description):
            checks_passed += 1
    
    print()
    
    # ============= SUMMARY =============
    print("=" * 70)
    print(f"VALIDATION RESULTS: {checks_passed}/{checks_total} checks passed")
    print("=" * 70)
    
    if checks_passed == checks_total:
        print()
        print("🎉 ALL CHECKS PASSED! Refactoring is complete and validated.")
        print()
        print("Next steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Setup database: python setup_db.py")
        print("  3. Start server: python app.py")
        print("  4. Test health: curl http://localhost:5001/api/health")
        print()
        return 0
    else:
        print()
        print(f"⚠️  {checks_total - checks_passed} checks failed. Please review above.")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
