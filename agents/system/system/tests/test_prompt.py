from cogni import Agent

def test_prompt(): 
    """Test the basic prompt middleware functionality."""
    # Create an agent with the prompt middleware
    Agent('prompt_test_agent','prompt')
    
    # Test that the agent correctly processes the input
    assert 'ok'==Agent['prompt_test_agent']('aa')[1].content

def test_prompt_histo():
    """Test the prompt_histo middleware that maintains conversation history."""
    # Set up agent with prompt_histo middleware
    agent_name = 'prompt_test_histo_agent'
    middleware_name = 'prompt_histo'
    Agent(agent_name, middleware_name)
    
    # Test that the conversation history is correctly maintained
    conv = Agent[agent_name]('Hi')
    assert conv[-1].content == 'Hi'
