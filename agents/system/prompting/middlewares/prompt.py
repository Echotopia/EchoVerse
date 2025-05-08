from cogni import mw, Message, Tool

@mw
def prompt(ctx: dict[str, any], input_str: str):
    """
    Create a prompt by appending user input to the agent's base prompt.
    
    Args:
        ctx: The context dictionary containing the agent
        input_str: The user input string
        
    Returns:
        The conversation with the user input appended
    """
    return ctx['agent'].base_prompt + Message(role='user', content=input_str)


@mw
def prompt_histo(ctx: dict[str, any], input_str: str):
    """
    Create a prompt using the agent's history and base prompt.
    
    Args:
        ctx: The context dictionary containing the agent and args
        input_str: The user input string
        
    Returns:
        The conversation with history and user input
    """
    base_prompt = ctx['agent'].base_prompt
    ctx['user_input'],*_ = ctx['args']

    # Get the last 12 messages from history
    histo = ctx['agent'].histo[-12:]
    
    # Create template with base prompt, history and user input
    ret = Tool['tpl']((base_prompt+histo) + Message('user','{user_input}'), **ctx)
    
    # Append the last message to history
    ctx['agent'].append_histo(ret[-1])
    
    return ret
