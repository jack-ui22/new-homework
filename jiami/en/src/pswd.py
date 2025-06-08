import secrets

import random

def generate_basic():
    return random.randint(10_000_000, 20_000_000)

def generate_secure(digits):
    key=secrets.randbelow(10**digits - 10**(digits-1)) + 10**(digits-1)
    return key

def generate_basic1():
    return random.randint(10, 25)

