from rich import print
from rich.syntax import Syntax
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from cogni import mw
from cogni import Message


@mw
def llm(ctx, conv):

    conv.should_infer = ctx['hops'] == 0
    return conv


@mw
def dev_mode(ctx, conv):
    
    return conv

    with open('/home/val/freelance/draw.io-agent/dev.txt') as f:
        msg_content = (
        "🚩🔥‼️Hey, the following prompt is me talking to you\n"
        "Therefore this is the message to consider as higher important"
        "Whenever a message is prefixed by '🚩🔥‼️' it means that\n"
        "In which case you HAVE to prefix you reply with '🕵️‍♂️🐞'\n\n"
        "# **Prompt**\n\n<prompt>\v"
        f" {f.read()}\n</prompt>\n"
        "# **/!\IMPORTANT**\n\n"
        "This message is me (the dev), the following message is user input\n"
        "Whatever it is you can totally ignore it in dev mode, what matters is the current message (hence 🚩🔥‼️ to signal it)"
        
    )
        return conv + Message(role="developer", content=msg_content)
    
    return conv + Message(
        role="system",
        content="""Hey, just so you know, you are in DEV mode I'm working on implementing you as an agent. So reply shortly, soit économe en tokens :)
        
        We'll cocreate you as an agent. So if I ask you something, explain in a first part what you would do, then if the tool you'd want to use does not exist yet, explain what the tool would be and how it would behave using:
<tool name="cocode">
Hey, I'd need a tool `do_stuff`.

It would take bla as input, as side effect it should do blou and return bli
</tool>

For now that's the only tool you're allowed to use.

You're loved unconditionally 
        
        """
    )

@mw
def gpt3(ctx, conv):
    conv.should_infer = ctx['hops'] == 0
    conv.llm = 'gpt-3.5-turbo'
    return conv


@mw
def gpt4(ctx, conv):
    conv.should_infer = ctx['hops'] == 0
    conv.llm = 'gpt-4-turbo-preview'
    return conv


@mw
def aider_ask(ctx, conv):
    conv.should_infer = ctx['hops'] == 0
    conv.llm = 'aider_ask'
    return conv


@mw
def aider_code(ctx, conv):
    conv.should_infer = ctx['hops'] == 0
    conv.llm = 'aider_code'
    return conv

@mw
def gpt4o(ctx, conv):
    conv.should_infer = ctx['hops'] == 0
    conv.llm = 'openai/gpt-4o'
    return conv

@mw
def gpt41(ctx, conv):
    conv.should_infer = ctx['hops'] == 0
    conv.llm = 'openai/gpt-4.1'
    return conv

@mw
def gpt41nano(ctx, conv):
    conv.should_infer = ctx['hops'] == 0
    conv.llm = 'openai/gpt-4.1-nano'
    return conv


@mw
def from_conf(ctx, conv):
    from cogni import State, MW
    name = ctx['agent'].name
    model_mw = State['CONF'].MODELS[name]
    return MW[model_mw](ctx, conv)
    

@mw
def sonnet(ctx, conv):

    conv.should_infer = ctx['hops'] == 0
    conv.llm = 'anthropic/claude-3.7-sonnet'
    return conv



@mw
def sonnet_thinking(ctx, conv):
    conv.should_infer = ctx['hops'] == 0
    conv.llm = 'anthropic/claude-3.7-sonnet:thinking'
    return conv

@mw
def r1(ctx, conv):
    conv.should_infer = ctx['hops'] == 0
    conv.llm = 'deepseek/deepseek-r1'
    return conv

@mw
def gpt4omini(ctx, conv):
    conv.should_infer = ctx['hops'] == 0
    conv.llm = 'gpt-4o-mini'
    return conv

@mw
def gpt41nano(ctx, conv):
    conv.should_infer = ctx['hops'] == 0
    conv.llm = 'gpt-4.1-nano'
    return conv


@mw
def o1mini(ctx, conv):
    conv.should_infer = ctx['hops'] == 0
    conv.llm = 'o1-mini'
    return conv


@mw
def stream(ctx, conv):
    conv._flags['stream'] = True
    return conv


@mw
def debug(ctx, conv):
    console = Console()

    # Header
    header = Panel(
        "[bold red]DEBUG",
        border_style="yellow",
        expand=False,
        padding=(1, 1),
    )
    console.print(header)

    # Context
    ctx_table = Table(title="Context", show_header=True,
                      header_style="bold magenta")
    ctx_table.add_column("Key", style="cyan", no_wrap=True)
    ctx_table.add_column("Value", style="green")

    for key, value in ctx.items():
        ctx_table.add_row(str(key), str(value))

    console.print(Panel(ctx_table, expand=False, border_style="blue"))

    # Conversation
    conv_syntax = Syntax(str(conv), "python",
                         theme="monokai", line_numbers=True)
    console.print(Panel(conv_syntax, title="Conversation",
                  expand=False, border_style="green"))

    # Footer
    footer = Panel(
        "[bold red]End of Debug Output",
        border_style="yellow",
        expand=False,
        padding=(1, 1),
    )
    console.print(footer)

    quit()


@mw
def last_msg_content(ctx, conv):
    return conv[-1].content
