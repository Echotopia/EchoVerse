import os
import random
from openai import OpenAI
from cogni import tool, Conversation, Tool, State
from rich import print
import requests



@tool
def llm(conversation: Conversation) -> str:
    """
    Process a conversation through an LLM model with streaming support.
    
    Args:
        conversation: The conversation to process
        model: The model to use for processing
        
    Returns:
        The generated response as a string
    """
    from cogni import Stream, ES
    tpl = Tool['tpl_tool']
    conversation = tpl(conversation)
    DEBUG = State['CONF']['DEBUG']

    print(conversation)
    if DEBUG:
        print(conversation)
        with open('last_conv.txt',"w") as f: 
            f.write(str(conversation))
        if input('go?').strip() == 'q':
            quit()
    
    
    if DEBUG:
        print('waiting for validation')
        State['agentTrace']['paused'] = True
        State['agentTrace']['conv'] = conversation.openai()
        #while State['agentTrace']['paused']:
        #    State.reset_cache()
        #    print('.',end='')
        
        
    

    client = OpenAI(
          #base_url="https://openrouter.ai/api/v1",
          #api_key=os.getenv('OPENROUTER_API_KEY')
        api_key=os.getenv('OPENAI_API_KEY')
    ) 

    # Create the completion
    response = client.chat.completions.create(
        model=conversation.llm,
        messages=conversation.openai(),
        max_tokens=32000,
        temperature=.01,
        stream=True
    )

    # Process the streaming response
    msg = ''
    print('\n\n[red]Stream[green i]\n\n')
    last_edit_success = True
    print('_________________')
    for message in response:
        mm = message.choices[0].delta.content
        if mm:
            print(f"[green i]{mm}", end='')
            msg += mm
        Stream.stream = msg
    print('\n\n_______[green on blue b]END_STREAM[/]________\n\n')
    #print(msg)
    DEBUG and input('continue ?')
    return msg


@tool
def llm_no_stream(conversation: Conversation, model: str = 'o1-mini') -> str:
    """
    Process a conversation through an LLM model without streaming.
    
    Args:
        conversation: The conversation to process
        model: The model to use for processing
        
    Returns:
        The generated response as a string
    """
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model=model,
        messages=conversation.openai(),
    )

    return response.choices[0].message.content
