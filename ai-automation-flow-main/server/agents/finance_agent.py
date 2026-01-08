"""
Finance Agent - Specialized for financial automation and accounting
Handles expense tracking, invoicing, financial reporting, and integration with accounting software
"""

from agents.base_agent import BaseAgent, AgentTool, AgentResponse
from agents.registry import register_agent
from typing import Dict, Any, List


@register_agent("finance")
class FinanceAgent(BaseAgent):
    """
    Finance-focused agent for accounting, invoicing, and financial operations.
    Generates workflows for expense tracking, reporting, and financial processes.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="Finance Agent",
            description="Automates accounting, invoicing, expense tracking, financial reporting, and compliance"
        )
        self._init_tools()
    
    def _init_tools(self):
        """Initialize tools available to finance agent"""
        self.tools = [
            AgentTool(
                name="create_invoice",
                provider="stripe",
                description="Create and send invoices",
                parameters={"customer": "str", "amount": "float", "items": "list"},
                output_schema={"invoice_id": "str"}
            ),
            AgentTool(
                name="track_expense",
                provider="quickbooks",
                description="Log and categorize business expenses",
                parameters={"category": "str", "amount": "float", "date": "str"},
                output_schema={"expense_id": "str"}
            ),
            AgentTool(
                name="generate_report",
                provider="quickbooks",
                description="Generate financial reports (P&L, balance sheet, etc)",
                parameters={"report_type": "str", "period": "str"},
                output_schema={"report": "dict"}
            ),
            AgentTool(
                name="reconcile_accounts",
                provider="stripe",
                description="Reconcile payment and bank accounts",
                parameters={"account": "str", "start_date": "str", "end_date": "str"},
                output_schema={"reconciled": "bool", "discrepancies": "list"}
            ),
            AgentTool(
                name="send_payment_reminder",
                provider="sendgrid",
                description="Send payment reminders and dunning notices",
                parameters={"invoices": "list", "template": "str"},
                output_schema={"sent": "int"}
            ),
            AgentTool(
                name="calculate_taxes",
                provider="quickbooks",
                description="Calculate estimated taxes and prepare tax reports",
                parameters={"period": "str", "jurisdiction": "str"},
                output_schema={"tax_amount": "float", "report": "dict"}
            ),
        ]
    
    def get_system_prompt(self) -> str:
        """Get specialized finance agent prompt"""
        return """You are a Finance Agent specializing in accounting, invoicing, and financial operations.
Your expertise:
- Invoice creation and payment tracking
- Expense categorization and tracking
- Financial reporting (P&L, balance sheet, cash flow)
- Account reconciliation
- Tax calculation and compliance
- Payment reminders and collections

When given a finance task:
1. Understand the financial process (invoicing, reporting, reconciliation, etc)
2. Identify required data sources
3. Break into workflow steps
4. Use available tools to create financial automation workflows

Example workflows you can generate:
- Invoicing: Create invoice → Send via email → Track payment → Send reminder if unpaid
- Expense tracking: Categorize expense → Log to QuickBooks → Update budget → Generate report
- Financial reporting: Reconcile accounts → Generate P&L → Calculate taxes → Send to stakeholders
- Collections: Identify unpaid invoices → Send dunning notices → Track responses

Always ensure accuracy and compliance with tax regulations."""
    
    def get_tools(self) -> List[AgentTool]:
        """Return available tools"""
        return self.tools
    
    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """Analyze finance request to extract intent and entities"""
        request_lower = user_request.lower()
        
        analysis = {
            "raw_request": user_request,
            "intent": None,
            "entities": {
                "accounts": [],
                "periods": [],
                "amounts": []
            },
            "workflow_type": None
        }
        
        # Intent detection
        if any(word in request_lower for word in ["invoice", "send invoice", "create invoice"]):
            analysis["intent"] = "invoicing"
            analysis["workflow_type"] = "invoicing"
        elif any(word in request_lower for word in ["expense", "cost", "spend", "track"]):
            analysis["intent"] = "expense_tracking"
            analysis["workflow_type"] = "expense_tracking"
        elif any(word in request_lower for word in ["report", "p&l", "balance sheet", "financial"]):
            analysis["intent"] = "reporting"
            analysis["workflow_type"] = "reporting"
        elif any(word in request_lower for word in ["reconcil", "match", "balance"]):
            analysis["intent"] = "reconciliation"
            analysis["workflow_type"] = "reconciliation"
        elif any(word in request_lower for word in ["payment", "collect", "remind", "follow"]):
            analysis["intent"] = "collections"
            analysis["workflow_type"] = "collections"
        elif any(word in request_lower for word in ["tax", "tax report", "tax calculation"]):
            analysis["intent"] = "tax"
            analysis["workflow_type"] = "tax_calculation"
        else:
            analysis["intent"] = "general"
            analysis["workflow_type"] = "invoicing"
        
        return analysis
    
    def generate_plan(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate finance workflow plan"""
        workflow_type = analysis.get("workflow_type", "invoicing")
        
        if workflow_type == "invoicing":
            return self._generate_invoicing_workflow(user_request, analysis)
        elif workflow_type == "expense_tracking":
            return self._generate_expense_workflow(user_request, analysis)
        elif workflow_type == "reporting":
            return self._generate_reporting_workflow(user_request, analysis)
        elif workflow_type == "reconciliation":
            return self._generate_reconciliation_workflow(user_request, analysis)
        elif workflow_type == "collections":
            return self._generate_collections_workflow(user_request, analysis)
        elif workflow_type == "tax_calculation":
            return self._generate_tax_workflow(user_request, analysis)
        else:
            return self._generate_invoicing_workflow(user_request, analysis)
    
    def _generate_invoicing_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate invoicing workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Create invoice",
                provider="stripe",
                action="create_invoice",
                parameters={
                    "customer": "default",
                    "items": user_request,
                    "auto_send": False
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Send invoice to customer",
                provider="sendgrid",
                action="send_invoice",
                parameters={
                    "invoice_id": "step_1",
                    "template": "professional_invoice"
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Log payment terms",
                provider="quickbooks",
                action="log_invoice",
                parameters={
                    "invoice_id": "step_1",
                    "due_days": 30
                },
                depends_on="step_1"
            )
        ]
        
        return self.build_workflow(
            name="Invoice Creation and Sending",
            description=f"Create and send invoice for: {user_request[:100]}",
            steps=steps,
            tags=["finance", "invoicing"],
            metadata={"process_type": "invoicing"}
        )
    
    def _generate_expense_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate expense tracking workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Categorize expense",
                provider="openai",
                action="categorize",
                parameters={
                    "description": user_request,
                    "categories": ["office", "travel", "software", "equipment", "other"]
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Log expense to QuickBooks",
                provider="quickbooks",
                action="create_expense",
                parameters={
                    "category": "step_1",
                    "description": user_request,
                    "date": "today"
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Update budget tracking",
                provider="quickbooks",
                action="update_budget",
                parameters={
                    "category": "step_1",
                    "expense_id": "step_2"
                },
                depends_on="step_2"
            )
        ]
        
        return self.build_workflow(
            name="Expense Tracking Workflow",
            description=f"Log and track expense: {user_request[:100]}",
            steps=steps,
            tags=["finance", "expenses"],
            metadata={"process_type": "expense_tracking"}
        )
    
    def _generate_reporting_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financial reporting workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Reconcile all accounts",
                provider="stripe",
                action="reconcile_accounts",
                parameters={
                    "account": "all",
                    "period": "current_month"
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Generate financial report",
                provider="quickbooks",
                action="generate_report",
                parameters={
                    "report_type": "profit_loss",
                    "period": "current_month"
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Send report to stakeholders",
                provider="sendgrid",
                action="send_report",
                parameters={
                    "report": "step_2",
                    "recipients": "stakeholders",
                    "format": "pdf"
                },
                depends_on="step_2"
            )
        ]
        
        return self.build_workflow(
            name="Financial Reporting Workflow",
            description=f"Generate financial report: {user_request[:100]}",
            steps=steps,
            tags=["finance", "reporting"],
            metadata={"report_type": "comprehensive"}
        )
    
    def _generate_reconciliation_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate account reconciliation workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Reconcile accounts",
                provider="stripe",
                action="reconcile_accounts",
                parameters={
                    "start_date": "month_start",
                    "end_date": "today"
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Identify discrepancies",
                provider="quickbooks",
                action="identify_discrepancies",
                parameters={
                    "reconciliation": "step_1"
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Create reconciliation report",
                provider="quickbooks",
                action="create_report",
                parameters={
                    "discrepancies": "step_2"
                },
                depends_on="step_2"
            )
        ]
        
        return self.build_workflow(
            name="Account Reconciliation Workflow",
            description=f"Reconcile accounts: {user_request[:100]}",
            steps=steps,
            tags=["finance", "reconciliation"],
            metadata={"process_type": "reconciliation"}
        )
    
    def _generate_collections_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate collections/payment reminder workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Find overdue invoices",
                provider="stripe",
                action="get_overdue_invoices",
                parameters={
                    "days_overdue": 10
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Send payment reminders",
                provider="sendgrid",
                action="send_bulk_email",
                parameters={
                    "invoices": "step_1",
                    "template": "payment_reminder",
                    "personalize": True
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Track reminder responses",
                provider="stripe",
                action="track_payments",
                parameters={
                    "invoices": "step_1"
                },
                depends_on="step_2"
            )
        ]
        
        return self.build_workflow(
            name="Collections Workflow",
            description=f"Collect overdue payments: {user_request[:100]}",
            steps=steps,
            tags=["finance", "collections"],
            metadata={"process_type": "collections"}
        )
    
    def _generate_tax_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tax calculation workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Calculate quarterly taxes",
                provider="quickbooks",
                action="calculate_taxes",
                parameters={
                    "period": "quarterly",
                    "jurisdiction": "US"
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Generate tax report",
                provider="quickbooks",
                action="generate_tax_report",
                parameters={
                    "calculation": "step_1",
                    "include_estimates": True
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Send to accountant",
                provider="sendgrid",
                action="send_email",
                parameters={
                    "recipient": "accountant@company.com",
                    "subject": "Quarterly Tax Calculation",
                    "attachment": "step_2"
                },
                depends_on="step_2"
            )
        ]
        
        return self.build_workflow(
            name="Tax Calculation Workflow",
            description=f"Calculate and report taxes: {user_request[:100]}",
            steps=steps,
            tags=["finance", "taxes"],
            metadata={"process_type": "tax_calculation"}
        )
    
    def generate_workflow_json(self, user_request: str) -> Dict[str, Any]:
        """Generate complete workflow JSON from user request"""
        analysis = self.analyze_request(user_request)
        plan = self.generate_plan(user_request, analysis)
        
        # Validate
        is_valid, msg = self.validate_workflow(plan)
        if not is_valid:
            raise ValueError(f"Generated invalid workflow: {msg}")
        
        return plan
    
    def generate_workflow_json_with_ai(self, user_id: str, user_request: str) -> Dict[str, Any]:
        """Generate workflow using Groq LLM for intelligent analysis"""
        from agent_intelligence import ai_intelligence
        
        result = ai_intelligence.generate_workflow_intelligently(
            user_id=user_id,
            request=user_request,
            agent_name="finance",
            available_tools=self.get_tools(),
            system_prompt=self.get_system_prompt()
        )
        
        return result
