import json
import random

DEFAULT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'

def get_user_agent():
    try:
        with open('user-agents.json') as f:
            agents_list = json.loads(f.read())
            return random.choice(agents_list)            
    except Exception as e:
        return DEFAULT