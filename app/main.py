"""
A2A Server for AppFND ProCode Agent using PydanticAI with LiteLLM and MCP Server.
"""

# Standard library imports
import json
import logging
import os

# Initialize auto-instrumentation before importing AI frameworks
from application_foundation.common.telemetry import auto_instrument
auto_instrument()

# Third-party imports
import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from application_foundation.aicore import set_aicore_config

# Local imports
from agent_executor import AppFNDAgentExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_env_var(key: str, default: str = "") -> str:
    """
    Get an environment variable or return a default value.

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        Environment variable value or default
    """
    return os.environ.get(key, default)

logger.info("Setting AICore configuration with Application Foundation SDK")
set_aicore_config()

# Server configuration
HOST = get_env_var("HOST", "0.0.0.0")
PORT = int(get_env_var("PORT", "5000"))

logger.info(f"HOST: {HOST}")
logger.info(f"PORT: {PORT}")


@click.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=5000, help="Port to bind to")
def main(host: str = HOST, port: int = PORT):
    """Start the A2A agent server."""
    logger.info("Starting A2A server")
    logger.info(f"Using HOST: {host}")
    logger.info(f"Using PORT: {port}")

    # Agent capabilities
    capabilities = AgentCapabilities(
        streaming=True,
        pushNotifications=False,
    )

    # Agent skill definition
    skill = AgentSkill(
        id="appfnd-procode-agent",
        name="AppFND ProCode Agent",
        description=(
            "An AI assistant specialized in SAP Application Foundation (AppFND) Toolkit. "
            "Provides documentation, code samples, and guidance for serverless development "
            "on SAP BTP including Object Store, Audit Log, Destination Service, and SDK usage."
        ),
        tags=[
            "appfnd", "application-foundation", "sap-btp", "serverless",
            "object-store", "audit-log", "sdk", "pydantic-ai", "mcp"
        ],
        examples=[
            "How do I get started with Application Foundation?",
            "Generate a sample Node.js serverless application",
            "Show me Object Store code samples",
            "What's the schema for app.yaml?",
            "Show me the Go SDK documentation for Audit Log",
            "Help me migrate my CAP application to Application Foundation",
            "What changed in the latest Python SDK version?",
        ],
    )

    # Agent card (metadata)
    agent_card = AgentCard(
        name="AppFND ProCode Agent",
        description=(
            "An AI-powered assistant for SAP Application Foundation Toolkit. "
            "Helps developers with onboarding, sample application generation, "
            "SDK documentation (Go, Java, Node.js, Python), Object Store, "
            "Audit Log, Destination Service, CAP migration, and app.yaml configuration. "
            "Integrates with AppFND MCP Server for accurate, up-to-date information."
        ),
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=capabilities,
        skills=[skill],
    )

    # Task store for managing conversation state
    task_store = InMemoryTaskStore()

    # Request handler with agent executor
    request_handler = DefaultRequestHandler(
        agent_executor=AppFNDAgentExecutor(),
        task_store=task_store,
    )

    # Create A2A server application
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    logger.info(f"Starting A2A server at http://{host}:{port}")
    logger.info(f"Agent Card: {agent_card.name}")

    # Run the server
    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()