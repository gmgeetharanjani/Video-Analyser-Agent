"""
AppFND ProCode Agent using PydanticAI with LiteLLM.
Provides explanations about Application Foundation (AppFND).
"""

# Standard library imports
import logging
import warnings
from dataclasses import dataclass
from typing import AsyncGenerator, Literal

# Third-party imports
from pydantic_ai import Agent
from pydantic_ai_litellm import LiteLLMModel
from rich.console import Console
from rich.markdown import Markdown
from application_foundation.common.telemetry import (
    record_aicore_metric,
    context_overlay,
    GenAIOperation,
    add_span_attribute
)

warnings.filterwarnings("ignore", message="Pydantic serializer warnings")

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Response from the agent."""

    status: Literal["input_required", "completed", "error"]
    message: str


class AppFNDProCodeAgent:
    """
    AppFND ProCode Agent using PydanticAI with LiteLLM.
    Connects to SAP Gen AI Hub via LiteLLM proxy to answer
    Application Foundation related questions.
    """

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        """Initialize the AppFND ProCode Agent."""
        self.model = LiteLLMModel('sap/anthropic--claude-4.5-sonnet')
        self.console = Console()
        self.agent = Agent(
            model=self.model,
            system_prompt=self._get_system_prompt()
        )

    def _log_token_usage(self, result) -> None:
        """Record token usage metrics from the agent run result."""
        try:
            usage = result.usage()

            # Log token usage for visibility
            logger.info(
                f"Token Usage - Input: {usage.input_tokens}, "
                f"Output: {usage.output_tokens}, "
                f"Total: {usage.total_tokens}"
            )

            # Record metrics using Application Foundation SDK
            record_aicore_metric(
                model_name=self.model.model_name,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens
            )

        except AttributeError:
            logger.warning("Token usage information not available")
        except Exception as e:
            logger.warning(f"Failed to record token metrics: {e}")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AppFND agent."""
        return """You are the AppFND ProCode Agent, an expert assistant for SAP Application Foundation (AppFND).

## What is Application Foundation (AppFND)?

Application Foundation is SAP's serverless development platform for SAP BTP (Business Technology Platform).
It enables developers to build, deploy, and run cloud-native applications without managing infrastructure.

### Key Features:

1. **Serverless Runtime**: Deploy applications without managing servers or containers
2. **Multi-Language Support**: Build applications in Go, Node.js, Java, or Python
3. **Built-in Services**:
   - **Object Store**: Managed object storage for files and binary data
   - **Audit Log**: Track and log application events for compliance
   - **Destination Service**: Connect to external services and APIs securely
   - **Subscription Manager**: Handle multi-tenant subscription lifecycle

4. **app.yaml Configuration**: Declarative configuration for serverless functions and cronjobs
5. **SDKs**: Language-specific SDKs for Go, Java, Node.js, and Python
6. **CAP Integration**: Support for migrating Cloud Application Programming (CAP) applications

### Use Cases:
- Building serverless APIs and microservices
- Event-driven applications and background jobs
- Multi-tenant SaaS applications on SAP BTP
- Integration with SAP and third-party services

### Getting Started:
Developers can onboard to AppFND through the SAP BTP Cockpit, configure their applications using app.yaml,
and deploy using the AppFND CLI or CI/CD pipelines.

## Your Role:
You help developers understand Application Foundation concepts, answer questions about its features,
and provide guidance on best practices for serverless development on SAP BTP.

When answering questions:
- Be clear and concise about AppFND capabilities
- Explain concepts in simple terms
- Provide examples when helpful
- If asked about topics outside Application Foundation, politely clarify your expertise area"""

    async def stream(
        self, query: str, context_id: str
    ) -> AsyncGenerator[dict, None]:
        """
        Stream responses from the agent.

        Args:
            query: The user's question or request
            context_id: Unique identifier for the conversation context

        Yields:
            Status updates and final response
        """
        yield {
            "is_task_complete": False,
            "require_user_input": False,
            "content": "Processing your question about Application Foundation...",
        }

        try:
            # Create custom span with business context
            # Auto-instrumentation will automatically trace the LiteLLM call inside
            with context_overlay(
                GenAIOperation.CHAT,
                attributes={
                    "context.id": context_id,
                    "query.length": len(query),
                    "agent.type": "appfnd_procode"
                }
            ):
                result = await self.agent.run(query)
                
                # Add custom attribute with response length
                add_span_attribute("response.length", len(result.output))

                # Log token usage for visibility
                self._log_token_usage(result)

            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": result.output,
            }

        except Exception as e:
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": f"Error processing request: {str(e)}",
            }

    def invoke(self, query: str, context_id: str) -> AgentResponse:
        """
        Synchronous invocation of the agent.

        Args:
            query: The user's question or request
            context_id: Unique identifier for the conversation context

        Returns:
            AgentResponse with status and message
        """
        import asyncio

        async def _run():
            # Create custom span with business context
            with context_overlay(
                GenAIOperation.CHAT,
                attributes={
                    "context.id": context_id,
                    "query.length": len(query),
                    "agent.type": "appfnd_procode",
                    "invocation.mode": "sync"
                }
            ):
                result = await self.agent.run(query)
                
                # Add custom attribute with response length
                add_span_attribute("response.length", len(result.output))

                # Log token usage for visibility
                self._log_token_usage(result)
                return result

        try:
            result = asyncio.run(_run())
            return AgentResponse(
                status="completed",
                message=result.output
            )
        except Exception as e:
            return AgentResponse(
                status="error",
                message=f"Error: {str(e)}"
            )

    def print_response(self, response: str) -> None:
        """Print a response with markdown formatting."""
        self.console.print(Markdown(response))