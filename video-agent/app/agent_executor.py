"""
A2A Agent Executor for the Video Analyzer Agent.
Handles A2A protocol integration and task management.
"""

import logging
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    InvalidParamsError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError
try:
    from agent import VideoAnalyzerAgent
except ImportError:
    from agent_local import VideoAnalyzerAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoAnalyzerExecutor(AgentExecutor):
    """A2A executor that bridges the A2A protocol with the VideoAnalyzerAgent."""

    def __init__(self, agent: VideoAnalyzerAgent):
        """
        Initialize the agent executor.
        
        Args:
            agent: VideoAnalyzerAgent instance with video context
        """
        self.agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute the agent and stream results back via A2A protocol.
        """
        error = self._validate_request(context)
        if error:
            raise ServerError(error=InvalidParamsError())

        query = context.get_user_input()
        task = context.current_task

        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            async for item in self.agent.stream(query, task.context_id):
                is_task_complete = item['is_task_complete']
                require_user_input = item['require_user_input']
                content = item.get('content', '')

                if not is_task_complete and not require_user_input:
                    # Working status update
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(content, task.context_id, task.id)
                    )
                elif require_user_input:
                    # Agent requests more input
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(content, task.context_id, task.id),
                        final=True
                    )
                    break
                else:
                    # Completed: add artifact and complete task
                    await updater.add_artifact(
                        [Part(root=TextPart(text=content))],
                        name='agent_result'
                    )
                    await updater.complete()
                    break

        except Exception as e:
            logger.exception("Error while executing agent")
            raise ServerError(error=InternalError()) from e

    def _validate_request(self, context: RequestContext) -> bool:
        """Validate request. Return False for no error."""
        return False

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel a running task."""
        raise ServerError(error=UnsupportedOperationError())