# Joule Setup Guide for SAP BTP

This guide provides step-by-step instructions for setting up Joule (SAP's AI assistant) in your SAP BTP subaccount, including support for **Bring Your Own Agents (BYOA)**.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [BTP Resources Required](#btp-resources-required)
4. [Setup Steps - BTP Configuration](#setup-steps---btp-configuration)
5. [Setup Steps - Agent Integration](#setup-steps---agent-integration)
6. [Joule CLI Commands](#joule-cli-commands)
7. [Technical References](#technical-references)

---

## Overview

**Joule** is SAP's AI-powered assistant that integrates with SAP applications. With **BYOA (Bring Your Own Agents)**, you can create, host, and maintain your own agents that integrate with Joule using the **Agent-to-Agent (A2A) protocol**.

### Key Concepts

- **BYOA**: Capability to deploy custom agents that work alongside Joule
- **A2A Protocol**: Agent-to-Agent communication protocol (version 0.3.0, JSON-RPC based)
- **DTA Schema**: Digital Assistant schema (minimum version 3.27.0 for BYOA support)
- **Capabilities**: Modular functions that extend Joule's abilities

---

## Prerequisites

Before starting, ensure you have:

1. **SAP BTP Global Account** with entitlements for:
   - Joule
   - SAP Identity Authentication Service (IAS)
   - Destination Service

2. **SAP Identity Authentication Service (IAS)** tenant configured

3. **Administrator access** to your BTP subaccount

4. **Node.js** (version 18 or higher) for Joule CLI

5. **Understanding of**:
   - SAP BTP Cockpit
   - Service instances and subscriptions
   - OAuth 2.0 authentication

---

## BTP Resources Required

The following BTP resources must be configured in your subaccount:

### 1. SAP Identity Authentication Service (IAS)

- Required for user authentication
- Must be configured as a trusted identity provider in your subaccount
- Users must exist in IAS to access Joule

### 2. Joule Internal Production Subscription

- Application subscription in BTP Cockpit
- Service: `das-application-canary` 
- Plan: `development`
- Provides access to the Joule UI

### 3. Joule Service Instance

- Service instance for API access
- Service: `das-service-canary`
- Plan: `designer`
- Provides credentials for Joule CLI

### 4. Destination Service

- Required for connecting to external agents (BYOA)
- Used to configure system aliases for agent endpoints

### 5. Role Collections

Essential role collections for Joule:

| Role Collection | Description |
|----------------|-------------|
| `capability_developer` | Access to Joule Web Client, compile Design Time Artifacts (DTA), and generate Runtime Artifacts (RTA) |
| `capability_release_admin` | Deploy and configure runtime artifacts in the Joule environment |
| `end_user` | Access Joule standalone Web Client with Single Sign-On (SSO) |

> **Important:** To deploy capabilities using the Joule CLI, you must have **both** `das_release_admin` and `das_developer` roles assigned in SAP BTP.

---

## Setup Steps - BTP Configuration

### Step 1: Configure Trust with SAP IAS

1. Navigate to **BTP Cockpit** → **Security** → **Trust Configuration**
2. Click **Establish Trust**
3. Select your **SAP IAS tenant**
4. If you're using AppFnd, you can use the IAS `appfndconhosdevmt.accounts400.ondemand.com`. You may need to request access to this IAS tenant.
5. Complete the trust configuration wizard
6. Verify the trust status shows as **Active**

### Step 2: Create a Destination Service Instance

1. Go to **BTP Cockpit** → **Services** → **Service Marketplace**
2. Search for **"Destination"**
3. Click on the Destination tile
4. Select **Create**
5. Choose the appropriate plan (e.g., `lite`)
6. Provide an instance name (e.g., `destination-instance`)
7. Click **Create**

### Step 3: Create Joule Subscription

1. Go to **BTP Cockpit** → **Services** → **Service Marketplace**
2. Search for **"Joule Internal Production"**
3. Click on the Joule tile
4. Select **Create**
5. Choose the plan: `development`
6. Wait for the subscription to be created (status: **Subscribed**)

### Step 4: Create Joule Service Instance

1. Go to **BTP Cockpit** → **Services** → **Instances and Subscriptions**
2. Click **Create** (top right corner)
3. Configure:
   - **Service**: Joule
   - **Plan**: designer
   - **Instance Name**: e.g., `joule-instance`
4. Click **Create**
5. After creation, create a **Service Key**:
   - Click on the instance
   - Go to **Bindings** tab
   - Click **Create**
   - Name it: e.g., `joule-key`

### Step 5: Assign Roles to Users

1. Go to **BTP Cockpit** → **Security** → **Role Collections**
2. Create a new Role Collection named **Joule Extensibility Developer**
3. Assign the required roles to your collection:
   - Select **Security** → **Role Collections** → **Joule Extensibility Developer** → Click **Edit**
   - In the **Role Name** field, use the value help to add the following roles:
     - `capability_developer`
     - `capability_release_admin`
     - `end_user`
   - Click **Add** for each role, then **Save** the changes
4. Finally, add your users to this collection:
   - The users must exist in the Identity Provider that was configured in the trust setup (e.g., `appfndconhosdevmt.accounts400.ondemand.com`)

> **Note:** At this point, you have completed the BTP configuration required for your application to work. Now let's proceed to integrate your agent with Joule.

---

## Setup Steps - Agent Integration

### Step 1: Create a Destination for Your Agent

At this point, you should already have the agent you want to integrate with Joule configured and running on Kyma.

1. Get the access URL of your agent (e.g., `sample-procode-agent.eee0862.stage.kyma.ondemand.com`)
2. Navigate to **Connectivity** → **Destinations**
3. Click **Create Destination** and select "Create from scratch"
4. Configure the destination:
   - **Name**: Use the name specified in your capability YAML (e.g., `APPFND_AGENT`)
   - **URL**: Enter your agent's endpoint URL
5. If you're using JWT authentication, add the necessary secrets so Joule can communicate with your agent

### Step 2: Install Joule CLI

Install the Joule CLI globally using npm:

```bash
npm install -g @sap/joule-cli
```

Verify the installation:

```bash
joule --version
```

### Step 3: Login to Joule CLI

1. Get credentials from your Joule service key (created in Step 4 of BTP Configuration)

2. Login using:

```bash
joule login -a <authurl> --sso-passcode
```

3. When prompted, enter:
   - **URL**: The Joule service URL from your service key
   - **Client ID**: From service key credentials
   - **Client Secret**: From service key credentials

4. Alternatively, set environment variables:

```bash
export JOULE_URL=<your-joule-url>
export JOULE_CLIENT_ID=<your-client-id>
export JOULE_CLIENT_SECRET=<your-client-secret>
```

### Step 4: Compile and Deploy Capability

In this step, you will deploy your agent's capabilities and tell Joule which Destination to use for communication.

#### Deploy the Capability

```bash
joule deploy --compile ./joule
```

Options:
- `--compile`: Compiles the Design Time Artifact (DTA) before deploying

### Step 5: Test the Assistant

From this point, you can run `joule list`. If everything up to here worked correctly, you will see your agent in the list:

```bash
joule list
```

Then you can launch your assistant to test the application. This will open a page in your browser pointing to Joule, which will use your agent:

```bash
joule launch appfnd_procode_agent
```

---

## Joule CLI Commands

| Command | Description |
|---------|-------------|
| `joule login` | Authenticate with Joule service |
| `joule compile <path>` | Compile DTA files without deploying |
| `joule deploy --compile <path>` | Compile and deploy capabilities |
| `joule list` | List all deployed capabilities |
| `joule delete <name>` | Delete a deployed capability |
| `joule launch <name>` | Open Joule in browser with specific assistant |

---

## Technical References

### A2A Protocol

- **Version**: 0.3.0
- **Specification**: https://a2a-protocol.org/v0.3.0/specification/
- **Format**: JSON-RPC based communication

### DTA Schema

- **Minimum Version**: 3.27.0 (for BYOA support)
- **Files**:
  - `da.sapdas.yaml`: Digital Assistant definition
  - `capability.sapdas.yaml`: Capability configuration
  - `functions/*.yaml`: Function definitions
  - `scenarios/**/*.yaml`: Scenario definitions

### System Alias Configuration

In `capability.sapdas.yaml`, configure the system alias for BTP destinations:

```yaml
systemAlias:
  destination: "my-agent-destination"
  authenticationType: "OAuth2ClientCredentials"
```

### Project Structure (BYOA)

```
joule/
├── da.sapdas.yaml           # Digital Assistant definition
├── a2a/
│   ├── capability.sapdas.yaml    # Capability configuration
│   ├── capability_context.yaml   # Context for capability
│   ├── functions/
│   │   └── agent.yaml            # Function definitions
│   └── scenarios/
│       └── myagent/
│           └── myagent.yaml      # Scenario definitions
└── *.daar                        # Compiled capability file
```

---

## Additional Resources

- [SAP Joule Documentation](https://help.sap.com/docs/joule)
- [Joule Development Guide](https://help.sap.com/docs/joule/joule-development-guide/what-s-new-for-joule-internal)
- [SAP BTP Documentation](https://help.sap.com/docs/btp)
- [A2A Protocol Specification](https://a2a-protocol.org/)
- [SAP Community - Joule](https://community.sap.com/topics/joule)

---

*Last updated: January 2026*
