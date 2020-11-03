import json
import requests

def load_config():
    with open('config.json') as f:
        return json.loads(f.read())

def get_json():
    url = load_config()['url']
    r = requests.get(url)
    # print(r.status_code, r.text)
    return r.json()


def load_termlist():
    return get_json()
