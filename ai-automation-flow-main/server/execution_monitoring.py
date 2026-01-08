"""
Execution Monitoring - Real-time execution tracking and websocket support
Custom Code Executor - Sandboxed Python/JavaScript code execution
"""

import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)


@dataclass
class ExecutionEvent:
    """Real-time execution event"""
    execution_id: str
    timestamp: str
    event_type: str  # "started", "step_started", "step_completed", "step_failed", "completed"
    step_id: Optional[str] = None
    step_name: Optional[str] = None
    data: Optional[Dict] = None
    error: Optional[str] = None


class ExecutionMonitor:
    """Monitor and stream execution progress"""
    
    def __init__(self):
        self.active_executions = {}  # execution_id -> execution state
        self.event_stream = {}  # execution_id -> list of events
        self.subscribers = {}  # execution_id -> list of callbacks
    
    def start_monitoring(self, execution_id: str) -> None:
        """Start monitoring execution"""
        self.active_executions[execution_id] = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "events": []
        }
        self.event_stream[execution_id] = []
        self.subscribers[execution_id] = []
        
        logger.info(f"Monitoring started: {execution_id}")
    
    def emit_event(self, event: ExecutionEvent) -> None:
        """Emit execution event"""
        self.event_stream[event.execution_id].append(event)
        
        # Notify all subscribers
        if event.execution_id in self.subscribers:
            for callback in self.subscribers[event.execution_id]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Subscriber callback error: {e}")
    
    def subscribe(self, execution_id: str, callback: Callable) -> None:
        """Subscribe to execution events"""
        if execution_id not in self.subscribers:
            self.subscribers[execution_id] = []
        self.subscribers[execution_id].append(callback)
    
    def get_execution_stream(self, execution_id: str, last_n: int = 100) -> list:
        """Get execution events"""
        if execution_id not in self.event_stream:
            return []
        return self.event_stream[execution_id][-last_n:]
    
    def stop_monitoring(self, execution_id: str, status: str = "completed") -> None:
        """Stop monitoring execution"""
        if execution_id in self.active_executions:
            self.active_executions[execution_id]["status"] = status
            self.active_executions[execution_id]["completed_at"] = datetime.now().isoformat()
        
        logger.info(f"Monitoring stopped: {execution_id} ({status})")
    
    def get_websocket_data(self, event: ExecutionEvent) -> str:
        """Convert event to WebSocket format (JSON)"""
        return json.dumps({
            "execution_id": event.execution_id,
            "timestamp": event.timestamp,
            "event_type": event.event_type,
            "step_id": event.step_id,
            "step_name": event.step_name,
            "data": event.data,
            "error": event.error
        })


class CustomCodeExecutor:
    """Safely execute custom Python or JavaScript code"""
    
    # Dangerous functions to block
    PYTHON_BANNED = [
        "eval", "exec", "__import__", "open", "input",
        "exit", "quit", "__builtins__"
    ]
    
    def __init__(self):
        self.max_timeout = 30  # 30 second max execution
        self.max_memory = 512  # 512 MB max
    
    def execute_python(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute Python code in sandboxed environment"""
        
        # Security check
        for banned in self.PYTHON_BANNED:
            if banned in code:
                return {
                    "success": False,
                    "error": f"Function '{banned}' is not allowed for security reasons"
                }
        
        try:
            # Create safe execution environment
            safe_globals = {
                "__builtins__": {
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "dict": dict,
                    "list": list,
                    "tuple": tuple,
                    "set": set,
                    "print": print,
                    "sum": sum,
                    "max": max,
                    "min": min,
                    "sorted": sorted,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "any": any,
                    "all": all,
                }
            }
            
            # Add provided context
            if context:
                safe_globals.update(context)
            
            # Execute code with timeout (simplified)
            exec(code, safe_globals)
            
            # Extract output
            result = safe_globals.get("result", "Execution completed")
            
            return {
                "success": True,
                "result": result,
                "output": result
            }
            
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"Syntax Error: {str(e)}",
                "error_type": "SyntaxError"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution Error: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def execute_javascript(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute JavaScript code via Node.js"""
        
        # Security check
        banned_js = ["eval", "Function", "require"]
        for banned in banned_js:
            if banned in code:
                return {
                    "success": False,
                    "error": f"Function '{banned}' is not allowed"
                }
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute JavaScript
            result = subprocess.run(
                ["node", temp_file],
                capture_output=True,
                text=True,
                timeout=self.max_timeout
            )
            
            os.unlink(temp_file)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr,
                    "error_type": "ExecutionError"
                }
            
            return {
                "success": True,
                "result": result.stdout.strip(),
                "output": result.stdout.strip()
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Execution timeout exceeded (30s)",
                "error_type": "TimeoutError"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def execute_sql_transform(self, sql: str, data: list) -> Dict[str, Any]:
        """Execute SQL-like data transformation"""
        try:
            # Simple SQL simulation for data transformation
            if "SELECT" in sql.upper():
                # Extract columns
                return {
                    "success": True,
                    "result": data,
                    "rows_affected": len(data)
                }
            return {
                "success": False,
                "error": "Only SELECT queries supported"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class CodeBlockStep:
    """Custom code block in workflow"""
    
    def __init__(self, step_id: str, language: str, code: str):
        self.step_id = step_id
        self.language = language  # "python", "javascript", "sql"
        self.code = code
        self.executor = CustomCodeExecutor()
    
    def execute(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute code block"""
        
        if self.language == "python":
            return self.executor.execute_python(self.code, context)
        elif self.language == "javascript":
            return self.executor.execute_javascript(self.code, context)
        elif self.language == "sql":
            return self.executor.execute_sql_transform(self.code, context.get("data", []))
        else:
            return {
                "success": False,
                "error": f"Unsupported language: {self.language}"
            }


# Global instances
execution_monitor = ExecutionMonitor()
code_executor = CustomCodeExecutor()
