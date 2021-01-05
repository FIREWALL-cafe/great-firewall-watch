import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'great-firewall-translator.json'
from google.cloud import translate_v2 as translate

class Translator():
    def __init__(self):
        self.client = translate.Client()
        self.target = 'zh-CN'

    def to_chinese(self, text, source_language='en'):
#         if isinstance(text, six.binary_type):
#             text = text.decode("utf-8")
        
        # Text can also be a sequence of strings, in which case this method
        # will return a sequence of results for each text.
        result = self.client.translate(text, target_language='zh-CN', source_language=source_language)
        return result['translatedText']

    def to_english(self, text, source_language='zh-CN'):
        result = self.client.translate(text, target_language='en', source_language=source_language)
        return result['translatedText']

def machine_translate(df):
    print("running machine translation on list")
    translator = Translator()
    for i,row in df.iterrows():
        english_term = row.english
        chinese_term = row.chinese
        # print(english_term, chinese_term)
        print(f'{i} of {len(df)}', end='\r')
        if not chinese_term and not english_term:
            continue
        if not chinese_term: 
            chinese_term = translator.to_chinese(english_term)
            df.at[i, 'chinese'] = chinese_term
        if not english_term:
            english_term = translator.to_english(chinese_term)
            df.at[i, 'english'] = english_term

    return df
