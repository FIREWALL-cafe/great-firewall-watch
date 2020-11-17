import json
import os
import requests

class Translator():
    def __init__(self):
        self.endpoint = 'https://babelfish.firewallcafe.com/translate'
        self.target = 'zh-CN'
        with open('config.json') as f:
            self.secret = json.loads(f.read())['babelfish_key_id']

    def translate(self, text, langFrom, langTo):
        r = requests.post(self.endpoint,
            data={'secret':self.secret, 'query':text, 'langFrom':langFrom, 'langTo':langTo}
        )
        print(r.status_code, r.text)
        try:
            j = r.json()
        except: 
            return ''
        if j['ok'] > 0:
            return j['translated']
        else:
            return ''

    def to_chinese(self, text):
        return self.translate(text, 'en', 'zh-CN')

    def to_english(self, text):
        return self.translate(text, 'zh-CN', 'en')

def machine_translate(termlist):
    print("running machine translation on list")
    translator = Translator()
    for term_idx in range(len(termlist)):
        english_term = termlist[term_idx]['english']
        chinese_term = termlist[term_idx]['chinese']
        print(english_term, chinese_term)
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