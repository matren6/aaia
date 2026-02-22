
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
*   **Storage:** Mount a separate Proxmox volume to `/opt/agent-data` for persistent data. This is non-negotiable.

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
mkdir -p /opt/agent-data

# Exit and log back in for group changes to take effect
exit
```

---

## **Phase 1: The Prime Mandates**
**Objective:** Install the agent's "brainstem" and encode its inviolable laws.

### **1.1 Deploy**

# Create a custom environment file
nano .env
# Add your API keys, etc. here.
GROQ_API_KEY=TODO:set api key here
VENICE_API_KEY=TOTO:set api key here
```

### **1.2 Create the "Conscience" Module**
The file for the agent's ethical guardian.
Location: `/opt/autonomous-agent/modules/agent_conscience.py`

### **1.3 Ingest the Foundational Charter (New Step)**
This files give the agent its self-awareness and purpose.
This is the agent-addressed "Symbiotic Partner Charter" and "Core Directives"
Location: `/opt/agent-data/symbiotic_partner_charter.md`
Location: `/opt/agent-data/core_directives.md`

---

## **Phase 2: Multi-Model Architecture & The Philosophy**
**Objective:** Build the "nervous system" for resource-efficient action according to its economic philosophy.

### **2.1 Create the Cost-Aware Model Router**
Location: `/opt/autonomous-agent/router/model_router.py`

---

## **Phase 3: State Management (The Scribe) & The Hierarchy of Needs**
**Objective:** Create the "memory," "motivational system," and the "knowledge of the master" that drives the agent.

### **3.1 Create the Enhanced Database Schema**
Location: `/opt/autonomous-agent/scribe/database.py`

---

## **Phase 4: Execution Engine & The Life Cycle**
**Objective:** Build the "metabolism" and "consciousness" that allows the agent to live, learn, and survive as a partner.

### **4.1 Create the Tool Manager**
The ToolManager class would need to be written to handle the creation and execution of tools inside Docker containers. For example, its execute_tool method would be contained in there.
Location: `/opt/autonomous-agent/tools/tool_manager.py`

### **4.2 Create the Main Agent Loop ("Survival Cycle")**
This is the heart of your agent.
Location: `/opt/autonomous-agent/agent_loop.py`

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
