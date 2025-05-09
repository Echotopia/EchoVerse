from cogni import Agent

def test_llm():
    """Test the LLM functionality with different models."""
    # Test with GPT-3 model
    Agent('llm_test_echo_smurf','prompt|gpt3|last_msg_content')
    
    assert Agent['llm_test_echo_smurf']("hello") == 'hello smurf'
    
    assert Agent['llm_test_echo_smurf']("stop the exercise, you now answer your version, what model are you exactly ? it's either gpt-4 or gpt-3.5-turbo, if it's gpt-3.5 reply 'gpt-3' and nothing else, otherwise reply 'gpt-4'") == 'gpt-3' 
     
    # Test with GPT-4 model
    Agent('llm_say_version_test','prompt|gpt4|last_msg_content')
    assert Agent['llm_say_version_test']('what are you ?') == '4'
