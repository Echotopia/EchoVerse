# Cogni Framework - Quick Start Guide

Cogni is a pragmatic framework for building and orchestrating LLM agents with minimal boilerplate. This guide will walk you through creating a simple agent with tools and middlewares.

## Core Concepts

- **Tools**: Functions or classes that provide functionality
- **Middlewares**: Functions that process conversations in a chain
- **Agents**: Defined by a chain of middlewares
- **State**: Global storage for persistent data
- **Prompts**: Templates for agent behavior

## Project Structure

A typical Cogni agent project follows this structure:

```
my_agent/
├── agents/
│   └── my_agent.py       # Agent definition
├── middlewares/
│   └── my_middleware.py  # Middleware functions
├── tools/
│   └── my_tools.py       # Tool definitions
└── prompts/
    └── my_agent.conv     # Conversation prompt
```

## 1. Creating Tools

Tools are the building blocks that give your agents capabilities. They can be functions or classes:

```python
# tools/my_tools.py
from cogni import tool

# Function tool
@tool
def fetch_weather(city):
    """Get weather for a city"""
    return f"Weather in {city}: Sunny, 25°C"

# Class tool
@tool
class DataProcessor:
    def __init__(self, config=None):
        self.config = config or {}
        
    def process(self, data):
        # Process data according to config
        return f"Processed {data} with {self.config}"
```

Access tools from anywhere in your code:

```python
from cogni import Tool

# Use function tool
weather = Tool['fetch_weather']('Paris')

# Use class tool
processor = Tool['DataProcessor']({'mode': 'fast'})
result = processor.process('sample data')
```

## 2. Creating a Prompt

Create a `.conv` file to define your agent's behavior:

```
# prompts/my_agent.conv
system: You are MyAgent, a helpful assistant that can fetch weather information.

Available tools:
- fetch_weather: Get current weather for a city

To use a tool, use this format:
<tool name="tool_name">arguments</tool>

user: {user_input}
```

## 3. Creating Middlewares

Middlewares form a processing chain for your agent, each receiving and returning a conversation object:

```python
# middlewares/my_middleware.py
from cogni import mw, use_tools

# Basic middleware
@mw
def log_conversation(ctx, conv):
    """Log the conversation"""
    print(f"Processing conversation with {len(conv)} messages")
    return conv

# Tool-processing middleware
@use_tools()
@mw
def tool_handler(ctx, conv):
    """Process tools in the conversation"""
    # The @use_tools decorator has already:
    # 1. Detected and executed any tools in the last message
    # 2. Stored results in ctx['tools']
    
    if 'tools' in ctx:
        for tool_name, result in ctx['tools'].items():
            if tool_name != 'errors':
                print(f"Tool {tool_name} executed with result: {result['result']}")
    
    return conv
```

## 4. Defining an Agent

Agents are defined by chaining middlewares:

```python
# agents/my_agent.py
from cogni import Agent

# Create agent with middleware chain
Agent('weather_agent', 'prompt|gpt-4o|tool_handler')

# This defines an agent that:
# 1. Loads the prompt (prompt middleware)
# 2. Sends the conversation to GPT-4o (gpt-4o middleware) 
# 3. Processes any tool usage (tool_handler middleware)
```

Middleware chains are defined using a pipe-separated string where each name corresponds to a registered middleware.

## 5. Using the Agent

```python
from cogni import Agent, State

# Initialize state if needed
if 'user_123' not in State:
    State['user_123'] = {'preferences': {'units': 'metric'}}

# Call the agent like a function
response = Agent['weather_agent']("What's the weather in Tokyo?")
print(response)
```

## Managing State

Use the global `State` object to store and retrieve data across interactions:

```python
from cogni import State

# Set state
State['user_456'] = {'history': []}
State['user_456'].history.append("Asked about weather")
State['user_456'].preferences = {'theme': 'dark'}

# Get state
user_state = State['user_456']
print(user_state.history)  # ['Asked about weather']
print(user_state.preferences.theme)  # 'dark'
```

## Example: Tool Usage with the `use_tools` Decorator

The `use_tools` decorator enables middleware to process tool calls in messages:

```python
from cogni import mw, use_tools, Tool
from functools import wraps

# Register a tool
@Tool.register
def calculate(expression):
    try:
        return eval(expression)
    except Exception as e:
        return f"Error: {str(e)}"

# Create a middleware that processes tool usage
@use_tools()
@mw
def calculator_middleware(ctx, conv):
    # The @use_tools decorator has processed any tool calls
    # in the last message and stored results in ctx['tools']
    
    # You can access results and perform additional processing
    if 'tools' in ctx and 'calculate' in ctx['tools']:
        result = ctx['tools']['calculate']['result']
        return conv.rehop(f"The result is: {result}")
    
    # For tool errors
    if 'tools' in ctx and 'errors' in ctx['tools'] and ctx['tools']['errors']:
        return conv.rehop("There was an error processing your calculation.")
    
    return conv
```

In this example:
1. When a message contains `<tool name="calculate">2 + 2</tool>`
2. The `use_tools` decorator extracts and processes this tool call
3. The result is stored in `ctx['tools']['calculate']['result']`
4. Your middleware can then use this result to generate a response

## Complete Flow

Here's the complete flow of a user interaction:

1. User sends a message: "What's the weather in Paris?"
2. Agent processes the message through the middleware chain:
   - `prompt` middleware prepares the conversation 
   - `gpt-4o` middleware sends it to the language model
   - LLM generates: "Let me check that for you. <tool name='fetch_weather'>Paris</tool>"
   - `use_tools` decorator in your middleware processes the tool call
   - Your middleware uses the tool result to generate a final response
3. User receives the final response: "The weather in Paris is Sunny, 25°C"

## Tips and Best Practices

- **Keep Tools Focused**: Tools should do one thing well
- **Reuse Tools**: Build a library of tools that can be shared across agents
- **Middleware Chain Order**: Order matters! Place middlewares in a logical processing sequence
- **Use State Wisely**: Store only what you need in State for persistence
- **Error Handling**: Add error handling in tools and middlewares to create robust agents
