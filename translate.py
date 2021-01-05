import json
import os
import requests

import spaces_interface

class Translator():
    def __init__(self):
        self.endpoint = 'https://babelfish.firewallcafe.com/translate'
        self.target = 'zh-CN'
        with open('config.json') as f:
            self.secret = json.loads(f.read())['babelfish_key_id']

    def translate(self, text, langFrom, langTo):
        return ''

        r = requests.post(self.endpoint,
            data={'secret':self.secret, 'query':text, 'langFrom':langFrom, 'langTo':langTo}
        )
        # print(r.status_code, r.text)
        try:
            j = r.json()
        except: 
            return ''
        if j['ok'] > 0:
            return j['translated']
        else:
            return ''

    def to_chinese(self, text):
        result = self.translate(text, 'en', 'zh-CN')
        if len(result) == 0:
            print(f"empty translation: {text} => {result}")
        return result

    def to_english(self, text):
        result = self.translate(text, 'zh-CN', 'en')
        if len(result) == 0:
            print(f"empty translation: {text} => {result}")
        return result

def machine_translate(df):
    print("running machine translation on list")
    translator = Translator()
    count = 0
    for i,row in df.iterrows():
        english_term = row.english
        chinese_term = row.chinese
        # print(english_term, chinese_term)
        if not chinese_term and not english_term:
            continue
        if not chinese_term: 
            chinese_term = translator.to_chinese(english_term)
            df.at[i, 'chinese'] = chinese_term
            if len(chinese_term) > 0:
                count += 1
        if not english_term:
            english_term = translator.to_english(chinese_term)
            df.at[i, 'english'] = english_term
            if len(english_term) > 0:
                count += 1
    print("translated", count, "words")

    return df
