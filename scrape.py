from spaces_interface import load_termlist, write_error, write_search_results, write_logs, write_job_log
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

MAX_PICTURES_PER = 5

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

def run(total_hours=24, hourly_limit=300, shuffle=False):
    termlist = load_termlist()

    total_requests = min(int(total_hours * hourly_limit), len(termlist))
    total_time = 60*60*min(total_hours, len(termlist)/hourly_limit)
    wait_time = total_time / total_requests
    daily_max_requests = hourly_limit * 24

    try:
        import os
        os.mkdir('search_results')
    except Exception as e:
        print("could not make directory", e)
        # pass

    # not sure if shuffle is needed, if so try shuffling index
    if shuffle:
        raise NotImplementedError()
    #     print("shuffling termlist")
    #     random.shuffle(termlist)
    if len(termlist) > daily_max_requests:
        print("Warning: termlist length is", len(termlist), "while max daily requests will be", daily_max_requests)
    if len(termlist) > total_requests:
        print(f"Warning: only querying {total_requests} of {len(termlist)} total terms (not enough time specified)")
    write_logs(f"querying {total_requests} terms for {printable_time(seconds=total_time)}", verbose=True)
    
    term_idx = 0
    google_img_count = 0
    baidu_img_count = 0
    google_fails = []
    baidu_fails = []
    google_results = []
    baidu_results = []

    start_ts = time.time()
    for i in range(0, total_requests):
        start_iter_ts = time.time()
        try:
            english_term = termlist.loc[term_idx].english
            chinese_term = termlist.loc[term_idx].chinese
        except:
            print("out of terms")
            break
        print(f'request {i}, term idx {term_idx}: "{english_term}", "{chinese_term}"')
        if not english_term:
            print("\tskipping Google for term (English term not present)")
        else:
            try:
                urls = query_google(english_term)
                print(f"\tGoogle got {len(urls)} images")
                result = {}
                result['english_term'] = english_term
                result['chinese_term'] = chinese_term
                result['urls'] = urls[:MAX_PICTURES_PER]
                result['ts'] = time.time()
                google_results.append(result)
            except Exception as e:
                google_fails.append(e)
                print("\tGoogle fail")
        if not chinese_term:
            print("\tskipping Baidu for term (Chinese term not present)")
        else:
            try:
                urls = query_baidu(chinese_term)
                print(f"\tbaidu got {len(urls)} images")
                result = {}
                result['english_term'] = english_term
                result['chinese_term'] = chinese_term
                result['urls'] = urls[:MAX_PICTURES_PER]
                result['ts'] = time.time()
                baidu_results.append(result)
            except Exception as e:
                baidu_fails.append(e)
                print("\tBaidu fail")
        print("done querying search engines for term", english_term)
        term_idx += 1

        # account for the time the calls took
        took = time.time() - start_iter_ts
        # add in random jitter
        time_noise = random.random()*2 - 1
        # print("adding noise to wait time", printable_time(seconds=time_noise))

        # cache results. this is a backup and not meant to be a reliable data store
        if i % 25 == 0:
            try:
                # count, google_urls = write_search_results(google_results, 'google')
                # google_img_count += count
                # save_search_results(google_results, "google", google_urls)
                google_img_count += update_results(google_results, 'google')
                # count, baidu_urls = write_search_results(baidu_results, 'baidu')
                # baidu_img_count += count
                # save_search_results(baidu_results, "baidu", baidu_urls)
                baidu_img_count += update_results(baidu_results, 'baidu')
                google_results = []
                baidu_results = []
            except Exception as e:
                print("failed to write search results; waiting until next attempt:", e)
        time.sleep(max(0, wait_time - took + time_noise))

    # count, google_urls = write_search_results(google_results, 'google')
    # google_img_count += count
    # count, baidu_urls = write_search_results(baidu_results, 'baidu')
    # baidu_img_count += count
    # save_search_results(google_results, "google", google_urls)
    # save_search_results(baidu_results, "baidu", baidu_urls)
    try:
        google_img_count += update_results(google_results, 'google')
        baidu_img_count += update_results(baidu_results, 'baidu')
    except Exception as e:
        exc = traceback.format_exc()
        print(exc)
        print("Failed to update search results, waiting 1 minute")
        time.sleep(60)
        google_img_count += update_results(google_results, 'google')
        baidu_img_count += update_results(baidu_results, 'baidu')

    google_results = []
    baidu_results = []

    write_logs(f'wrote {google_img_count} google images and {baidu_img_count} baidu images', verbose=True)
    write_error(f"Baidu failures: {len(baidu_fails)}")
    write_error(f"Google failures: {len(google_fails)}")
    print("took", printable_time(seconds=time.time() - start_ts))
    return (google_img_count, baidu_img_count, total_requests)

def update_results(results, engine):
    count, urls = write_search_results(results, engine)
    search_term_to_id = save_search_results(results, engine, urls)
    # to do: update termlist with a URL that points to the search on the API
    print(search_term_to_id)
    return count

if __name__ == "__main__":
    import traceback
    import time
    ts = time.time()
    error = False
    try:
        print(f"scraper started {datetime.utcnow()}")
        google_img_count, baidu_img_count, total_requests = run(.005)
    except Exception as e:
        exc = traceback.format_exc()
        error = True
        print(str(exc))
        write_logs("got an error while running scraper:" + str(e) + " (see error log for details)", verbose=True)
        write_error(exc, verbose=True)
    if not error:
        write_job_log(f'made {total_requests} requests and collected a total of {google_img_count + baidu_img_count} images over {printable_time(seconds=time.time()-ts)}')
    else:
        write_job_log(f'failed to finish with error {exc} (details in errors.json), run terminated after {printable_time(seconds=time.time()-ts)}')