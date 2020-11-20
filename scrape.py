from spaces_interface import load_termlist, write_error, write_search_results, write_logs
from storage import save_search_results
from user_agent import get_user_agent

from bs4 import BeautifulSoup
from datetime import datetime
import json
import pandas as pd
import random
import re
import requests
import time

MAX_PICTURES_PER = 10

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

def run(total_hours=24, hourly_limit=200, shuffle=False):


    google_fails = []
    baidu_fails = []

    google_results = []
    baidu_results = []

    total_requests = int(total_hours * hourly_limit)
    total_time = 60*60*total_hours
    wait_time = total_time / total_requests
    daily_max_requests = hourly_limit * 24

    termlist = load_termlist()

    # not sure if shuffle is needed, if so try shuffling index
    if shuffle:
        raise NotImplementedError()
    #     print("shuffling termlist")
    #     random.shuffle(termlist)
    if len(termlist) > daily_max_requests:
        print("Warning: termlist length is", len(termlist), "while max daily requests will be", daily_max_requests)
    if len(termlist) > total_requests:
        print(f"Warning: only querying {total_requests} of {len(termlist)} total terms (not enough time specified)")
    print("querying", total_requests, "terms for", printable_time(seconds=total_time))

    term_idx = 0

    start_ts = time.time()
    for i in range(0, total_requests):
        start_iter_ts = time.time()
        try:
            english_term = termlist.loc[term_idx].english
            chinese_term = termlist.loc[term_idx].chinese
        except:
            print("out of terms")
            break
        print(f'{i}: "{english_term}", "{chinese_term}"')
        try:
            urls = query_google(english_term)
            print(f"\tgoogle got {len(urls)} images")
            result = {}
            result['english_term'] = english_term
            result['chinese_term'] = chinese_term
            result['urls'] = urls[:MAX_PICTURES_PER]
            result['ts'] = time.time()
            google_results.append(result)
        except Exception as e:
            google_fails.append(e)
            print("\tgoogle fail", e)
        try:
            urls = query_baidu(english_term)
            print(f"\tbaidu got {len(urls)} images")
            result = {}
            result['english_term'] = english_term
            result['urls'] = urls[:MAX_PICTURES_PER]
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
        try:
            import os
            os.mkdir('search_results')
        except Exception as e:
            print("could not make directory", e)
        # write_search_results(f'search_results/google_searches_{datestring}.json', google_results)
        google_img_count = write_search_results(google_results, 'google')
        # write_search_results(f'search_results/baidu_searches_{datestring}.json', baidu_results)
        baidu_img_count = write_search_results(baidu_results, 'baidu')
        write_logs(f'wrote {google_img_count} google images and {baidu_img_count} baidu images')
        time.sleep(max(0, wait_time - took + time_noise))
    print("took", printable_time(seconds=time.time() - start_ts))

if __name__ == "__main__":
    # try:
    # run(.005, shuffle=False)
    run()
    # except Exception as e:
    #     print("during run(), an error occurred", e)
    #     write_error(str(datetime.now()) + ': ' + str(e))
