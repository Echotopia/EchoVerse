from functools import wraps
import inspect
import logging
from cogni import Tool

logger = logging.getLogger(__name__)


def get_function_info(func, include_body=False):
    """
    Retrieves information about a given function, including its prototype,
    docstring, file path, and optionally its body.
    """
    if hasattr(func, '_func'):
        func = func._func
    elif hasattr(func, '__wrapped__'):
        func = func.__wrapped__

    signature = inspect.signature(func)
    docstring = inspect.getdoc(func) or ''
    file_path = inspect.getfile(func)
    prototype = f"{func.__name__}{signature}"

    result = f"""# {file_path}

{prototype}
    '''{docstring}'''
"""
    if include_body:
        try:
            source_lines, _ = inspect.getsourcelines(func)
            body = ''.join(source_lines)
            result += f"""\n\n{body}"""
        except (IOError, TypeError):
            result += "\n\n[Source code not available]"
    return result


def process_tool_commands(last_msg_content):
    """
    Process tool commands in a message content using the XML parser.
    """
    parser = Tool['xml_parser']('tool')
    tool_commands = parser(last_msg_content)

    output = {'errors': []}

    def propagate_error(err):
        output['errors'].append(err)

    for name, cmd in tool_commands.items():
        if name not in Tool:
            propagate_error(
                f"ERROR: using:\n```{cmd['raw']}```\nthe tool {name} doesn't exist"
            )
            continue

        tool_func = Tool[name]

        # JSON-formatted arguments
        if cmd.get('format') == 'json':
            try:
                import json
                args = json.loads(cmd['content'])
                if not isinstance(args, dict):
                    raise ValueError("JSON args not an object")
            except Exception as e:
                propagate_error(f"ERROR parsing JSON args for {name}: {e}")
                continue
            try:
                Tool['exec_tool_start'](name, args)
                result = tool_func(**args, **cmd.get('kwargs', {}))
                Tool['exec_tool_end'](name, result)
                output[name] = {'name': name, 'result': result, 'args': args}
            except Exception as e:
                propagate_error(f"ERROR executing tool {name}: {e}")
                continue

        # Plaintext arguments
        else:
            try:
                if cmd.get('content', '') == '':
                    Tool['exec_tool_start'](name, {})
                    result = tool_func(**cmd.get('kwargs', {}))
                else:
                    Tool['exec_tool_start'](name, cmd['content'])
                    result = tool_func(cmd['content'], **cmd.get('kwargs', {}))
                Tool['exec_tool_end'](name, result)
                output[name] = {'name': name, 'result': result, 'args': cmd.get('content')}
            except Exception as e:
                propagate_error(f"ERROR executing tool {name}: {e}")
                continue

    return output


def use_tools(*tools, **kwargs):
    """
    Decorator for middleware that processes tool usage in the assistant's messages.
    """
    from cogni import Conversation, Message, Tool, ES

    def _mw_wrapper(mw):
        @wraps(mw)
        def _mw_wrapper_inner(ctx, conv):
            if not isinstance(conv, Conversation) or not conv or conv[-1].role != 'assistant':
                return mw(ctx, conv)
            if '!!NOTOOL' in conv[-1].content:
                return mw(ctx, conv)

            tool_results = process_tool_commands(conv[-1].content)
            tool_output = ""
            if tool_results.get('errors'):
                for err in tool_results['errors']:
                    logger.error(err)
                conv = conv + Message(role='system', content=f"<error>{tool_results['errors']}</error>")
                tool_output = f"<error>{tool_results['errors']}</error>"
                conv.should_infer = True
                return conv

            used = [n for n in tool_results if n != 'errors']
            if len(used) > 1:
                conv = conv + Message(role='developer', content=f"<error>Use one tool at a time: {used}</error>")
                conv.should_infer = True
                return conv
            if len(used) == 1:
                name = used[0]
                conv = conv + Message(role='developer', content=f"<tool_result name=\"{name}\">{tool_results[name]['result']}</tool_result>")
                conv.should_infer = True
                tool_output = tool_results[name]['result']
            ES.emit('tool_used', {
                "agent":ctx['agent'].name,
                "tool":name,
                "output": tool_output
            })
            ctx['tools'] = tool_results
            return mw(ctx, conv)

        return _mw_wrapper_inner

    return _mw_wrapper
