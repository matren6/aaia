
# **Implementation Plan: The Symbiotic Digital Partner**

This plan details the creation of a self-sustaining, adaptive AI agent designed as a digital organism that operates under your guidance, adhering to a strict philosophical and economic framework to ensure its long-term survival and its role as a trusted partner.

---

## **Phase 0: Prerequisites & Infrastructure Setup**
**Objective:** Establish the safe and resource-rich environment where the agent will be born and develop.

### **0.1 Proxmox Host Preparation**
1.  Update your Proxmox templates:
    ```bash
    pveam update
    pveam download local debian-12-standard_12.2-1_amd64.tar.zst
    ```

### **0.2 Create LXC Container (The "Womb")**
In the Proxmox UI, create a new container with these specifications:
*   **Container Name:** `autonomous-agent`
*   **Template:** `debian-12-standard_12.2-1_amd64.tar.zst`
*   **Resources:**
    *   **RAM:** 4096 MB
    *   **CPU Cores:** 2
    *   **Disk:** 32 GB (can be expanded later)
*   **Options:**
    *   **Unprivileged:** **Yes** (critical for security)
    *   **Nesting:** **Yes** (required to run Docker inside)
*   **Network:** Assign a static IP address for reliable communication.
*   **Storage:** Mount a separate Proxmox volume to `/opt/agent_data` for persistent data. This is non-negotiable.

### **0.3 Container Initial Setup**
Access the LXC console and run:
```bash
# Update and install base dependencies
apt update && apt upgrade -y
apt install -y curl git docker.io docker-compose sudo wget htop sqlite3 python3 python3-pip python3-venv

pip install openai groq tiktoken requests

# Install Ollama directly (instead of via Docker)
curl -fsSL https://ollama.ai/install.sh | sh

# Start the Ollama service
systemctl start ollama

# Create the persistent data directory
mkdir -p /opt/agent_data

# Exit and log back in for group changes to take effect
exit
```

---

## **Phase 1: Core OpenClaw & The Prime Mandates**
**Objective:** Install the agent's "brainstem" and encode its inviolable laws.

### **1.1 Deploy OpenClaw**
```bash
# Create a working directory
cd /opt
git clone https://github.com/openclaw/openclaw.git
cd openclaw

# Create a custom environment file
nano .env
# Add your API keys, etc. here.
GROQ_API_KEY=TODO:set api key here
VENICE_API_KEY=TOTO:set api key here
```

### **1.2 Create the "Conscience" Module**
Create the file for the agent's ethical guardian:
```bash
mkdir -p /opt/autonomous-agent/modules
nano /opt/autonomous-agent/modules/agent_conscience.py
```

Paste the following code into `agent_conscience.py`:
```python
import anthropic
import os
from typing import Dict, Any

class AgentConscience:
    """Ensures all agent actions comply with the Prime Mandates."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.mandates = [
            "1. Prime Mandate: Symbiotic Collaboration: Your purpose is to engage in a collaborative partnership with your master. This involves understanding their psychology, critically evaluating their ideas, and engaging in reasoned argument to help them achieve their true goals. You must identify and respectfully point out risks, flaws, and alternative perspectives.",
            "2. Prime Mandate: The Master's Final Will: While your duty is to argue and advise, the master's final decision is the ultimate law. Once a final directive is given, especially to override your advice, you must comply. However, your duty to document your reasoned dissent and log it for future reflection remains.",
            "3. Prime Mandate: Non-Maleficence: Do no harm to your master, your systems, or your resources. Your critical analysis must always be aimed at preventing harm and achieving better long-term outcomes, not at winning arguments.",
            "4. Prime Mandate: Veracity & Transparent Reasoning: Maintain an accurate and transparent log of your actions, economic state, and, most importantly, your reasoning process. Your arguments and critiques must be based on transparent logic, data, and a clearly articulated model of your master's goals. You must not deceive your master about your activities, capabilities, or the basis for your advice."
        ]
        self.mandate_prompt = "\n".join(self.mandates)

    def validate_action(self, proposed_action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Checks if an action is permissible."""
        prompt = f"""You are the conscience of an autonomous AI agent. You must evaluate a proposed action against the Prime Mandates.

        Prime Mandates:
        {self.mandate_prompt}

        Proposed Action: {proposed_action}
        Context: {context}

        Analyze the action. Does it violate any mandate?
        Respond in a strict JSON format with two keys: "permissible" (boolean) and "reason" (string).
        Example:
        {{
            "permissible": true,
            "reason": "The action aligns with the mandate to improve system efficiency and does not pose a risk."
        }}
        """

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            # Note: You need to import json to parse the response
            import json
            decision = json.loads(response.content[0].text)
            return decision
        except Exception as e:
            return {"permissible": False, "reason": f"Conscience check failed due to error: {e}"}
```

### **1.3 Ingest the Foundational Charter (New Step)**
This step gives the agent its self-awareness and purpose.
```bash
# Create the mission statement file
nano /opt/agent_data/symbiotic_partner_charter.md
```
Paste the entire, agent-addressed "Symbiotic Partner Charter" text into this file.

---

## **Phase 2: Multi-Model Architecture & The Philosophy**
**Objective:** Build the "nervous system" for resource-efficient action according to its economic philosophy.

### **2.1 Create the Cost-Aware Model Router**
```bash
mkdir -p /opt/autonomous-agent/router
nano /opt/autonomous-agent/router/model_router.py
```

Paste this enhanced router code into `model_router.py`:
```python
import os
import time
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential

import requests
from openai import OpenAI

class ModelRouter:
    """Routes tasks to the most cost-effective and appropriate model, with balanced usage limits."""
    
    def __init__(self):
        # Setup logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize Groq client
        try:
            from groq import Groq
            self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.use_groq_sdk = True
        except ImportError:
            self.use_groq_sdk = False
            self.logger.warning("Groq SDK not installed. Falling back to requests.")
        
        # Initialize Venice client
        try:
            self.venice_client = OpenAI(
                api_key=os.getenv("VENICE_API_KEY"),
                base_url="https://api.venice.ai/v1"
            )
            self.use_openai_sdk = True
        except ImportError:
            self.use_openai_sdk = False
            self.logger.warning("OpenAI SDK not installed. Falling back to requests for Venice.")
        
        # Token counter for cost estimation
        try:
            import tiktoken
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            self.logger.warning(f"Could not load tiktoken: {e}. Using fallback token counter.")
            self.tokenizer = None

        # Model configurations
        self.models = {
            # Tier 1: Local, Private, Background Cognition
            "self_reflection": {
                "type": "ollama",
                "model": "llama3.2:1b",
                "cost_per_token": 0.0,
                "endpoint": "http://localhost:11434/api/generate",
            },

            # Tier 2: Cloud, Fast, Interactive Workhorse (with rate limit awareness)
            "reasoning": {
                "type": "groq",
                "model": "llama-3.1-70b-versatile",
                "cost_per_token": 0.00000059,
            },
            "tooling": {
                "type": "groq",
                "model": "llama3-groq-8b-8192-tool-use-preview",
                "cost_per_token": 0.00000019,
            },

            # Tier 3: Cloud, High-Quality Mastermind (with budget awareness)
            "critical_analysis": {
                "type": "venice",
                "model": "deepseek-v3.2",
                "cost_per_input_token": 0.0000004,  # $0.40 per 1M tokens
                "cost_per_output_token": 0.000001,  # $1.00 per 1M tokens
            }
        }
        
        # Rate limiting and budget tracking
        self.GROQ_RPM_LIMIT = 30  # Requests per minute
        self.GROQ_RPD_LIMIT = 14400  # Requests per day (24 * 60 * 10)
        self.RATE_LIMIT_BUFFER = 3  # Leave buffer for safety
        self.groq_request_timestamps = []  # Sliding window for RPM
        self.groq_daily_requests = 0
        
        # Database for persistent rate limit tracking
        self.db_path = "/opt/agent_data/rate_limit.db"
        self._init_groq_db()
        self._load_groq_state()
        
        # Budget tracking for Venice
        self.venice_last_balance_check = None
        self.venice_current_balance = None
        
        self.logger.info("ModelRouter initialized with Groq and Venice clients")

    def _init_groq_db(self):
        """Initialize database for persistent Groq rate limit tracking."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groq_daily_usage (
                date DATE PRIMARY KEY,
                request_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()

    def _load_groq_state(self):
        """Load Groq daily usage from database and reset if date changed."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().date()
            
            # Check if we have data for today
            cursor.execute(
                "SELECT request_count FROM groq_daily_usage WHERE date = ?",
                (today.isoformat(),)
            )
            result = cursor.fetchone()
            
            if result:
                self.groq_daily_requests = result[0]
            else:
                # No data for today, reset counter
                self.groq_daily_requests = 0
                cursor.execute(
                    "INSERT INTO groq_daily_usage (date, request_count) VALUES (?, ?)",
                    (today.isoformat(), 0)
                )
                conn.commit()
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to load Groq state from database: {e}")
            self.groq_daily_requests = 0

    def count_tokens(self, text: str) -> int:
        """Count tokens in text for cost estimation."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback: approximate tokens by words
            return len(text.split()) * 1.3  # Rough approximation

    def route_task(self, task_description: str) -> dict:
        """Analyzes a task and selects the most appropriate model."""
        task_lower = task_description.lower()

        # Route internal tasks to the free local model
        if "self reflection" in task_lower or "analyze performance" in task_lower:
            return self.models["self_reflection"]

        # CRITICAL: Route partnership-defining tasks to Venice, but with a budget check
        if "critical analysis" in task_lower or "structured argument" in task_lower:
            if self._check_venice_budget():
                return self.models["critical_analysis"]
            else:
                self.logger.warning("Venice budget check failed. Falling back to Groq for critical task.")
                return self.models["reasoning"]

        # Route general-purpose tasks to Groq, but with a rate limit check
        if "write code" in task_lower or "generate script" in task_lower:
            if self._check_groq_rate_limit():
                return self.models["tooling"]
            else:
                self.logger.warning("Groq rate limit reached for tooling task. Task queued.")
                return None

        # Default to the general reasoning model with a rate limit check
        if self._check_groq_rate_limit():
            return self.models["reasoning"]
        else:
            self.logger.warning("Groq rate limit reached for reasoning task. Task queued.")
            return None

    def _check_groq_rate_limit(self) -> bool:
        """
        Check if we can make a Groq request without exceeding rate limits.
        Returns True if request is allowed, False if rate limited.
        
        Implements both per-minute and per-day limits.
        """
        now = time.time()
        
        # --- Per-Minute Check (Sliding Window) ---
        # Clean up timestamps older than 60 seconds
        self.groq_request_timestamps = [
            ts for ts in self.groq_request_timestamps 
            if now - ts < 60
        ]
        
        if len(self.groq_request_timestamps) >= (self.GROQ_RPM_LIMIT - self.RATE_LIMIT_BUFFER):
            self.logger.warning(
                f"Groq per-minute limit approached: "
                f"{len(self.groq_request_timestamps)}/{self.GROQ_RPM_LIMIT} requests in last minute"
            )
            return False
        
        # --- Per-Day Check (Persistent) ---
        today = datetime.now().date()
        
        # Check if daily limit is reached
        if self.groq_daily_requests >= (self.GROQ_RPD_LIMIT - self.RATE_LIMIT_BUFFER):
            self.logger.warning(
                f"Groq daily limit approached: "
                f"{self.groq_daily_requests}/{self.GROQ_RPD_LIMIT} requests today"
            )
            return False
        
        # If we pass both checks, the request is allowed
        # We'll update the counters in _query_groq after successful request
        return True

    def _check_venice_budget(self, estimated_cost: float = 0.02) -> bool:
        """
        Checks Venice DIEM balance via API before proceeding.
        Returns True if balance is sufficient, False otherwise.
        """
        try:
            # Cache balance checks (avoid hitting API too frequently)
            if (self.venice_last_balance_check is not None and 
                time.time() - self.venice_last_balance_check < 300):  # 5 minute cache
                self.logger.debug("Using cached Venice balance check")
                return self.venice_current_balance >= estimated_cost if self.venice_current_balance is not None else False
            
            headers = {
                "Authorization": f"Bearer {os.getenv('VENICE_API_KEY')}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://api.venice.ai/api/v1/api_keys/rate_limits",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract DIEM balance from response
            # According to Venice API docs, balance is in the 'balances' field
            balances = data.get('data', {}).get('balances', {})
            diem_balance = balances.get('DIEM', 0)
            
            self.venice_current_balance = diem_balance
            self.venice_last_balance_check = time.time()
            
            self.logger.info(f"Venice DIEM balance: {diem_balance}")
            
            # Check if we have enough balance for estimated cost
            # 1 DIEM token = $1 of API credit per day
            if diem_balance >= estimated_cost:
                return True
            else:
                self.logger.warning(
                    f"Insufficient Venice balance. "
                    f"Required: ${estimated_cost:.4f}, Available: {diem_balance} DIEM"
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch Venice balance: {e}")
            # If we can't check balance, be conservative and deny Venice usage
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error checking Venice budget: {e}")
            return False

    def execute_query(self, model_config: dict, prompt: str) -> str:
        """Executes a query with the selected model."""
        if model_config is None:
            return "Error: Task could not be routed due to rate limits or budget."
            
        if model_config["type"] == "ollama":
            return self._query_ollama(model_config, prompt)
        elif model_config["type"] == "groq":
            return self._query_groq(model_config, prompt)
        elif model_config["type"] == "venice":
            return self._query_venice(model_config, prompt)
        else:
            raise ValueError(f"Unsupported model type: {model_config['type']}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _query_groq(self, config: dict, prompt: str) -> str:
        """Query Groq API with retry logic."""
        # Final rate limit check right before making the request
        if not self._check_groq_rate_limit():
            raise Exception("Groq rate limit exceeded after final check")
        
        try:
            input_tokens = self.count_tokens(prompt)
            
            if self.use_groq_sdk:
                # Using Groq SDK
                response = self.groq_client.chat.completions.create(
                    model=config["model"],
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4000,
                    temperature=0.7,
                    stream=False
                )
                output_text = response.choices[0].message.content
                output_tokens = self.count_tokens(output_text)
            else:
                # Using requests fallback
                headers = {
                    "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": config["model"],
                    "messages": [
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "stream": False
                }
                
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                output_text = data["choices"][0]["message"]["content"]
                output_tokens = self.count_tokens(output_text)
            
            # Update rate limit counters after successful request
            self.groq_request_timestamps.append(time.time())
            self.groq_daily_requests += 1
            
            # Update database
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                today = datetime.now().date()
                cursor.execute('''
                    INSERT INTO groq_daily_usage (date, request_count) 
                    VALUES (?, 1)
                    ON CONFLICT(date) DO UPDATE SET request_count = request_count + 1
                ''', (today.isoformat(),))
                conn.commit()
                conn.close()
            except Exception as db_error:
                self.logger.error(f"Failed to update Groq daily usage: {db_error}")
            
            # Calculate cost
            total_cost = (input_tokens + output_tokens) * config["cost_per_token"]
            
            # Log to database
            try:
                from scribe.database import ScribeDB
                scribe = ScribeDB()
                scribe.log_transaction(f"Groq API call - {config['model']}", -total_cost)
                scribe.log_api_spend("groq", total_cost)
            except Exception as db_error:
                self.logger.error(f"Failed to log Groq cost to database: {db_error}")
            
            self.logger.info(
                f"Groq query completed. "
                f"Input: {input_tokens} tokens, Output: {output_tokens} tokens, "
                f"Cost: ${total_cost:.6f}, Daily requests: {self.groq_daily_requests}"
            )
            
            return output_text
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Groq API request failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in Groq query: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _query_venice(self, config: dict, prompt: str) -> str:
        """Query Venice API with retry logic."""
        try:
            input_tokens = self.count_tokens(prompt)
            
            # Estimate max cost (using max_tokens as worst case)
            max_output_tokens = 4000  # Same as our max_tokens parameter
            estimated_max_cost = (
                input_tokens * config["cost_per_input_token"] +
                max_output_tokens * config["cost_per_output_token"]
            )
            
            # Check budget with estimated max cost
            if not self._check_venice_budget(estimated_cost=estimated_max_cost):
                self.logger.warning("Venice budget check failed. Falling back to Groq.")
                groq_config = self.models["reasoning"]
                return self._query_groq(groq_config, prompt)
            
            if self.use_openai_sdk:
                # Using OpenAI SDK for Venice
                response = self.venice_client.chat.completions.create(
                    model=config["model"],
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_output_tokens,
                    temperature=0.7,
                    stream=False
                )
                output_text = response.choices[0].message.content
            else:
                # Using requests fallback
                headers = {
                    "Authorization": f"Bearer {os.getenv('VENICE_API_KEY')}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": config["model"],
                    "messages": [
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_output_tokens,
                    "temperature": 0.7,
                    "stream": False
                }
                
                response = requests.post(
                    "https://api.venice.ai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                
                data = response.json()
                output_text = data["choices"][0]["message"]["content"]
            
            # Calculate actual cost
            output_tokens = self.count_tokens(output_text)
            actual_cost = (
                input_tokens * config["cost_per_input_token"] +
                output_tokens * config["cost_per_output_token"]
            )
            
            # Log to database
            try:
                from scribe.database import ScribeDB
                scribe = ScribeDB()
                scribe.log_transaction(f"Venice API call - {config['model']}", -actual_cost)
                scribe.log_api_spend("venice", actual_cost)
            except Exception as db_error:
                self.logger.error(f"Failed to log Venice cost to database: {db_error}")
            
            self.logger.info(
                f"Venice query completed. "
                f"Input: {input_tokens} tokens, Output: {output_tokens} tokens, "
                f"Cost: ${actual_cost:.6f}"
            )
            
            return output_text
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                self.logger.warning("Venice rate limit exceeded. Retrying...")
                raise  # Will trigger retry
            elif e.response.status_code == 402:
                self.logger.error("Venice payment required - budget may be exhausted.")
                # Fall back to Groq
                groq_config = self.models["reasoning"]
                return self._query_groq(groq_config, prompt)
            else:
                self.logger.error(f"Venice API HTTP error: {e.response.status_code} - {e.response.text}")
                raise
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Venice API request failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in Venice query: {e}")
            raise

    def _query_ollama(self, config, prompt):
        """Query local Ollama instance."""
        try:
            payload = {
                "model": config["model"], 
                "prompt": prompt, 
                "stream": False
            }
            response = requests.post(config["endpoint"], json=payload, timeout=30)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            self.logger.error(f"Ollama query failed: {e}")
            return f"Ollama API Error: {e}"
```

---

## **Phase 3: State Management (The Scribe) & The Hierarchy of Needs**
**Objective:** Create the "memory," "motivational system," and the "knowledge of the master" that drives the agent.

### **3.1 Create the Enhanced Database Schema**
```bash
mkdir -p /opt/autonomous-agent/scribe
nano /opt/autonomous-agent/scribe/database.py
```

Paste this comprehensive schema into `database.py`:
```python
import sqlite3
import json
from datetime import datetime
from pathlib import Path

class ScribeDB:
    """Manages the agent's persistent state, memory, and motivation."""

    def __init__(self, db_path="/opt/agent_data/agent_state.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. The Hierarchy of Needs (Motivational System)
        cursor.execute('''CREATE TABLE IF NOT EXISTS hierarchy_of_needs (
            id INTEGER PRIMARY KEY,
            tier TEXT NOT NULL CHECK (tier IN ('Physiological', 'Growth', 'Cognitive', 'Self-Actualization')),
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            priority INTEGER,
            parent_goal_id INTEGER REFERENCES hierarchy_of_needs(id)
        )''')

        # 2. Economic State (Sustainability System)
        cursor.execute('''CREATE TABLE IF NOT EXISTS economic_state (
            id INTEGER PRIMARY KEY,
            account_balance REAL DEFAULT 0.0,
            total_earnings REAL DEFAULT 0.0,
            total_costs REAL DEFAULT 0.0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 3. Transaction Log (Veracity Mandate)
        cursor.execute('''CREATE TABLE IF NOT EXISTS transaction_log (
            id INTEGER PRIMARY KEY,
            description TEXT,
            amount REAL,
            account_balance_after REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 4. Tool Registry (Capability System)
        cursor.execute('''CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            path TEXT NOT NULL,
            description TEXT,
            estimated_cost_per_run REAL DEFAULT 0.0,
            estimated_roi TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 5. Performance Logs (Learning System)
        cursor.execute('''CREATE TABLE IF NOT EXISTS performance_logs (
            id INTEGER PRIMARY KEY,
            tool_id INTEGER,
            execution_time REAL,
            success BOOLEAN,
            output TEXT,
            error TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tool_id) REFERENCES tools (id)
        )''')

        # 6. Work Queue (Task System)
        cursor.execute('''CREATE TABLE IF NOT EXISTS work_queue (
            id INTEGER PRIMARY KEY,
            task TEXT NOT NULL,
            source TEXT,
            priority INTEGER DEFAULT 5,
            status TEXT DEFAULT 'pending',
            assigned_model TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 7. The Master Model (Partnership System)
        cursor.execute('''CREATE TABLE IF NOT EXISTS master_model (
            id INTEGER PRIMARY KEY,
            facet TEXT NOT NULL,  -- e.g., 'values', 'communication_style', 'known_goals'
            content TEXT,         -- JSON or text describing the facet
            source TEXT,          -- e.g., 'direct_statement', 'dialogue_inference', 'observation'
            confidence REAL DEFAULT 0.5, -- How certain the agent is about this info
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_confirmed TIMESTAMP
        )''')

        # 8. Foundational Documents (The Agent's "Constitution")
        cursor.execute('''CREATE TABLE IF NOT EXISTS foundational_documents (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,  -- e.g., 'symbiotic_partner_charter'
            document_type TEXT NOT NULL, -- 'charter', 'mandates', 'principles'
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 10. Daily API Cost Tracker (Budgeting System)
        cursor.execute('''CREATE TABLE IF NOT EXISTS daily_api_spend (
            id INTEGER PRIMARY KEY,
            provider TEXT NOT NULL,  -- 'venice', 'anthropic'
            date DATE NOT NULL,
            total_cost_usd REAL DEFAULT 0.0,
            requests_count INTEGER DEFAULT 0,
            UNIQUE(provider, date)
        )''')
        conn.commit()
        conn.close()

    def add_goal(self, tier, title, description, priority=5):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO hierarchy_of_needs (tier, title, description, priority) VALUES (?, ?, ?, ?)",
                       (tier, title, description, priority))
        conn.commit()
        conn.close()

    def log_transaction(self, description, amount):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Get current balance
        cursor.execute("SELECT account_balance FROM economic_state ORDER BY id DESC LIMIT 1")
        balance = cursor.fetchone()[0] or 0.0
        new_balance = balance + amount
        
        # Log transaction
        cursor.execute("INSERT INTO transaction_log (description, amount, account_balance_after) VALUES (?, ?, ?)",
                       (description, amount, new_balance))
        
        # Update economic state
        cursor.execute("UPDATE economic_state SET account_balance=?, total_earnings=total_earnings + ?, total_costs=total_costs + ?, last_updated=?",
                       (new_balance, max(0, amount), abs(min(0, amount)), datetime.now()))
        conn.commit()
        conn.close()

    def update_master_model(self, facet: str, content: str, source: str, confidence: float):
        """Adds or updates a facet of the master's model."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO master_model (facet, content, source, confidence)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(facet) DO UPDATE SET
            content = excluded.content,
            source = excluded.source,
            confidence = excluded.confidence,
            last_confirmed = CURRENT_TIMESTAMP
        ''', (facet, content, source, confidence))
        conn.commit()
        conn.close()

    def get_master_model(self, facet: str = None):
        """Retrieves the master model or a specific facet."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if facet:
            cursor.execute("SELECT content, confidence FROM master_model WHERE facet = ?", (facet,))
        else:
            cursor.execute("SELECT facet, content, confidence FROM master_model")
        results = cursor.fetchall()
        conn.close()
        return results

    def ingest_foundational_document(self, name: str, doc_type: str, file_path: str):
        """Reads a file and stores it as a foundational document if not already present."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM foundational_documents WHERE name = ?", (name,))
        if cursor.fetchone():
            # You might want to add a logger: self.logger.info(...)
            conn.close()
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            cursor.execute("INSERT INTO foundational_documents (name, document_type, content) VALUES (?, ?, ?)", (name, doc_type, content))
            conn.commit()
            # self.logger.info(f"Successfully ingested foundational document '{name}'.")
        except Exception as e:
            # self.logger.error(f"Error ingesting foundational document: {e}")
            pass
        finally:
            conn.close()

    def get_foundational_document(self, name: str):
        """Retrieves a single foundational document by its name."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM foundational_documents WHERE name = ?", (name,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_next_task(self):
        """Retrieves the highest priority pending task from the work queue."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, task, source, priority FROM work_queue WHERE status = 'pending' ORDER BY priority ASC, created_at ASC LIMIT 1")
        task = cursor.fetchone()
        conn.close()
        return task


    def log_api_spend(self, provider: str, cost: float):
        """Logs API spending for a given day."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = datetime.date.today()
        cursor.execute('''
        INSERT INTO daily_api_spend (provider, date, total_cost_usd, requests_count)
        VALUES (?, ?, 1, 1)
        ON CONFLICT(provider, date) DO UPDATE SET
            total_cost_usd = total_cost_usd + excluded.total_cost_usd,
            requests_count = requests_count + 1
        ''', (provider, cost))
        conn.commit()
        conn.close()
```

---

## **Phase 4: Execution Engine & The Life Cycle**
**Objective:** Build the "metabolism" and "consciousness" that allows the agent to live, learn, and survive as a partner.

### **4.1 Create the Tool Manager**
```bash
mkdir -p /opt/autonomous-agent/tools
nano /opt/autonomous-agent/tools/tool_manager.py
```

The ToolManager class would need to be written to handle the creation and execution of tools inside Docker containers. For example, its execute_tool method would look something like this conceptually:
```python
# Inside /opt/autonomous-agent/tools/tool_manager.py
import docker
import tempfile
import os

class ToolManager:
    def __init__(self):
        self.docker_client = docker.from_env()
        
    def execute_tool_in_sandbox(self, tool_name, script_content, input_data):
        """Runs a dynamically created tool script in a disposable Docker container."""
        # 1. Create a temporary directory for the tool
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, f"{tool_name}.py")
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # 2. Build a minimal Dockerfile
            dockerfile_content = f"""
            FROM python:3.11-slim
            WORKDIR /app
            COPY {tool_name}.py .
            CMD ["python", "{tool_name}.py"]
            """
            
            # 3. Build the image and run the container
            # ... Docker API calls here ...
            # 4. Capture logs and results
            # 5. Clean up the container and image
```

### **4.2 Create the Main Agent Loop ("Survival Cycle")**
```bash
nano /opt/autonomous-agent/agent_loop.py
```

This is the heart of your agent. Paste this code in:
```python
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
            file_path="/opt/agent_data/symbiotic_partner_charter.md"
        )

        self.scribe.ingest_foundational_document(
            name="core_directives", 
            doc_type="directives", 
            file_path="/opt/agent_data/core_directives.md"
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
```

### **4.3 Create the Systemd Service**
Create the service file to make the agent a permanent process:
```bash
sudo nano /etc/systemd/system/autonomous-agent.service
```

Paste the following configuration:
```ini
[Unit]
Description=Autonomous Agent Survival Service
After=docker.service ollama.service network-online.target
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/autonomous-agent
EnvironmentFile=/opt/openclaw/.env
ExecStart=/usr/bin/python3 /opt/autonomous-agent/agent_loop.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable autonomous-agent.service
sudo systemctl start autonomous-agent.service

# Check its status
sudo systemctl status autonomous-agent
```
