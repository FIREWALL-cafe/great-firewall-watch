from output import write_error
from termlist import load_termlist
from user_agent import get_user_agent

from bs4 import BeautifulSoup
from datetime import datetime
import json
import pandas as pd
import random
import re
import requests
import time

def query_baidu(term):
    baidu_template = 'https://image.baidu.com/search/index?tn=baiduimage&word={}'
    user_agent = get_user_agent()
    url = 'https://image.baidu.com/search/flip?tn=baiduimage&ie=utf-8&word='+term+'&ct=201326592&v=flip'
    r = requests.get(url, timeout=10,
                proxies={'https':None, 'http':None},
                headers={'User-Agent':user_agent})
    urls = re.findall('"objURL":"(.*?)",',r.text,re.S)
    return urls

def query_google(term):
    google_template = 'https://www.google.com/search?q={}&tbm=isch'
    r = requests.get(google_template.format(term))
    soup = BeautifulSoup(r.text, features="html.parser")
    urls = [tag.get('src') for tag in soup.find_all('img') if tag.get('src')[:4] == 'http']
    return urls

def printable_time(days=0, hours=0, minutes=0, seconds=0):
    total_seconds = 24*60*60*days + 60*60*hours + 60*minutes + seconds
    if total_seconds < 60:
        return f"{round(total_seconds)} seconds"
    if total_seconds < 60*60:
        return f"{round(total_seconds/60, 1)} minutes"
    if total_seconds < 2*24*60*60:
        return f"{round(total_seconds/(60*60), 1)} hours"
    total_days = int(total_seconds/(24*60*60))
    remainder = total_seconds % (24*60*60)
    return f"{total_days} days, {printable_time(seconds=remainder)}"

def run(total_hours, hourly_limit=200, shuffle=True):
    google_fails = []
    baidu_fails = []

    google_results = []
    baidu_results = []

    total_requests = int(total_hours * hourly_limit)
    total_time = 60*60*total_hours
    wait_time = total_time / total_requests
    daily_max_requests = hourly_limit * 24

    termlist = load_termlist()

    if shuffle:
        print("shuffling termlist")
        random.shuffle(termlist)
    if len(termlist) > daily_max_requests:
        print("Warning: termlist length is", len(termlist), "while max daily requests will be", daily_max_requests)
    if len(termlist) > total_requests:
        print(f"Warning: only querying {total_requests} of {len(termlist)} total terms")
    print("querying", total_requests, "terms for", printable_time(seconds=total_time))

    term_idx = 0

    start_ts = time.time()
    for i in range(0, total_requests):
        start_iter_ts = time.time()
        try:
            term = termlist[term_idx]
        except:
            print("out of terms")
            break
        print(f'{i}: "{term}"')
        try:
            urls = query_google(term)
            print(f"\tgoogle got {len(urls)} images")
            result = {}
            result['term'] = term
            result['urls'] = urls
            result['ts'] = time.time()
            google_results.append(result)
        except Exception as e:
            # google_results['term'] = term
            # google_results['error'] = str(e)
            google_fails.append(e)
            print("\tgoogle fail", e)
        try:
            urls = query_baidu(term)
            print(f"\tbaidu got {len(urls)} images")
            result = {}
            result['term'] = term
            result['urls'] = urls[:20]
            result['ts'] = time.time()
            baidu_results.append(result)
        except Exception as e:
            baidu_fails.append(e)
            print("\tbaidu fail")

        term_idx += 1

        # account for the time the calls took
        took = time.time() - start_iter_ts
        # add in random jitter
        time_noise = random.random()*2 - 1
        # print("adding noise to wait time", printable_time(seconds=time_noise))

        # cache results. this is a backup and not meant to be a reliable data store
        datestring = str(datetime.utcnow().date())
        with open(f'search_results/google_searches_{datestring}.json', 'w') as f:
            f.write(json.dumps(google_results))
        with open(f'search_results/baidu_searches_{datestring}.json', 'w') as f:
            f.write(json.dumps(baidu_results))
        time.sleep(max(0, wait_time - took + time_noise))
    print("took", printable_time(seconds=time.time() - start_ts))

if __name__ == "__main__":
    # run(.05, shuffle=False)
    write_error("testing the error reporting method")
