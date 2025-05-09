import logging
import inspect
from cogni import Agent, tool, Tool, State

logger = logging.getLogger(__name__)

@tool
def talk_to_agent(content, agent_name):
    from cogni import ES
    logger.info(f"[talk_to_agent] Agent: {agent_name}, Content: {content!r}")
    # capture a concise call stack (skip current frame, take next 4)
    stack = inspect.stack()[1:5]
    stack_str = " -> ".join(
        f"{frame.function}({frame.filename}:{frame.lineno})" for frame in stack
    )
    logger.info(f"[talk_to_agent] Call stack: {stack_str}")
    parent = State['exec']
    try:
        parent = Agent.last_active
        ES.emit('talk_to_agent', {
            "parent": parent,
            "name":agent_name
        })
        result = Agent[agent_name](content)
        ES.emit('talk_to_agent_done', {
            "parent": parent,
            "name":agent_name
        })
        Agent.last_active = parent
        
        logger.info(f"[talk_to_agent] Result from {agent_name}: {result!r}")
        return result
    except Exception:
        logger.exception(f"[talk_to_agent] Exception in agent {agent_name}")
        raise
