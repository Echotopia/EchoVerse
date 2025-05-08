import random

from cogni import tool

@tool
def rnd_id(length=9):
    return ''.join(random.choice('0123456789abcdef') for _ in range(length))
