import io
import sys
from contextlib import redirect_stdout, redirect_stderr
from cogni import Agent
import subprocess

# Capture tout stdout/stderr
buffer = io.StringIO()
with redirect_stdout(buffer), redirect_stderr(buffer):
    def get_git_diff():
        result = subprocess.run(['git', 'diff'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("Git diff fetched")  # Ceci sera aussi capturé
        return result.stdout

    diff = get_git_diff()

    msg = Agent['Commiter'](diff)

# Fin de la capture
captured_output = buffer.getvalue()

print(msg)
