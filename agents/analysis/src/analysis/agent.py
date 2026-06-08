"""A2A wiring for the analysis agent: Agent, Executor (Pattern B), RequestHandler."""

import logging

from a2a.helpers import new_task_from_user_message, new_text_status_update_event, new_text_artifact_update_event
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, TaskState

from analysis.graph import AGENT_NAME, build_graph

logger = logging.getLogger(__name__)


class AnalysisAgent:
    """Wraps the compiled LangGraph graph."""

    def __init__(self) -> None:
        self._graph = build_graph()

    def invoke(self) -> str:
        result = self._graph.invoke()
        return result["name"]


class AnalysisExecutor(AgentExecutor):
    """Pattern B: task lifecycle stream — emits Task → working → completed."""

    def __init__(self, agent: AnalysisAgent) -> None:
        self._agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task or new_task_from_user_message(context.message)
        await event_queue.enqueue_event(task)

        await event_queue.enqueue_event(
            new_text_status_update_event(
                task_id=task.id,
                context_id=task.context_id,
                state=TaskState.TASK_STATE_WORKING,
                text="Processing...",
            )
        )

        # TODO: pass context.message to the graph
        result = await self._agent.invoke(context.message)
        logger.info("agent '%s'", result["name"])

        await event_queue.enqueue_event(
            new_text_artifact_update_event(
                task_id=task.id,
                context_id=task.context_id,
                name='result',
                text=result,
            )
        )

        await event_queue.enqueue_event(
            new_text_status_update_event(
                task_id=task.id,
                context_id=task.context_id,
                state=TaskState.TASK_STATE_COMPLETED,
                text='Done!',
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError

class AnalysisRequestHandler:
    """Wires the executor, task store, and card into a DefaultRequestHandler."""

    def __init__(self, agent_card: AgentCard) -> None:
        self.request_handler = DefaultRequestHandler(
            agent_executor=AnalysisExecutor(AnalysisAgent()),
            task_store=InMemoryTaskStore(),
            agent_card=agent_card,
        )
