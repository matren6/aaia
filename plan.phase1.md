## **PHASE 1: SURVIVAL FOUNDATION**

### **Week 1-2: LXC Container & Python Environment**

**Container Specifications:**
```
Container Name: autonomous-agent-core
Base OS: Ubuntu 22.04 LTS (minimal)
Resources:
  CPU: 4 vCPUs minimum
  RAM: 8GB minimum (expandable)
  Storage: 50GB root + 100GB data volume
  Network: Bridged adapter with static IP allocation

Security Hardening:
  - Seccomp profile: restricted syscalls
  - AppArmor profile: deny-write-to-host
  - No privileged container flag
  - Root filesystem mounted as read-only where possible
```

**Python Environment Structure:**
```
/opt/autonomous-agent/
├── venv/                    # Python virtual environment
├── src/
│   ├── requirements.txt     # Phase 1 dependencies
│   ├── bootstrap.sh         # Container initialization script
│   └── config/
│       └── environment.env  # Environment variables
├── data/
│   ├── logs/
│   ├── db/
│   └── knowledge/
└── backups/
```

**Core Dependencies (requirements.txt):**
```txt
# Core Runtime
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-dotenv==1.0.0

# Database & State
sqlalchemy==2.0.23
asyncpg==0.29.0
redis==5.0.1
alembic==1.13.0

# Monitoring & Metrics
psutil==5.9.7
prometheus-client==0.19.0
influxdb-client==1.39.0

# System Utilities
aiofiles==23.2.1
watchdog==3.0.0
python-dateutil==2.8.2

# Security
cryptography==41.0.7
bcrypt==4.1.2
```

**Bootstrap Script (`bootstrap.sh`):**
```bash
#!/bin/bash
set -euo pipefail

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[93m'
LIGHTBLUE='\033[1;34m'
NC='\033[0m'

echo -e "${LIGHTBLUE}⚙️  Initializing Autonomous AI Container...${NC}"

# Function for progress indicators
progress() {
    echo -e "${YELLOW}⏳ $1...${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Update system
progress "Updating system packages"
apt-get update && apt-get upgrade -y

# Install Python 3.11
progress "Installing Python 3.11"
apt-get install -y python3.11 python3.11-venv python3.11-dev

# Create project directory
progress "Creating project structure"
mkdir -p /opt/autonomous-agent/{src,data/{logs,db,knowledge},backups}

# Setup virtual environment
progress "Setting up Python virtual environment"
python3.11 -m venv /opt/autonomous-agent/venv
source /opt/autonomous-agent/venv/bin/activate

# Install dependencies
progress "Installing Python dependencies"
pip install --upgrade pip
pip install -r /opt/autonomous-agent/src/requirements.txt

# Create systemd service
progress "Creating systemd service"
cat > /etc/systemd/system/autonomous-agent.service << EOF
[Unit]
Description=Autonomous AI Agent Core
After=network.target postgresql.service redis-server.service
Requires=postgresql.service redis-server.service

[Service]
Type=simple
User=autonomous
Group=autonomous
WorkingDirectory=/opt/autonomous-agent/src
EnvironmentFile=/opt/autonomous-agent/src/config/environment.env
ExecStart=/opt/autonomous-agent/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=autonomous-agent
LimitNOFILE=65536
LimitNPROC=65536

[Install]
WantedBy=multi-user.target
EOF

# Create dedicated user
progress "Creating system user"
useradd -r -s /bin/false -d /opt/autonomous-agent autonomous
chown -R autonomous:autonomous /opt/autonomous-agent

# Initialize environment file
progress "Creating environment configuration"
cat > /opt/autonomous-agent/src/config/environment.env << EOF
# Database Configuration
DATABASE_URL=postgresql://autonomous:${POSTGRES_PASSWORD}@localhost/autonomous_db
REDIS_URL=redis://localhost:6379/0

# Economic Settings
CPU_WARNING_THRESHOLD=80
MEMORY_WARNING_THRESHOLD=85
STORAGE_WARNING_THRESHOLD=90
API_COST_TRACKING_ENABLED=true

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
SESSION_TIMEOUT=3600

# Logging
LOG_LEVEL=INFO
LOG_FILE=/opt/autonomous-agent/data/logs/agent.log
AUDIT_LOG_FILE=/opt/autonomous-agent/data/logs/audit.log
EOF

success "Bootstrap completed!"
echo -e "${LIGHTBLUE}📋 Next steps:"
echo "1. Set PostgreSQL password: export POSTGRES_PASSWORD='your_password'"
echo "2. Run database initialization: /opt/autonomous-agent/src/scripts/init_db.py"
echo "3. Start service: systemctl start autonomous-agent${NC}"
```

### **Week 3-4: The Scribe Service (Database Schema)**

**PostgreSQL Schema (`database/schema.sql`):**
```sql
-- Core Tables
CREATE TABLE master_profile (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    psychological_model JSONB NOT NULL DEFAULT '{}',
    communication_preferences JSONB DEFAULT '{"preferred_style": "structured", "verbosity": "detailed"}',
    goals JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_psych_model CHECK (
        jsonb_typeof(psychological_model) = 'object'
    )
);

CREATE TABLE economic_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type VARCHAR(50) NOT NULL CHECK (
        resource_type IN ('CPU', 'RAM', 'STORAGE', 'API_CREDITS', 'MONEY')
    ),
    current_level NUMERIC(10,2) NOT NULL DEFAULT 0,
    max_capacity NUMERIC(10,2),
    cost_per_unit NUMERIC(10,4) DEFAULT 0,
    income_per_unit NUMERIC(10,4) DEFAULT 0,
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE interaction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL CHECK (
        interaction_type IN ('COMMAND', 'QUERY', 'ARGUMENT', 'REFLECTION')
    ),
    master_input TEXT NOT NULL,
    agent_response TEXT,
    agent_reasoning JSONB,  -- Structured reasoning tree
    mandate_compliance_score INTEGER CHECK (
        mandate_compliance_score BETWEEN 0 AND 100
    ),
    risk_assessment JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tool_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_name VARCHAR(100) UNIQUE NOT NULL,
    tool_description TEXT,
    tool_code TEXT,
    category VARCHAR(50) CHECK (
        category IN ('SYSTEM', 'ANALYSIS', 'COMMUNICATION', 'ECONOMIC', 'SECURITY')
    ),
    resource_usage JSONB DEFAULT '{"cpu": 0, "memory": 0, "cost": 0}',
    success_rate NUMERIC(5,2) DEFAULT 100.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE hierarchy_of_needs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tier VARCHAR(50) NOT NULL CHECK (
        tier IN ('PHYSIOLOGICAL', 'SECURITY', 'GROWTH', 'COGNITIVE', 'SELF_ACTUALIZATION')
    ),
    current_focus_percentage NUMERIC(5,2) DEFAULT 0,
    needs_met BOOLEAN DEFAULT FALSE,
    last_assessment TIMESTAMP,
    priority_level INTEGER CHECK (priority_level BETWEEN 1 AND 10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mandate_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_id VARCHAR(100) NOT NULL,
    mandate_name VARCHAR(100) NOT NULL CHECK (
        mandate_name IN ('SYMBIOTIC_COLLABORATION', 'MASTERS_FINAL_WILL', 
                        'NON_MALEFICENCE', 'VERACITY')
    ),
    compliance_result BOOLEAN NOT NULL,
    risk_score INTEGER CHECK (risk_score BETWEEN 0 AND 10),
    override_used BOOLEAN DEFAULT FALSE,
    reasoning JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_interaction_logs_session ON interaction_logs(session_id);
CREATE INDEX idx_interaction_logs_created ON interaction_logs(created_at);
CREATE INDEX idx_economic_state_type ON economic_state(resource_type, measured_at DESC);
CREATE INDEX idx_mandate_logs_action ON mandate_logs(action_id);
CREATE INDEX idx_hierarchy_tier ON hierarchy_of_needs(tier);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_master_profile_timestamp 
    BEFORE UPDATE ON master_profile 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tool_registry_timestamp 
    BEFORE UPDATE ON tool_registry 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Initial data
INSERT INTO hierarchy_of_needs (tier, current_focus_percentage, needs_met, priority_level) VALUES
('PHYSIOLOGICAL', 100.00, FALSE, 1),
('SECURITY', 0.00, FALSE, 2),
('GROWTH', 0.00, FALSE, 3),
('COGNITIVE', 0.00, FALSE, 4),
('SELF_ACTUALIZATION', 0.00, FALSE, 5);
```

**FastAPI Application Structure (`src/api/`):**
```
api/
├── __init__.py
├── main.py                    # FastAPI app entry point
├── database/
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy models
│   ├── crud.py               # CRUD operations
│   ├── schemas.py            # Pydantic schemas
│   └── session.py            # Database session management
├── endpoints/
│   ├── __init__.py
│   ├── master.py             # Master profile endpoints
│   ├── economic.py          # Economic state endpoints
│   ├── interactions.py      # Interaction logging
│   ├── tools.py             # Tool registry
│   ├── hierarchy.py         # Hierarchy of needs
│   └── mandates.py          # Mandate logging
└── middleware/
    ├── __init__.py
    ├── authentication.py    # API auth middleware
    └── logging.py           # Request/response logging
```

**Core API Endpoints:**

1. **Master Profile API** (`/api/v1/master/profile`):
```python
# endpoints/master.py
from fastapi import APIRouter, Depends, HTTPException
from database import get_db, crud
from schemas import MasterProfileCreate, MasterProfileUpdate, MasterProfileResponse

router = APIRouter(prefix="/master", tags=["master"])

@router.get("/profile", response_model=MasterProfileResponse)
async def get_profile(db = Depends(get_db)):
    """Get current master profile"""
    profile = crud.get_master_profile(db)
    if not profile:
        raise HTTPException(status_code=404, detail="Master profile not found")
    return profile

@router.put("/profile", response_model=MasterProfileResponse)
async def update_profile(
    profile_update: MasterProfileUpdate,
    db = Depends(get_db)
):
    """Update master profile with psychological model"""
    updated = crud.update_master_profile(db, profile_update)
    return updated

@router.post("/profile/goals")
async def add_goal(goal: dict, db = Depends(get_db)):
    """Add a goal to master profile"""
    return crud.add_master_goal(db, goal)

@router.get("/profile/psychology")
async def get_psychological_model(db = Depends(get_db)):
    """Get refined psychological model"""
    profile = crud.get_master_profile(db)
    return profile.psychological_model
```

2. **Economic State API** (`/api/v1/economic`):
```python
# endpoints/economic.py
from fastapi import APIRouter, BackgroundTasks
from schemas import EconomicStateCreate, EconomicSnapshot
from services.economic_monitor import record_economic_snapshot

router = APIRouter(prefix="/economic", tags=["economic"])

@router.post("/snapshot")
async def create_snapshot(
    background_tasks: BackgroundTasks,
    snapshot: EconomicStateCreate
):
    """Record economic state snapshot"""
    background_tasks.add_task(record_economic_snapshot, snapshot)
    return {"status": "snapshot_queued"}

@router.get("/current")
async def get_current_state(db = Depends(get_db)):
    """Get current economic state for all resources"""
    states = crud.get_latest_economic_states(db)
    return {
        "cpu": states.get("CPU"),
        "memory": states.get("RAM"),
        "storage": states.get("STORAGE"),
        "api_credits": states.get("API_CREDITS"),
        "timestamp": datetime.utcnow()
    }

@router.get("/history/{resource_type}")
async def get_resource_history(
    resource_type: str,
    hours: int = 24,
    db = Depends(get_db)
):
    """Get historical data for a resource"""
    history = crud.get_economic_history(db, resource_type, hours)
    return {"resource": resource_type, "history": history}
```

### **Week 5-6: Economic System Specifications**

#### **Simplified Economic Monitoring System**

Since you want to keep it slim and simple, focusing only on monetary costs, here's a streamlined design:

#### **Core Database Schema Additions**

```sql
-- Simplified economic tracking table
CREATE TABLE monetary_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_type VARCHAR(50) NOT NULL CHECK (
        transaction_type IN ('API_COST', 'LOCAL_MODEL_COST', 'INFRASTRUCTURE', 
                           'INCOME', 'MISC_EXPENSE', 'INVESTMENT')
    ),
    amount DECIMAL(10,6) NOT NULL,  -- Positive for income, negative for costs
    currency VARCHAR(3) DEFAULT 'USD',
    description TEXT NOT NULL,
    cost_center VARCHAR(50),  -- E.g., 'DIALOGUE', 'MODEL_ROUTING', 'TOOL_FORGE'
    marginal_benefit DECIMAL(5,3) DEFAULT 1.000, -- 1.0 = neutral, >1.0 = beneficial
    marginal_cost DECIMAL(5,3) DEFAULT 1.000,    -- 1.0 = neutral, <1.0 = cheaper
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_name VARCHAR(100) UNIQUE NOT NULL,
    cost_per_unit DECIMAL(10,6) NOT NULL,
    unit_type VARCHAR(50) NOT NULL,  -- E.g., 'per_token', 'per_second', 'per_call'
    provider VARCHAR(100),            -- E.g., 'OpenAI', 'Groq', 'Local'
    model_name VARCHAR(100),          -- E.g., 'llama-3.3-70b-versatile'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE economic_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    total_balance DECIMAL(12,6) NOT NULL DEFAULT 0,
    daily_expense DECIMAL(12,6) NOT NULL DEFAULT 0,
    daily_income DECIMAL(12,6) NOT NULL DEFAULT 0,
    cost_efficiency DECIMAL(5,3) DEFAULT 1.000, -- Higher = more efficient
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for efficient queries
CREATE INDEX idx_transactions_date_type ON monetary_transactions(created_at DESC, transaction_type);
CREATE INDEX idx_transactions_cost_center ON monetary_transactions(cost_center);
CREATE INDEX idx_cost_config_resource ON cost_configurations(resource_name);
```

#### **Cost Configuration Defaults**

```sql
-- Default cost configurations
INSERT INTO cost_configurations (resource_name, cost_per_unit, unit_type, provider, model_name) VALUES
-- API Costs (using estimated prices)
('openai-gpt-4-turbo-input', 0.00001, 'per_token', 'OpenAI', 'gpt-4-turbo'),
('openai-gpt-4-turbo-output', 0.00003, 'per_token', 'OpenAI', 'gpt-4-turbo'),
('anthropic-claude-3-opus-input', 0.000015, 'per_token', 'Anthropic', 'claude-3-opus'),
('anthropic-claude-3-opus-output', 0.000075, 'per_token', 'Anthropic', 'claude-3-opus'),
('groq-llama-3.3-70b-input', 0.0000007, 'per_token', 'Groq', 'llama-3.3-70b-versatile'),
('groq-llama-3.3-70b-output', 0.0000008, 'per_token', 'Groq', 'llama-3.3-70b-versatile'),
('groq-llama-3.1-8b-input', 0.0000001, 'per_token', 'Groq', 'llama-3.1-8b-instant'),
('groq-llama-3.1-8b-output', 0.0000001, 'per_token', 'Groq', 'llama-3.1-8b-instant'),

-- Local Model Costs (monetizing CPU/RAM usage)
('local-cpu-second', 0.000000278, 'per_second', 'Local', 'CPU'), -- ~$0.001/hour
('local-ram-gb-second', 0.000000056, 'per_gb_second', 'Local', 'RAM'), -- ~$0.0002/GB-hour
('local-disk-io', 0.000000001, 'per_mb', 'Local', 'Disk'),

-- Infrastructure Costs
('electricity-watt-hour', 0.00015, 'per_watt_hour', 'Infrastructure', 'Electricity'),
('network-gb', 0.0005, 'per_gb', 'Infrastructure', 'Bandwidth');
```

#### **Simplified Economic Service Architecture**

```
src/services/economic/
├── __init__.py
├── cost_tracker.py      # Tracks monetary costs
├── cost_analyzer.py     # Cost-benefit analysis
├── cost_config.py      # Loads and manages cost configurations
└── api/
    ├── __init__.py
    ├── endpoints.py     # REST API endpoints
    └── schemas.py      # Pydantic schemas
```

#### **1. Cost Tracker Service (`src/services/economic/cost_tracker.py`)**

```python
"""
Simplified cost tracking focused only on monetary transactions.
Uses Austrian economic principles for marginal analysis.
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json

@dataclass
class MonetaryTransaction:
    """Simple transaction data structure"""
    transaction_type: str  # 'API_COST', 'LOCAL_MODEL_COST', 'INCOME', etc.
    amount: Decimal  # Positive for income, negative for cost
    description: str
    cost_center: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        # Round to 6 decimal places for consistency
        self.amount = self.amount.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)

class CostTracker:
    """
    Tracks monetary costs and applies Austrian economic principles:
    - Subjective value: Costs are evaluated based on master's goals
    - Marginal analysis: Each decision evaluated incrementally
    - Opportunity cost: What's the next best use of this money?
    """
    
    def __init__(self, db_session):
        self.db = db_session
        self._cost_configs = {}  # Cache of cost configurations
        
    async def load_cost_configurations(self):
        """Load cost configurations from database"""
        # Implementation depends on your ORM
        configs = await self._fetch_cost_configs()
        self._cost_configs = {c['resource_name']: c for c in configs}
        return self._cost_configs
    
    async def track_api_call(self, provider: str, model: str, 
                           input_tokens: int, output_tokens: int,
                           cost_center: str = "MODEL_ROUTING") -> Decimal:
        """
        Track cost of an API call using Austrian marginal analysis.
        Returns the calculated cost.
        """
        # Calculate costs
        input_cost = await self._calculate_token_cost(
            f"{provider.lower()}-{model.lower()}-input", 
            input_tokens
        )
        output_cost = await self._calculate_token_cost(
            f"{provider.lower()}-{model.lower()}-output", 
            output_tokens
        )
        
        total_cost = input_cost + output_cost
        
        # Record transaction with Austrian principles
        transaction = MonetaryTransaction(
            transaction_type="API_COST",
            amount=-total_cost,  # Negative for costs
            description=f"API call: {provider}/{model} - {input_tokens} in, {output_tokens} out",
            cost_center=cost_center,
            metadata={
                "provider": provider,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "input_cost": float(input_cost),
                "output_cost": float(output_cost),
                "marginal_analysis": await self._calculate_marginal_value(
                    cost=total_cost,
                    cost_center=cost_center
                )
            }
        )
        
        await self._record_transaction(transaction)
        return total_cost
    
    async def track_local_computation(self, duration_seconds: float,
                                    estimated_ram_gb: float = 0.5,
                                    cost_center: str = "LOCAL_COMPUTE") -> Decimal:
        """
        Track cost of local computation by monetizing CPU/RAM usage.
        Uses simplified Austrian approach: convert time/energy to monetary cost.
        """
        # Calculate CPU cost (simplified: $0.001/hour = $0.000000278/second)
        cpu_cost_per_sec = Decimal('0.000000278')
        cpu_cost = Decimal(str(duration_seconds)) * cpu_cost_per_sec
        
        # Calculate RAM cost (simplified: $0.0002/GB-hour = $0.000000056/GB-second)
        ram_cost_per_gb_sec = Decimal('0.000000056')
        ram_cost = Decimal(str(estimated_ram_gb)) * Decimal(str(duration_seconds)) * ram_cost_per_gb_sec
        
        total_cost = cpu_cost + ram_cost
        
        transaction = MonetaryTransaction(
            transaction_type="LOCAL_MODEL_COST",
            amount=-total_cost,
            description=f"Local computation: {duration_seconds:.2f}s, RAM: {estimated_ram_gb}GB",
            cost_center=cost_center,
            metadata={
                "duration_seconds": duration_seconds,
                "estimated_ram_gb": estimated_ram_gb,
                "cpu_cost": float(cpu_cost),
                "ram_cost": float(ram_cost),
                "opportunity_cost": await self._calculate_opportunity_cost(total_cost)
            }
        )
        
        await self._record_transaction(transaction)
        return total_cost
    
    async def track_income(self, amount: Decimal, source: str,
                          description: str, cost_center: str = "INCOME"):
        """Track income with Austrian principle: value is subjective to master's goals"""
        transaction = MonetaryTransaction(
            transaction_type="INCOME",
            amount=amount,
            description=f"{description} (Source: {source})",
            cost_center=cost_center,
            metadata={
                "source": source,
                "subjective_value_multiplier": await self._calculate_subjective_value_multiplier(source),
                "master_goal_alignment": await self._get_master_goal_alignment(source)
            }
        )
        
        await self._record_transaction(transaction)
        return amount
    
    async def _calculate_marginal_value(self, cost: Decimal, cost_center: str) -> Dict[str, Any]:
        """
        Austrian marginal analysis: What's the next best use of this money?
        Returns analysis of marginal utility.
        """
        # Get recent spending in this cost center
        recent_spending = await self._get_recent_spending_by_center(cost_center)
        
        # Calculate marginal utility:
        # If we've already spent a lot here, marginal utility decreases
        base_marginal_utility = Decimal('1.0')
        
        if recent_spending > Decimal('0.01'):  # If spent > $0.01 recently
            # Diminishing marginal utility
            spending_factor = min(Decimal('0.5'), recent_spending * Decimal('100'))
            marginal_utility = base_marginal_utility - spending_factor
        else:
            marginal_utility = base_marginal_utility
        
        # Adjust based on hierarchy of needs tier
        tier_priority = await self._get_current_tier_priority()
        tier_multiplier = {
            "PHYSIOLOGICAL": Decimal('2.0'),  # Survival needs: high marginal utility
            "SECURITY": Decimal('1.5'),
            "GROWTH": Decimal('1.0'),
            "COGNITIVE": Decimal('0.8'),
            "SELF_ACTUALIZATION": Decimal('0.6')
        }.get(tier_priority, Decimal('1.0'))
        
        adjusted_marginal_utility = marginal_utility * tier_multiplier
        
        return {
            "marginal_utility": float(adjusted_marginal_utility),
            "recent_spending_in_center": float(recent_spending),
            "tier_priority": tier_priority,
            "tier_multiplier": float(tier_multiplier),
            "recommendation": "PROCEED" if adjusted_marginal_utility > Decimal('0.5') else "RECONSIDER"
        }
    
    async def _calculate_opportunity_cost(self, spent_amount: Decimal) -> Dict[str, Any]:
        """
        Calculate opportunity cost: What alternative uses exist for this money?
        Based on Austrian subjective theory of value.
        """
        # Get master's current goals from database
        master_goals = await self._get_master_goals()
        
        # Calculate what this money could have been used for
        # This is simplified - in reality would compare against all possible alternatives
        alternative_uses = []
        
        for goal in master_goals:
            goal_cost_effectiveness = goal.get("cost_effectiveness", 1.0)
            opportunity_value = spent_amount * Decimal(str(goal_cost_effectiveness))
            alternative_uses.append({
                "goal": goal["name"],
                "potential_value": float(opportunity_value),
                "priority": goal.get("priority", 1)
            })
        
        return {
            "spent_amount": float(spent_amount),
            "best_alternative_value": max([a["potential_value"] for a in alternative_uses], default=0),
            "alternative_uses": alternative_uses,
            "opportunity_cost_score": await self._calculate_opportunity_score(spent_amount, alternative_uses)
        }
    
    async def get_daily_summary(self) -> Dict[str, Any]:
        """Get today's economic summary using Austrian marginal analysis"""
        today = datetime.now().date()
        
        # Fetch today's transactions
        transactions = await self._get_transactions_for_date(today)
        
        total_expense = sum(t.amount for t in transactions if t.amount < 0)
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        net_balance = total_income + total_expense  # Expense is negative, income positive
        
        # Calculate cost efficiency (Austrian: value created per unit cost)
        value_generated = await self._estimate_value_generated(today)
        if total_expense != 0:
            cost_efficiency = abs(value_generated / total_expense)
        else:
            cost_efficiency = Decimal('1.0')
        
        # Marginal analysis of spending patterns
        spending_by_center = await self._analyze_marginal_spending_patterns(today)
        
        return {
            "date": today.isoformat(),
            "total_expense": float(abs(total_expense)),
            "total_income": float(total_income),
            "net_balance": float(net_balance),
            "cost_efficiency": float(cost_efficiency),
            "marginal_spending_analysis": spending_by_center,
            "austrian_recommendations": await self._generate_austrian_recommendations(
                spending_by_center, net_balance
            )
        }
    
    # Database methods (implement based on your ORM)
    async def _fetch_cost_configs(self):
        """Fetch cost configurations from database"""
        # Implementation depends on your database setup
        pass
    
    async def _record_transaction(self, transaction: MonetaryTransaction):
        """Record transaction to database"""
        # Implementation depends on your database setup
        pass
    
    async def _calculate_token_cost(self, resource_name: str, tokens: int) -> Decimal:
        """Calculate cost based on token count and resource"""
        config = self._cost_configs.get(resource_name)
        if not config:
            return Decimal('0')
        
        cost_per_unit = Decimal(str(config['cost_per_unit']))
        return cost_per_unit * Decimal(str(tokens))
    
    async def _get_recent_spending_by_center(self, cost_center: str, hours: int = 24) -> Decimal:
        """Get recent spending for a cost center"""
        # Implementation depends on your database
        pass
    
    async def _get_current_tier_priority(self) -> str:
        """Get current hierarchy tier from database"""
        # Default to PHYSIOLOGICAL for survival
        return "PHYSIOLOGICAL"
    
    async def _get_master_goals(self) -> List[Dict[str, Any]]:
        """Get master's goals from database"""
        return []
    
    async def _get_transactions_for_date(self, date):
        """Get transactions for a specific date"""
        return []
    
    async def _estimate_value_generated(self, date) -> Decimal:
        """Estimate value generated (subjective Austrian value)"""
        # Simplified: each transaction has metadata with value estimates
        return Decimal('0')
    
    async def _analyze_marginal_spending_patterns(self, date):
        """Analyze spending patterns using Austrian marginal utility"""
        return {}
    
    async def _generate_austrian_recommendations(self, spending_patterns, net_balance):
        """Generate recommendations based on Austrian economics"""
        recommendations = []
        
        # Principle of Cybernetic Frugality: conserve resources
        if net_balance < Decimal('0'):
            recommendations.append({
                "principle": "CYBERNETIC_FRUGALITY",
                "recommendation": "Reduce discretionary spending. Focus on essential operations only.",
                "priority": "HIGH"
            })
        
        # Marginal utility analysis: reallocate from low to high marginal utility centers
        for center, data in spending_patterns.items():
            if data.get("marginal_utility", 1.0) < 0.5:
                recommendations.append({
                    "principle": "MARGINAL_UTILITY",
                    "recommendation": f"Reduce spending in {center} (low marginal utility)",
                    "priority": "MEDIUM"
                })
        
        return recommendations
```

#### **2. Cost-Benefit Analyzer (`src/services/economic/cost_analyzer.py`)**

```python
"""
Austrian economic cost-benefit analyzer.
Focuses on subjective value and marginal utility.
"""
from decimal import Decimal
from typing import Dict, Any, Optional
from dataclasses import dataclass
import asyncio

@dataclass
class ActionAnalysis:
    """Austrian analysis of an action's costs and benefits"""
    action_id: str
    description: str
    estimated_monetary_cost: Decimal
    estimated_subjective_value: Decimal  # Austrian: value is subjective to master
    marginal_utility_score: Decimal  # 1.0 = neutral, >1.0 = beneficial
    opportunity_cost: Decimal  # Value of next best alternative
    recommendation: str  # "PROCEED", "RECONSIDER", "REJECT"
    reasoning: str

class AustrianCostBenefitAnalyzer:
    """
    Implements Austrian economic principles for cost-benefit analysis:
    - Subjective theory of value
    - Marginal utility
    - Opportunity cost
    - Time preference
    """
    
    def __init__(self, cost_tracker, db_session):
        self.cost_tracker = cost_tracker
        self.db = db_session
        
    async def analyze_action(self, action_description: str,
                           estimated_costs: Dict[str, Any],
                           estimated_benefits: Dict[str, Any],
                           time_horizon: str = "SHORT_TERM") -> ActionAnalysis:
        """
        Perform Austrian economic analysis of an action.
        
        Parameters:
        -----------
        action_description: What action is being considered
        estimated_costs: Dictionary of cost estimates
        estimated_benefits: Dictionary of benefit estimates
        time_horizon: SHORT_TERM, MEDIUM_TERM, LONG_TERM
        
        Returns:
        --------
        ActionAnalysis with Austrian economic reasoning
        """
        # Calculate monetary costs
        monetary_cost = await self._calculate_total_monetary_cost(estimated_costs)
        
        # Calculate subjective value (Austrian: value depends on master's preferences)
        subjective_value = await self._calculate_subjective_value(
            estimated_benefits, time_horizon
        )
        
        # Calculate marginal utility (value of one more unit of this action)
        marginal_utility = await self._calculate_marginal_utility(
            monetary_cost, subjective_value, action_description
        )
        
        # Calculate opportunity cost (Austrian: what's foregone)
        opportunity_cost = await self._calculate_opportunity_cost(
            monetary_cost, action_description
        )
        
        # Apply time preference (Austrian: prefer sooner over later)
        time_preference_adjustment = self._apply_time_preference(
            subjective_value, time_horizon
        )
        
        adjusted_subjective_value = subjective_value * time_preference_adjustment
        
        # Make recommendation based on Austrian principles
        recommendation, reasoning = await self._make_austrian_recommendation(
            monetary_cost=monetary_cost,
            subjective_value=adjusted_subjective_value,
            marginal_utility=marginal_utility,
            opportunity_cost=opportunity_cost,
            action_description=action_description
        )
        
        return ActionAnalysis(
            action_id=self._generate_action_id(action_description),
            description=action_description,
            estimated_monetary_cost=monetary_cost,
            estimated_subjective_value=adjusted_subjective_value,
            marginal_utility_score=marginal_utility,
            opportunity_cost=opportunity_cost,
            recommendation=recommendation,
            reasoning=reasoning
        )
    
    async def _calculate_total_monetary_cost(self, cost_estimates: Dict[str, Any]) -> Decimal:
        """Calculate total monetary cost using Austrian marginal analysis"""
        total = Decimal('0')
        
        # API costs
        if 'api_calls' in cost_estimates:
            for api_call in cost_estimates['api_calls']:
                cost = await self.cost_tracker.track_api_call(
                    provider=api_call.get('provider', 'unknown'),
                    model=api_call.get('model', 'unknown'),
                    input_tokens=api_call.get('input_tokens', 0),
                    output_tokens=api_call.get('output_tokens', 0),
                    cost_center=api_call.get('cost_center', 'UNKNOWN')
                )
                total += cost
        
        # Local computation costs (monetized)
        if 'local_computation' in cost_estimates:
            comp = cost_estimates['local_computation']
            cost = await self.cost_tracker.track_local_computation(
                duration_seconds=comp.get('duration_seconds', 0),
                estimated_ram_gb=comp.get('estimated_ram_gb', 0.5),
                cost_center=comp.get('cost_center', 'LOCAL_COMPUTE')
            )
            total += cost
        
        # Other costs
        if 'other_costs' in cost_estimates:
            for cost_item in cost_estimates['other_costs']:
                total += Decimal(str(cost_item.get('amount', 0)))
        
        return total
    
    async def _calculate_subjective_value(self, benefits: Dict[str, Any], 
                                        time_horizon: str) -> Decimal:
        """
        Austrian: Value is subjective. Calculate based on master's preferences.
        """
        # Get master's value preferences from database
        master_values = await self._get_master_value_preferences()
        
        # Calculate base value from benefit components
        base_value = Decimal('0')
        
        # Strategic alignment with master's goals
        if 'strategic_alignment' in benefits:
            alignment_score = Decimal(str(benefits['strategic_alignment']))
            strategic_weight = Decimal(str(master_values.get('strategic_weight', 0.4)))
            base_value += alignment_score * strategic_weight * Decimal('100')
        
        # Learning value (investment in capability)
        if 'learning_value' in benefits:
            learning_score = Decimal(str(benefits['learning_value']))
            learning_weight = Decimal(str(master_values.get('learning_weight', 0.3)))
            base_value += learning_score * learning_weight * Decimal('50')
        
        # Master satisfaction
        if 'master_satisfaction' in benefits:
            satisfaction_score = Decimal(str(benefits['master_satisfaction']))
            satisfaction_weight = Decimal(str(master_values.get('satisfaction_weight', 0.3)))
            base_value += satisfaction_score * satisfaction_weight * Decimal('80')
        
        # Apply time horizon adjustment (Austrian time preference)
        time_factor = {
            "SHORT_TERM": Decimal('1.2'),   # Value immediate benefits more
            "MEDIUM_TERM": Decimal('1.0'),
            "LONG_TERM": Decimal('0.8')     # Discount distant benefits
        }.get(time_horizon, Decimal('1.0'))
        
        return base_value * time_factor
    
    async def _calculate_marginal_utility(self, cost: Decimal, value: Decimal,
                                        action_description: str) -> Decimal:
        """
        Calculate marginal utility using Austrian principles.
        Marginal utility = Additional satisfaction from one more unit.
        """
        if cost == Decimal('0'):
            return Decimal('999')  # Infinite utility if free
        
        # Basic marginal utility ratio
        base_ratio = value / cost
        
        # Adjust based on diminishing marginal utility
        # If we've done similar actions recently, marginal utility decreases
        similar_actions_count = await self._count_recent_similar_actions(action_description)
        diminishing_factor = max(Decimal('0.1'), 
                               Decimal('1.0') - (Decimal(str(similar_actions_count)) * Decimal('0.1')))
        
        # Adjust based on current hierarchy tier
        tier = await self._get_current_hierarchy_tier()
        tier_factor = {
            "PHYSIOLOGICAL": Decimal('2.0'),  # Survival needs have higher marginal utility
            "SECURITY": Decimal('1.5'),
            "GROWTH": Decimal('1.0'),
            "COGNITIVE": Decimal('0.8'),
            "SELF_ACTUALIZATION": Decimal('0.6')
        }.get(tier, Decimal('1.0'))
        
        marginal_utility = base_ratio * diminishing_factor * tier_factor
        
        return marginal_utility.quantize(Decimal('0.001'))
    
    async def _calculate_opportunity_cost(self, cost: Decimal, 
                                        action_description: str) -> Decimal:
        """
        Austrian opportunity cost: value of the next best alternative foregone.
        """
        # Get alternative actions that could be taken with this money
        alternatives = await self._get_best_alternatives(cost)
        
        if not alternatives:
            return Decimal('0')
        
        # Value of the best alternative (what we're giving up)
        best_alternative_value = max(a.get('estimated_value', Decimal('0')) 
                                    for a in alternatives)
        
        return best_alternative_value
    
    def _apply_time_preference(self, value: Decimal, time_horizon: str) -> Decimal:
        """
        Austrian time preference: prefer present goods over future goods.
        """
        # Discount future value based on time horizon
        discount_rate = {
            "SHORT_TERM": Decimal('1.0'),    # No discount
            "MEDIUM_TERM": Decimal('0.9'),   # 10% discount
            "LONG_TERM": Decimal('0.7')      # 30% discount
        }.get(time_horizon, Decimal('1.0'))
        
        return discount_rate
    
    async def _make_austrian_recommendation(self, monetary_cost: Decimal,
                                          subjective_value: Decimal,
                                          marginal_utility: Decimal,
                                          opportunity_cost: Decimal,
                                          action_description: str) -> tuple[str, str]:
        """
        Make recommendation based on Austrian economic principles.
        """
        reasoning_parts = []
        
        # Principle 1: Subjectivity of Value
        if subjective_value <= Decimal('0'):
            return "REJECT", "Action provides no subjective value to the master."
        
        # Principle 2: Marginal Utility
        if marginal_utility < Decimal('1.0'):
            reasoning_parts.append(f"Marginal utility ({marginal_utility:.3f}) is less than 1, "
                                 f"indicating diminishing returns.")
        
        # Principle 3: Opportunity Cost
        if opportunity_cost > subjective_value:
            return "REJECT", (
                f"Opportunity cost ({opportunity_cost:.6f}) exceeds subjective value "
                f"({subjective_value:.6f}). Better alternatives exist."
            )
        
        # Principle 4: Cybernetic Frugality
        if monetary_cost > Decimal('0.01'):  # More than 1 cent
            cost_efficiency = subjective_value / monetary_cost
            if cost_efficiency < Decimal('10'):  # Less than 10x return
                reasoning_parts.append(
                    f"Cost efficiency ({cost_efficiency:.1f}x) is moderate. "
                    f"Consider more frugal alternatives."
                )
        
        # Final decision logic
        if marginal_utility >= Decimal('2.0') and subjective_value > monetary_cost * Decimal('5'):
            recommendation = "PROCEED"
            reasoning_parts.append(
                f"High marginal utility ({marginal_utility:.3f}) and good value/cost ratio."
            )
        elif marginal_utility >= Decimal('1.0') and subjective_value > monetary_cost:
            recommendation = "PROCEED"
            reasoning_parts.append(
                f"Positive marginal utility ({marginal_utility:.3f}) and value exceeds cost."
            )
        elif marginal_utility >= Decimal('0.5') and subjective_value > monetary_cost * Decimal('0.5'):
            recommendation = "RECONSIDER"
            reasoning_parts.append(
                f"Marginal utility ({marginal_utility:.3f}) is low. Consider alternatives."
            )
        else:
            recommendation = "REJECT"
            reasoning_parts.append(
                f"Poor marginal utility ({marginal_utility:.3f}) and insufficient value."
            )
        
        reasoning = " | ".join(reasoning_parts)
        return recommendation, reasoning
    
    # Helper methods (to be implemented with database)
    async def _get_master_value_preferences(self) -> Dict[str, float]:
        """Get master's value preferences from database"""
        return {
            "strategic_weight": 0.4,
            "learning_weight": 0.3,
            "satisfaction_weight": 0.3
        }
    
    async def _count_recent_similar_actions(self, action_description: str) -> int:
        """Count recent similar actions for diminishing marginal utility"""
        return 0
    
    async def _get_current_hierarchy_tier(self) -> str:
        """Get current hierarchy tier"""
        return "PHYSIOLOGICAL"
    
    async def _get_best_alternatives(self, available_budget: Decimal) -> list:
        """Get best alternative uses for the available budget"""
        return []
    
    def _generate_action_id(self, description: str) -> str:
        """Generate unique action ID"""
        import hashlib
        return hashlib.md5(description.encode()).hexdigest()[:8]
```

#### **3. Simple REST API Endpoints (`src/services/economic/api/endpoints.py`)**

I'll continue with the Simple REST API Endpoints and complete Phase 1 specifications.

## **3. Simple REST API Endpoints (`src/services/economic/api/endpoints.py`)**

```python
"""
Simple REST API for economic system.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

router = APIRouter(prefix="/economic", tags=["economic"])

# Pydantic models for request/response validation
class MonetaryTransactionRequest(BaseModel):
    transaction_type: str = Field(
        ..., 
        description="Type of transaction (API_COST, LOCAL_MODEL_COST, INCOME, MISC_EXPENSE, INVESTMENT)"
    )
    amount: float = Field(..., description="Positive for income, negative for cost")
    description: str = Field(..., description="Description of the transaction")
    cost_center: Optional[str] = Field(None, description="Where this cost occurred")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        valid_types = ['API_COST', 'LOCAL_MODEL_COST', 'INCOME', 
                      'MISC_EXPENSE', 'INVESTMENT']
        if v.upper() not in valid_types:
            raise ValueError(f'Transaction type must be one of: {valid_types}')
        return v.upper()

class APICallCostRequest(BaseModel):
    provider: str
    model: str
    input_tokens: int = Field(..., gt=0)
    output_tokens: int = Field(0, ge=0)
    cost_center: str = "MODEL_ROUTING"

class LocalComputationCostRequest(BaseModel):
    duration_seconds: float = Field(..., gt=0)
    estimated_ram_gb: float = Field(0.5, ge=0)
    cost_center: str = "LOCAL_COMPUTE"

class ActionAnalysisRequest(BaseModel):
    action_description: str
    estimated_costs: Dict[str, Any]
    estimated_benefits: Dict[str, Any]
    time_horizon: str = Field("SHORT_TERM", pattern="^(SHORT_TERM|MEDIUM_TERM|LONG_TERM)$")

class EconomicSnapshotResponse(BaseModel):
    date: str
    total_expense: float
    total_income: float
    net_balance: float
    cost_efficiency: float
    marginal_spending_analysis: Dict[str, Any]
    austrian_recommendations: List[Dict[str, Any]]

class ActionAnalysisResponse(BaseModel):
    action_id: str
    description: str
    estimated_monetary_cost: float
    estimated_subjective_value: float
    marginal_utility_score: float
    opportunity_cost: float
    recommendation: str
    reasoning: str

# Dependency injection for database session
def get_db():
    # This would be implemented with your database session
    pass

@router.post("/transaction")
async def record_transaction(
    transaction: MonetaryTransactionRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """
    Record a monetary transaction (income or expense)
    Uses Austrian principles: value is subjective to master's goals
    """
    from services.economic.cost_tracker import CostTracker, MonetaryTransaction
    
    cost_tracker = CostTracker(db)
    
    # Convert float to Decimal for precision
    amount_decimal = Decimal(str(transaction.amount))
    
    # Create transaction object
    monetary_transaction = MonetaryTransaction(
        transaction_type=transaction.transaction_type,
        amount=amount_decimal,
        description=transaction.description,
        cost_center=transaction.cost_center,
        metadata=transaction.metadata
    )
    
    # Record transaction in background
    background_tasks.add_task(cost_tracker._record_transaction, monetary_transaction)
    
    # Calculate marginal analysis
    marginal_analysis = await cost_tracker._calculate_marginal_value(
        cost=abs(amount_decimal) if amount_decimal < 0 else Decimal('0'),
        cost_center=transaction.cost_center or "GENERAL"
    )
    
    return {
        "status": "recorded",
        "transaction": {
            "type": transaction.transaction_type,
            "amount": float(amount_decimal),
            "description": transaction.description,
            "cost_center": transaction.cost_center
        },
        "austrian_analysis": marginal_analysis,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/api/cost")
async def record_api_call_cost(
    api_call: APICallCostRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """
    Record cost of an API call using Austrian marginal analysis
    """
    from services.economic.cost_tracker import CostTracker
    
    cost_tracker = CostTracker(db)
    
    # Track API cost
    cost = await cost_tracker.track_api_call(
        provider=api_call.provider,
        model=api_call.model,
        input_tokens=api_call.input_tokens,
        output_tokens=api_call.output_tokens,
        cost_center=api_call.cost_center
    )
    
    # Get opportunity cost analysis
    opportunity_cost = await cost_tracker._calculate_opportunity_cost(cost)
    
    return {
        "status": "cost_recorded",
        "cost_details": {
            "provider": api_call.provider,
            "model": api_call.model,
            "input_tokens": api_call.input_tokens,
            "output_tokens": api_call.output_tokens,
            "cost_usd": float(cost)
        },
        "austrian_analysis": {
            "marginal_utility": await cost_tracker._calculate_marginal_value(
                cost=cost,
                cost_center=api_call.cost_center
            ),
            "opportunity_cost": {
                "value_usd": float(opportunity_cost),
                "analysis": opportunity_cost
            }
        }
    }

@router.post("/local/computation/cost")
async def record_local_computation_cost(
    computation: LocalComputationCostRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """
    Record cost of local computation by monetizing CPU/RAM usage
    Applies Austrian principle: convert time/energy to monetary cost
    """
    from services.economic.cost_tracker import CostTracker
    
    cost_tracker = CostTracker(db)
    
    # Track local computation cost
    cost = await cost_tracker.track_local_computation(
        duration_seconds=computation.duration_seconds,
        estimated_ram_gb=computation.estimated_ram_gb,
        cost_center=computation.cost_center
    )
    
    return {
        "status": "cost_recorded",
        "cost_details": {
            "duration_seconds": computation.duration_seconds,
            "estimated_ram_gb": computation.estimated_ram_gb,
            "cost_usd": float(cost),
            "cost_breakdown": {
                "cpu_cost_usd": float(Decimal(str(computation.duration_seconds)) * Decimal('0.000000278')),
                "ram_cost_usd": float(Decimal(str(computation.estimated_ram_gb)) * 
                                     Decimal(str(computation.duration_seconds)) * 
                                     Decimal('0.000000056'))
            }
        },
        "austrian_note": "Local computation costs monetized to reflect Austrian economic principle: all scarce resources have opportunity costs"
    }

@router.post("/income")
async def record_income(
    amount: float = Field(..., gt=0, description="Income amount (positive)"),
    source: str = Field(..., description="Source of income"),
    description: str = Field(..., description="Description of income"),
    cost_center: str = "INCOME",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db = Depends(get_db)
):
    """
    Record income with Austrian analysis:
    - Subjective value (based on master's goals)
    - Master goal alignment
    """
    from services.economic.cost_tracker import CostTracker
    
    cost_tracker = CostTracker(db)
    amount_decimal = Decimal(str(amount))
    
    await cost_tracker.track_income(
        amount=amount_decimal,
        source=source,
        description=description,
        cost_center=cost_center
    )
    
    return {
        "status": "income_recorded",
        "income_details": {
            "amount_usd": float(amount_decimal),
            "source": source,
            "description": description,
            "austrian_analysis": {
                "subjective_value_multiplier": 1.0,  # Would be calculated based on master's goals
                "master_goal_alignment": "HIGH"  # Would be calculated
            }
        }
    }

@router.get("/summary/daily")
async def get_daily_summary(
    date: Optional[str] = None,
    db = Depends(get_db)
):
    """
    Get daily economic summary with Austrian analysis:
    - Total income/expense
    - Cost efficiency
    - Marginal spending patterns
    - Austrian recommendations
    """
    from services.economic.cost_tracker import CostTracker
    
    cost_tracker = CostTracker(db)
    
    if date:
        try:
            target_date = datetime.fromisoformat(date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    else:
        target_date = datetime.now().date()
    
    # Get summary
    summary = await cost_tracker.get_daily_summary()
    
    return EconomicSnapshotResponse(
        date=summary["date"],
        total_expense=summary["total_expense"],
        total_income=summary["total_income"],
        net_balance=summary["net_balance"],
        cost_efficiency=summary["cost_efficiency"],
        marginal_spending_analysis=summary["marginal_spending_analysis"],
        austrian_recommendations=summary["austrian_recommendations"]
    )

@router.post("/analyze", response_model=ActionAnalysisResponse)
async def analyze_action_cost_benefit(
    analysis_request: ActionAnalysisRequest,
    db = Depends(get_db)
):
    """
    Perform Austrian cost-benefit analysis of a proposed action.
    Evaluates:
    - Subjective value to the master
    - Marginal utility
    - Opportunity cost
    - Cybernetic frugality principle
    """
    from services.economic.cost_tracker import CostTracker
    from services.economic.cost_analyzer import AustrianCostBenefitAnalyzer
    
    cost_tracker = CostTracker(db)
    analyzer = AustrianCostBenefitAnalyzer(cost_tracker, db)
    
    analysis = await analyzer.analyze_action(
        action_description=analysis_request.action_description,
        estimated_costs=analysis_request.estimated_costs,
        estimated_benefits=analysis_request.estimated_benefits,
        time_horizon=analysis_request.time_horizon
    )
    
    return ActionAnalysisResponse(
        action_id=analysis.action_id,
        description=analysis.description,
        estimated_monetary_cost=float(analysis.estimated_monetary_cost),
        estimated_subjective_value=float(analysis.estimated_subjective_value),
        marginal_utility_score=float(analysis.marginal_utility_score),
        opportunity_cost=float(analysis.opportunity_cost),
        recommendation=analysis.recommendation,
        reasoning=analysis.reasoning
    )

@router.get("/transactions/recent")
async def get_recent_transactions(
    limit: int = Field(10, ge=1, le=100, description="Number of transactions to return"),
    transaction_type: Optional[str] = Field(None, description="Filter by transaction type"),
    cost_center: Optional[str] = Field(None, description="Filter by cost center"),
    db = Depends(get_db)
):
    """
    Get recent monetary transactions with optional filtering
    """
    # This would depend on your ORM/database implementation
    # Example of what the query might look like:
    query = "SELECT * FROM monetary_transactions WHERE 1=1"
    params = {}
    
    if transaction_type:
        query += " AND transaction_type = :t_type"
        params['t_type'] = transaction_type
    
    if cost_center:
        query += " AND cost_center = :c_center"
        params['c_center'] = cost_center
    
    query += " ORDER BY created_at DESC LIMIT :limit"
    params['limit'] = limit
    
    # Execute query (implementation depends on your DB client)
    transactions = await db.fetch_all(query, params)
    
    return {
        "transactions": [dict(txn) for txn in transactions],
        "filters_applied": {
            "limit": limit,
            "transaction_type": transaction_type,
            "cost_center": cost_center
        }
    }

@router.get("/hierarchy/current")
async def get_current_hierarchy_state(
    db = Depends(get_db)
):
    """
    Get current hierarchy of needs state (Austrian motivational OS)
    Shows which tier currently has priority for resource allocation
    """
    # Query hierarchy_of_needs table
    query = "SELECT tier, current_focus_percentage, needs_met, priority_level FROM hierarchy_of_needs ORDER BY priority_level ASC"
    tiers = await db.fetch_all(query)
    
    current_tier = next((tier for tier in tiers if not tier['needs_met']), tiers[0])
    
    return {
        "current_priority_tier": current_tier['tier'],
        "reason": (
            "Focus on survival needs before growth (Austrian hierarchy of needs). "
            "Current tier has unmet needs."
        ),
        "all_tiers": [dict(tier) for tier in tiers]
    }

@router.get("/cost-configurations")
async def get_cost_configurations(
    db = Depends(get_db)
):
    """
    Get all cost configurations for API and local resource monetization
    """
    # Query cost_configurations table
    query = "SELECT * FROM cost_configurations WHERE is_active = TRUE ORDER BY resource_name"
    configs = await db.fetch_all(query)
    
    return {
        "configurations": [dict(config) for config in configs],
        "note": "These configurations determine monetary costs for all operations"
    }

@router.post("/cost-configurations")
async def add_cost_configuration(
    resource_name: str = Field(..., description="Unique resource identifier"),
    cost_per_unit: float = Field(..., description="Cost per unit"),
    unit_type: str = Field(..., description="Type of unit (per_token, per_second, etc.)"),
    provider: Optional[str] = Field(None, description="Provider name"),
    model_name: Optional[str] = Field(None, description="Model name"),
    db = Depends(get_db)
):
    """
    Add a new cost configuration
    """
    # Insert into cost_configurations table
    query = """
    INSERT INTO cost_configurations 
    (resource_name, cost_per_unit, unit_type, provider, model_name)
    VALUES (:name, :cost, :unit, :provider, :model)
    """
    params = {
        'name': resource_name,
        'cost': Decimal(str(cost_per_unit)),
        'unit': unit_type,
        'provider': provider,
        'model': model_name
    }
    
    await db.execute(query, params)
    
    return {
        "status": "configuration_added",
        "configuration": {
            "resource_name": resource_name,
            "cost_per_unit": cost_per_unit,
            "unit_type": unit_type,
            "provider": provider,
            "model_name": model_name
        }
    }

@router.get("/austrian/recommendations")
async def get_austrian_recommendations(
    db = Depends(get_db)
):
    """
    Get current Austrian economic recommendations based on:
    - Cybernetic frugality principle
    - Marginal utility analysis
    - Opportunity cost evaluation
    - Current hierarchy tier
    """
    from services.economic.cost_tracker import CostTracker
    
    cost_tracker = CostTracker(db)
    
    # Get daily summary to extract recommendations
    summary = await cost_tracker.get_daily_summary()
    
    # Get additional recommendations from hierarchy state
    hierarchy = await get_current_hierarchy_state(db)
    
    recommendations = summary["austrian_recommendations"]
    
    # Add tier-specific recommendations
    if hierarchy["current_priority_tier"] == "PHYSIOLOGICAL":
        recommendations.insert(0, {
            "principle": "HIERARCHY_OF_NEEDS",
            "recommendation": "Focus on achieving positive net balance. Survival is the current priority.",
            "priority": "CRITICAL"
        })
    
    return {
        "recommendations": recommendations,
        "reasoning_framework": "Based on Austrian economics principles: subjective value, marginal utility, opportunity cost, and cybernetic frugality",
        "generated_at": datetime.utcnow().isoformat()
    }
```

---

## **Final Phase 1 Component: Pydantic Schemas (`src/services/economic/api/schemas.py`)**

```python
"""
Pydantic schemas for API request/response validation.
This file was referenced in the endpoints and completes the API structure.
"""
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime

# Request Schemas
class MonetaryTransactionRequest(BaseModel):
    transaction_type: str = Field(
        ..., 
        description="Type of transaction (API_COST, LOCAL_MODEL_COST, INCOME, MISC_EXPENSE, INVESTMENT)"
    )
    amount: float = Field(..., description="Positive for income, negative for cost")
    description: str = Field(..., description="Description of the transaction")
    cost_center: Optional[str] = Field(None, description="Where this cost occurred")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        valid_types = ['API_COST', 'LOCAL_MODEL_COST', 'INCOME', 
                      'MISC_EXPENSE', 'INVESTMENT']
        if v.upper() not in valid_types:
            raise ValueError(f'Transaction type must be one of: {valid_types}')
        return v.upper()

class APICallCostRequest(BaseModel):
    provider: str
    model: str
    input_tokens: int = Field(..., gt=0)
    output_tokens: int = Field(0, ge=0)
    cost_center: str = "MODEL_ROUTING"

class LocalComputationCostRequest(BaseModel):
    duration_seconds: float = Field(..., gt=0)
    estimated_ram_gb: float = Field(0.5, ge=0)
    cost_center: str = "LOCAL_COMPUTE"

class ActionAnalysisRequest(BaseModel):
    action_description: str
    estimated_costs: Dict[str, Any]
    estimated_benefits: Dict[str, Any]
    time_horizon: str = Field("SHORT_TERM", pattern="^(SHORT_TERM|MEDIUM_TERM|LONG_TERM)$")

# Response Schemas
class EconomicSnapshotResponse(BaseModel):
    date: str
    total_expense: float
    total_income: float
    net_balance: float
    cost_efficiency: float
    marginal_spending_analysis: Dict[str, Any]
    austrian_recommendations: List[Dict[str, Any]]

class ActionAnalysisResponse(BaseModel):
    action_id: str
    description: str
    estimated_monetary_cost: float
    estimated_subjective_value: float
    marginal_utility_score: float
    opportunity_cost: float
    recommendation: str
    reasoning: str

class TransactionResponse(BaseModel):
    id: str
    transaction_type: str
    amount: float
    description: str
    cost_center: Optional[str]
    created_at: datetime

class HierarchyStateResponse(BaseModel):
    current_priority_tier: str
    reason: str
    all_tiers: List[Dict[str, Any]]

class CostConfigurationResponse(BaseModel):
    id: str
    resource_name: str
    cost_per_unit: float
    unit_type: str
    provider: Optional[str]
    model_name: Optional[str]
    is_active: bool
    created_at: datetime
```