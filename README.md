# A2A Agent Template

[![A2A Protocol](https://img.shields.io/badge/A2A%20Protocol-0.3-blue?style=flat)](https://github.com/google/A2A)
[![LangChain](https://img.shields.io/badge/LangChain-LangGraph-orange?style=flat)](https://langchain-ai.github.io/langgraph/)
[![SAP Joule](https://img.shields.io/badge/SAP%20Joule-Ready-green?style=flat)](https://help.sap.com/docs/joule)

> 🚀 **[Use this template](https://github.tools.sap/app-fnd-templates/a2a-agent-template/generate)** to create your own A2A agent.

Build AI agents that integrate with **SAP Joule** using the **A2A (Agent-to-Agent) protocol**.

## Stack

| Component | Purpose |
|-----------|---------|
| **LangChain + LangGraph** | Agent framework & workflows |
| **LiteLLM** | LLM gateway (SAP AI Core) |
| **A2A SDK** | Protocol implementation |

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Configure (or use AppFND secrets volume)
export AICORE_CLIENT_ID="..."
export AICORE_CLIENT_SECRET="..."
export AICORE_AUTH_URL="..."
export AICORE_BASE_URL="..."
export AICORE_RESOURCE_GROUP="..."

# Run
python app/main.py --port 5000
```

```bash
# Docker
docker build -t a2a-agent .
docker run -p 5000:5000 --env-file .env a2a-agent
```

## Customization

### 1. Agent Metadata (`app/main.py`)

```python
AGENT_NAME = "my_agent"
AGENT_DESCRIPTION = "What my agent does"
AGENT_TAGS = ["tag1", "tag2"]
AGENT_EXAMPLES = ["Example query 1", "Example query 2"]
```

### 2. Agent Logic (`app/agent.py`)

```python
SYSTEM_PROMPT = """Your agent's personality and instructions"""

@tool
def my_tool(param: str) -> str:
    """Tool description"""
    return "result"
```

### 3. Joule Config (`joule/`)

Update YAML files to match your agent's name and capabilities.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  SAP Joule   │────▶│  A2A Agent   │────▶│ SAP AI Core  │
│ Orchestrator │     │  (this repo) │     │   (LiteLLM)  │
└──────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────▼───────┐
                    │ Custom Tools │
                    └──────────────┘
```

## Project Structure

```
├── app/
│   ├── main.py           # A2A server + ORD endpoint (/agent-card)
│   ├── agent.py          # LangChain agent implementation
│   └── agent_executor.py # A2A executor bridge
├── joule/                # Joule deployment configs
├── Dockerfile
└── requirements.txt
```

## Joule Deployment

📖 See [docs/joule-setup-guide.md](docs/joule-setup-guide.md) for full BTP setup guide.

### Prerequisites

1. **BTP Subaccount** with:
   - Joule subscription (`das-application-canary`, plan: `development`)
   - Joule service instance (`das-service-canary`, plan: `designer`)
   - Destination pointing to your deployed agent
   - Roles: `capability_developer`, `capability_release_admin`

2. **Service Key** from your Joule instance (contains auth credentials)

### Create Destination

Your agent must be accessible via a BTP Destination. Create one in:

**BTP Cockpit → Connectivity → Destinations → New Destination**

| Field | Value |
|-------|-------|
| **Name** | `SAMPLE_AGENT` (must match `system_aliases` in `capability.sapdas.yaml`) |
| **Type** | `HTTP` |
| **URL** | `https://your-agent.kyma.ondemand.com` (your deployed agent URL) |
| **Proxy Type** | `Internet` |
| **Authentication** | `NoAuthentication` (A2A uses JWT in headers) |

Click **Save** → **Check Connection** (should return 200 OK).

> **Note:** The destination name must match the `system_aliases` configured in `joule/a2a/capability.sapdas.yaml`.

### Get Joule Credentials

1. BTP Cockpit → Services → Instances and Subscriptions
2. Click on your Joule instance → Service Keys → Create/View
3. Copy values from the JSON:

```json
{
  "uaa": {
    "url": "https://<subaccount>.authentication.<region>.hana.ondemand.com",  // <authurl>
    "clientid": "sb-xxxxx",
    "clientsecret": "xxxxx"
  }
}
```

### Deploy

```bash
# Install Joule CLI (requires Node.js 18+)
npm install -g @sap/joule-cli

# Login with SSO (opens browser)
joule login -a <authurl> --sso-passcode

# Compile and deploy the joule/ folder
joule deploy --compile ./joule

# Verify deployment
joule list

# Test in browser
joule launch sample_agent
```

### What gets deployed

The `joule/` folder contains Joule capability configs that tell Joule how to communicate with your agent:

```
joule/
├── da.sapdas.yaml              # Digital Assistant definition
└── a2a/
    ├── capability.sapdas.yaml  # Capability + Destination alias
    ├── functions/sample_agent.yaml
    └── scenarios/sample/sample.yaml
```

## Resources

- [AppFND Agent Runtime Docs](https://pages.github.tools.sap/application-foundation/agent-documentation/#runtime)
- [A2A Protocol Spec](https://github.com/google/A2A)
- [SAP Joule Docs](https://help.sap.com/docs/joule)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
