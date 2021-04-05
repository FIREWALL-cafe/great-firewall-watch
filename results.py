import time
from watch_utils import combined_term

class ResultSet:
    '''
    Serves as the data store for a single term
    '''
    def __init__(self, english_term, chinese_term, label):
        self.english_term = english_term
        self.chinese_term = chinese_term
        self.label = label
        self.urls = {'google':[], 'baidu':[]}
        self.datalake_urls = {'google':[], 'baidu':[]}
        self.ts = time.time()

    def add(self, urls, search_engine):
        if len(self.urls[search_engine]) > 0:
            raise Exception(f"already added urls for {search_engine} to {self.combined_term()}")
        self.ts = time.time()
        self.urls[search_engine] = urls

    def set_datalake_urls(self, urls, search_engine):
        if len(self.datalake_urls[search_engine]) > 0:
            raise Exception(f"already added datalake urls for {search_engine} to {self.combined_term()}")
        self.datalake_urls[search_engine] = urls

    def get_datalake_urls(self, search_engine):
        return self.datalake_urls[search_engine]

    def combined_term(self):
        return combined_term(self.english_term, self.chinese_term)

class ResultSetList:
    '''
    A collection of ResultSets
    '''

    def __init__(self):
        self.dict = {}
        self.wrote = {'google':0, 'baidu':0}

    def add(self, result):
        term = result.combined_term()
        self.dict[term] = result

    def iterterm(self):
        for term,result in self.dict.items():
            yield term,result

    def get_searches_by_term(self, term_param):
        return [result for term,result in self.iterterm() if term == term_param]

    def clear(self):
        self.wrote['google'] = sum([len(result.get_datalake_urls('google')) for term,result in self.iterterm()])
        self.wrote['baidu'] = sum([len(result.get_datalake_urls('baidu')) for term,result in self.iterterm()])
        print("cleared", self.wrote)
        self.dict = {}

    @property
    def length(self):
        return len(self.dict)