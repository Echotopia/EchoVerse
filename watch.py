from cogni import Agent
import subprocess

def get_git_diff():
    result = subprocess.run(['git', 'diff'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout

diff = get_git_diff()

print(Agent['Commiter'](diff))
