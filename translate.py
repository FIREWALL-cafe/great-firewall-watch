import json
import os
import requests

class Translator():
    def __init__(self):
        self.endpoint = 'https://babelfish.firewallcafe.com/translate'
        self.target = 'zh-CN'
        with open('config.json') as f:
            self.secret = json.loads(f.read())['private_key_id']
        
    def to_chinese(self, text):
#         if isinstance(text, six.binary_type):
#             text = text.decode("utf-8")
        j = requests.post(self.endpoint,
            data={'secret':private_key_id, 'query':text, 'langFrom':'en', 'langTo':'zh-CN'}
        ).json()
        if j['ok'] > 0:
            return j['translated']
        else return ''

    def to_english(self, text, source_language='zh-CN'):
        j = requests.post(self.endpoint,
            data={'secret':private_key_id, 'query':text, 'langFrom':'zh-CN', 'langTo':'en'}
        ).json()
        if j['ok'] > 0:
            return j['translated']
        else return ''

def machine_translate(termlist):
    print("running machine translation on list")
    translator = Translator()
    for term_idx in range(len(termlist)):
        english_term = termlist[term_idx]['english']
        chinese_term = termlist[term_idx]['chinese']
        if not chinese_term and not english_term:
            continue
        if not chinese_term: 
            chinese_term = translator.to_chinese(english_term)
            termlist[term_idx]['chinese'] = chinese_term
        if not english_term:
            english_term = translator.to_english(chinese_term)
            termlist[term_idx]['english'] = english_term

    write_csv(termlist)
    return termlist