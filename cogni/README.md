# Cogni

A pragmatic framework for building and orchestrating LLM agents with minimal boilerplate.

## Foreword (terminology)

**Agent** :In the README and everywhere else, I'll call `Agent`, an agent, or a set of agents working together.

**Prompt**: Because cogni makes heavy use of `Few Shot Prompting`, I call `Prompt` a conversation with several messages.

## Core Philosophy

Cogni treats agents as functions - modular, composable building blocks that can be stacked together to create powerful AI applications.

```python
from cogni import Agent

# Use agents like functions in your code
result = Agent['classifier'](user_query)
if result == 'question':
    response = Agent['qa_agent'](user_query)
else:
    response = Agent['task_agent'](user_query)
```

## Key Features

- **Agents as Functions**: Build and orchestrate agents using familiar programming patterns
- **Magic Imports**: Automatic discovery of tools and components across your project
- **Middleware Architecture**: Process agent conversations through customizable transformation chains
- **Low Boilerplate**: Focus on agent logic, not framework configuration
- **State Management**: Persistent, hierarchical state with attribute-style access
- **Tool Registry**: Global registry of decorated functions accessible anywhere

## Installation

```bash
python3 -m pip install -e .
```

## Project Structure

Cogni encourages a modular directory structure without `__init__.py` files for better component isolation:

```
project/
├── agents/
│   ├── agent_type1/
│   │   ├── agents/        # Agent initialization
│   │   ├── middlewares/   # Middleware functions
│   │   ├── prompts/       # Conversation templates (.conv)
│   │   └── tools/         # Agent-specific tools
│   └── agent_type2/
│       └── ...
└── tools/                 # Global tools
```

**Important**: The absence of `__init__.py` files is intentional. This prevents unintended imports and encourages explicit component references.

## Quick Start

### 1. Create a Tool

Tools are standalone functions or classes that can be used by both your code and agents:

```python
# tools/weather.py
from cogni import tool

# Function tool
@tool
def fetch_weather(city: str) -> dict:
    """Get current weather for a city"""
    # Your implementation here
    return {"city": city, "temp": 22, "conditions": "sunny"}

# Class tool
@tool
class WeatherService:
    def __init__(self, api_key):
        self.api_key = api_key
        
    def get_forecast(self, city, days=3):
        # Use api_key to fetch forecast
        return [
            {"day": 1, "temp": 22, "conditions": "sunny"},
            {"day": 2, "temp": 20, "conditions": "partly cloudy"},
            {"day": 3, "temp": 18, "conditions": "rainy"}
        ]
```

Access anywhere in your project:

```python
from cogni import Tool

# Use function tool
weather_data = Tool['fetch_weather']('Paris')

# Use class tool
weather_service = Tool['WeatherService']('your-api-key')
forecast = weather_service.get_forecast('Paris')
```

### 2. Create an Agent Prompt

Create a prompt template in `.conv` format:

Messages are

```
# agents/weather_agent/prompts/weather_agent.conv
system: You are WeatherAgent, a helpful assistant for weather information.
You can use the fetch_weather tool to get current weather data.

__-__
```

### 3. Define Middleware

Middlewares form a processing chain for your agent:

```python
# agents/weather_agent/middlewares/process.py
from cogni import mw, Tool, use_tools, Message

@mw
@use_tools()  # Gives middleware access to tools
def process_middleware(ctx, conv):
    query = conv[-1].content
    city = extract_city(query)
    
    if city:
        weather = Tool['fetch_weather'](city)
        # Replace last assistant message with weather response
        return conv.rehop(
            f"The weather in {city} is {weather['temp']}°C and {weather['conditions']}."
        )
    else:
        # Add a new message to the conversation
        return conv + Message(
            role="assistant", 
            content="I couldn't determine which city you're asking about."
        )

def extract_city(query):
    # Simple extraction logic
    if "in" in query:
        return query.split("in")[1].strip().split()[0]
    return None
```

### 4. Register Your Agent

```python
# agents/weather_agent/agents/weather.py
from cogni import Agent

# Register with middleware chain
Agent('weather_agent', 'prompt|gpt-3.5-turbo|process_middleware')
```

The configuration string uses a pipe-delimited format to specify:
- `prompt`: Use prompt templates
- `gpt-3.5-turbo`: The LLM model to use
- `process_middleware`: Middleware to apply

### 5. Use Your Agent

```python
from cogni import Agent

response = Agent['weather_agent']("What's the weather in Paris?")
print(response)  # The weather in Paris is 22°C and sunny.
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Prompt MW  │ ──► │   LLM MW    │ ──► │ Process MW  │
└─────────────┘     └─────────────┘     └─────────────┘
      ▲                                        │
      └────────────────────────────────────────┘
```

Cogni uses a middleware chain architecture:

1. **Prompt Middleware**: Prepares the conversation with templates
2. **LLM Middleware**: Sends the conversation to the language model
3. **Process Middleware**: Handles the response, using tools as needed

Each middleware accepts and returns a `Conversation` object, allowing for flexible transformations.

## Middleware Deep Dive

Middlewares are the heart of Cogni's agent processing:

```python
from cogni import mw, use_tools, Message

@mw  # Register as middleware
@use_tools()  # Enable tool access
def my_middleware(ctx, conv):
    # ctx: Context information
    # conv: Conversation object
    
    # Conversation manipulation options:
    
    # 1. Add message to conversation
    new_conv = conv + Message(role="assistant", content="New message")
    
    # 2. Replace last assistant message
    new_conv = conv.rehop("Replacement message")
    
    # 3. Control inference behavior
    conv.should_infer = False  # Prevent LLM from generating a response
    
    return conv  # Always return the conversation object
```

Common middleware naming patterns:
- `{agent_name}_middleware`: Basic middleware for an agent
- `{agent_name}_loop`: Middleware that handles repeated processing cycles

## Tool System

The tool system provides a global registry of functions and classes:

```python
from cogni import tool, Tool

# Register a function as a tool
@tool
def my_tool(param1, param2):
    return f"Processed {param1} and {param2}"

# Access the tool from anywhere
result = Tool['my_tool']("value1", "value2")
```

Tool decorators can also be applied to classes, making all methods callable through the registry.

## Inter-Agent Communication

Agents can communicate with each other using the `talk_to_agent` tool:

```python
from cogni import tool, Agent

@tool
def talk_to_agent(content, agent_name):
    return Agent[agent_name](content)
```

This enables multi-agent systems where agents can:
- Delegate tasks to specialized agents
- Request information from other agents
- Coordinate complex workflows across multiple agents

## Advanced Features

### State Management

```python
from cogni import State

# Get or create state
state = State['user_123']
state.history.append("User asked about weather")
state.preferences = {"units": "metric"}

# Access state anywhere
user_state = State['user_123']
print(user_state.preferences)  # {"units": "metric"}

# Hierarchical state access
user_state.session.current_topic = "weather"
print(user_state.session.current_topic)  # "weather"

# Dict-style access for dynamic keys
dynamic_key = f"conversation_{session_id}"
state[dynamic_key] = {"messages": []}
```

The state system provides:
- Persistent storage of data across agent runs
- Attribute-style access to nested data
- Automatic saving of changes
- Hierarchical organization of data

### Conversation Management

The `Conversation` class provides methods for manipulating the conversation flow:

```python
from cogni import Message

# Add a message to the conversation
conv = conv + Message(role="assistant", content="New message")

# Replace the last assistant message
conv = conv.rehop("Updated response", role="assistant")

# Examine conversation history
last_message = conv[-1].content

# Control LLM inference
conv.should_infer = False  # Prevent LLM from generating a response
```

### Agent Composition

```python
from cogni import Agent, Tool

def process_complex_task(user_query):
    # Use multiple agents in sequence
    task_list = Agent['task_splitter'](user_query)
    results = []
    
    for task in task_list:
        if "research" in task:
            results.append(Agent['research_agent'](task))
        else:
            results.append(Agent['general_agent'](task))
            
    return Agent['summarizer'](results)
```

## Best Practices

1. **Avoid Circular Dependencies**:
   - Do not create circular dependencies between tools and agents
   - Tools should be self-contained and not rely on specific agents

2. **Middleware Design**:
   - Keep middleware functions focused on a single responsibility
   - Chain multiple middlewares rather than creating monolithic ones

3. **State Management**:
   - Use hierarchical state organization for clarity
   - Prefer attribute-style access for better readability
   - Consider state persistence needs when designing your data structure

4. **Import Patterns**:
   - Use absolute imports because of the absence of `__init__.py` files
   - Avoid importing entire modules - import specific functions/classes instead
   - Access tools through the `Tool` registry rather than direct imports when possible
