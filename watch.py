import io
import sys
import os
from contextlib import redirect_stdout, redirect_stderr
from cogni import Agent
import subprocess

EMOJI_FILE = "/tmp/emoji_used.txt"

# Lire emojis utilisés
if os.path.exists(EMOJI_FILE):
    with open(EMOJI_FILE, "r", encoding="utf-8") as f:
        used_emojis = [line.strip() for line in f if line.strip()]
else:
    used_emojis = []

# Capture tout stdout/stderr
buffer = io.StringIO()
with redirect_stdout(buffer), redirect_stderr(buffer):
    def get_git_diff():
        result = subprocess.run(['git', 'diff'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout

    diff = get_git_diff()

    prompt = f"""# Emojis
Here are the emojis used already (you have to renew and not use the same twice): {used_emojis}

---

# Diff

```diff
{diff}
```
"""

    msg = Agent['Commiter'](prompt)

# Fin de la capture
captured_output = buffer.getvalue()

# Extraire premier caractère s’il est emoji (très basique, tu peux raffiner)
first_char = msg[0]
if first_char not in used_emojis and first_char.strip():
    with open(EMOJI_FILE, "a", encoding="utf-8") as f:
        f.write(first_char + "\n")

print(msg)
