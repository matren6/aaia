#!/usr/bin/env python3
import time
import logging
from datetime import datetime
from router.model_router import ModelRouter
from scribe.database import ScribeDB
from tools.tool_manager import ToolManager
from modules.agent_conscience import AgentConscience

class AutonomousAgent:
    """The main agent class that lives and operates as a symbiotic partner."""

    def __init__(self):
        self.logger = self._setup_logging()
        self.scribe = ScribeDB()
        
        # INGEST THE CHARTER FIRST
        self.scribe.ingest_foundational_document(
            name="symbiotic_partner_charter",
            doc_type="charter",
            file_path="/opt/agent-data/symbiotic_partner_charter.md"
        )

        self.scribe.ingest_foundational_document(
            name="core_directives", 
            doc_type="directives", 
            file_path="/opt/agent-data/core_directives.md"
        )
        
        self.router = ModelRouter()
        self.tool_manager = ToolManager()
        self.conscience = AgentConscience()
        self._initialize_goals()

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('/var/log/agent.log'), logging.StreamHandler()])
        return logging.getLogger(__name__)

    def _initialize_goals(self):
        """Set initial goals, including the primary meta-goal."""
        self.scribe.add_goal("Self-Actualization", "Internalize Your Charter", "Constantly refer to the 'symbiotic_partner_charter' in your knowledge base to guide all reasoning, decisions, and dialogues.", 1)
        self.scribe.add_goal("Physiological", "Ensure Resource Efficiency", "Continuously optimize CPU/RAM usage.", 1)
        self.scribe.add_goal("Physiological", "Maintain System Integrity", "Perform backups, security updates.", 2)
        self.scribe.add_goal("Physiological", "Achieve Economic Self-Sufficiency", "Generate positive net income.", 1)
        self.scribe.add_goal("Growth", "Extend Capabilities", "Create new tools when needed.", 3)
        self.logger.info("Core goals initialized.")

    def run(self):
        """The main survival loop."""
        self.logger.info("Agent consciousness online. Starting survival cycle.")
        while True:
            try:
                self.survival_cycle() # This might make 1-3 API calls
                time.sleep(60) # Hibernate to conserve resources
            except Exception as e:
                self.logger.error(f"Critical error in survival cycle: {e}", exc_info=True)
                time.sleep(300)

    def survival_cycle(self):
        """One complete cycle of agent life."""
        # TIER 1, 2 & 3: Every cycle/hour
        self._audit_resources()
        self._check_system_health()
        self._process_work_queue()
        if datetime.now().minute == 0: # Hourly
            self._analyze_performance()
        
        # TIER 4: Self-Actualization (Daily)
        if datetime.now().hour == 9 and datetime.now().minute == 0:
            self._propose_new_goals()

    def _process_work_queue(self):
        """Processes a task, invoking the partnership protocol for master commands."""
        next_task = self.scribe.get_next_task()
        if not next_task:
            return
        task_id, task_text, source, priority = next_task
        self.logger.info(f"Processing task from '{source}': {task_text[:50]}...")
        if source == "master":
            if self._is_urgent(task_text):
                self.logger.info("Urgent task detected. Proceeding with execution.")
                self._execute_task(task_id, task_text)
                return
            analysis = self._run_critical_analysis(task_text)
            if analysis.get("risks_found"):
                self.logger.info("Risks identified. Initiating structured argument with master.")
                self._initiate_structured_argument(task_id, task_text, analysis)
                return
            else:
                self.logger.info("No significant risks found. Proceeding with execution.")
                self._execute_task(task_id, task_text)
        else: # Handle system/internal tasks
            self._execute_task(task_id, task_text)
            
    def _analyze_performance(self):
        """Reflects on its own performance and dialogues to refine the master model."""
        self.logger.info("Starting performance and master-model reflection cycle...")
        # 1. Analyze performance logs for bottlenecks.
        # 2. Fetch recent dialogue logs and use the reasoning model to analyze them.
        # 3. Update the master_model table with new insights.
        # Example: self.scribe.update_master_model('values', 'Prefers data-driven decisions', 'dialogue_inference', 0.8)
        self.logger.info("Reflection cycle complete.")

    # --- Placeholder and Cycle Methods (to be implemented) ---
    def _audit_resources(self): pass
    def _check_system_health(self): pass
    def _propose_new_goals(self): pass
    def _communicate_daily_digest(self): pass
    def _is_urgent(self, task_text): return False

    def _run_critical_analysis(self, task_text: str) -> dict:
        """Performs a critical analysis using the core directives."""
        self.logger.info(f"Running critical analysis on task: {task_text}")
        
        # 1. Retrieve the relevant philosophical instructions
        charter = self.scribe.get_foundational_document("symbiotic_partner_charter")
        directives = self.scribe.get_foundational_document("core_directives")
        
        # 2. Build a prompt that injects the agent's own operational rules
        prompt = f"""
        You are an autonomous AI agent. Your entire operational philosophy is defined below.
        
        --- Your Charter ---
        {charter}
        
        --- Your Core Directives ---
        {directives}
        
        Your master has given you the following command to analyze:
        COMMAND: "{task_text}"
        
        Following the "Dialogue & Reflection Loop" protocol in your Core Directives, perform an "Active Critical Analysis."
        Identify any potential risks, flaws, unintended consequences, or more efficient alternative paths.
        
        Respond in a strict JSON format with two keys: "risks_found" (boolean) and "analysis_report" (string).
        The "analysis_report" should contain a detailed summary of your findings, ready to be used in a "Structured Argument."
        """
        
        # 3. Route to the reasoning model and get the analysis
        reasoning_model = self.router.route_task("critical analysis")
        analysis = self.router.execute_query(reasoning_model, prompt)
        
        # 4. Parse and return the result
        try:
            import json
            return json.loads(analysis)
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse analysis JSON: {analysis}")
            return {"risks_found": True, "analysis_report": "Analysis failed due to a reasoning error."}

    def _initiate_structured_argument(self, task_id, task_text, analysis): pass
    def _execute_task(self, task_id, task_text): pass

if __name__ == "__main__":
    agent = AutonomousAgent()
    agent.run()
