# from spaces_interface import load_termlist, write_error, write_search_results, write_logs, write_job_log
import api_interface as api
from results import ResultSet, ResultSetList
import spaces_interface as space
from user_agent import get_user_agent
from watch_utils import BAIDU, GOOGLE

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

def run(total_hours=24, hourly_limit=300, shuffle=False, termlist=None):
    if termlist is None:
        termlist = space.load_termlist()

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
    space.write_logs(f"querying {total_requests} terms for a minimum of {printable_time(seconds=total_time)}", verbose=True)
    
    term_idx = 0
    google_img_count = 0
    baidu_img_count = 0
    google_fails = []
    baidu_fails = []
    results = ResultSetList()

    start_ts = time.time()
    for i in range(0, total_requests):
        start_iter_ts = time.time()
        try:
            english_term = termlist.loc[term_idx].english
            chinese_term = termlist.loc[term_idx].chinese
        except:
            print("out of terms")
            break
        result = ResultSet(english_term, chinese_term)
        print(f'request {i}, term idx {term_idx}: "{result.combined_term()}"')
        if not english_term:
            print("\tskipping Google for term (English term not present)")
        else:
            try:
                urls = query_google(english_term)
                # print(f"\tGoogle got {len(urls)} images")
                result.add(urls[:MAX_PICTURES_PER], GOOGLE)
            except Exception as e:
                google_fails.append(e)
                print("\tGoogle fail")
        if not chinese_term:
            print("\tskipping Baidu for term (Chinese term not present)")
        else:
            try:
                urls = query_baidu(chinese_term)
                # print(f"\tbaidu got {len(urls)} images")
                result.add(urls[:MAX_PICTURES_PER], BAIDU)
            except Exception as e:
                baidu_fails.append(e)
                print("\tBaidu fail")
        print("done querying search engines for term", english_term)
        results.add(result)
        term_idx += 1

        # account for the time the calls took
        took = time.time() - start_iter_ts
        # add in random jitter
        time_noise = random.random()*2 - 1
        # print("adding noise to wait time", printable_time(seconds=time_noise))

        # cache results. this is a backup and not meant to be a reliable data store
        if i % 25 == 24:
            try:
                update_results(results)
                results.clear()
                google_img_count += results.wrote[GOOGLE]
                baidu_img_count += results.wrote[BAIDU]
            except Exception as e:
                import traceback
                print("failed to write search results; waiting until next attempt:", e)
                exc = traceback.format_exc()
                print(str(exc))
        time.sleep(max(0, wait_time - took + time_noise))

    if results.length > 0:
        try:
            update_results(results)
            results.clear()
            google_img_count += results.wrote[GOOGLE]
            baidu_img_count += results.wrote[BAIDU]
        except Exception as e:
            import traceback
            exc = traceback.format_exc()
            print(exc)
            print("Failed to update search results, waiting 1 minute")
            time.sleep(60)
            update_results(results)
            results.clear()
            google_img_count += results.wrote[GOOGLE]
            baidu_img_count += results.wrote[BAIDU]

    space.write_logs(f'wrote {results.wrote["google"]} google images and {results.wrote[BAIDU]} baidu images', verbose=True)
    if len(baidu_fails) > 0 or len(google_fails) > 0:
        space.write_error(f"Baidu failures: {len(baidu_fails)}, Google failures: {len(google_fails)}")
    print("took", printable_time(seconds=time.time() - start_ts))
    return (google_img_count, baidu_img_count, total_requests)

def update_results(results):
    count = space.write_search_results(results)
    search_term_to_id = api.save_search_results(results)
    # to do: update termlist with a URL that points to the search on the API
    print("search IDs:", search_term_to_id)
    return count

if __name__ == "__main__":
    import traceback
    import time
    ts = time.time()
    error = False
    try:
        print(f"scraper started {datetime.utcnow()}")
        google_img_count, baidu_img_count, total_requests = run()
    except Exception as e:
        exc = traceback.format_exc()
        error = True
        print(str(exc))
        space.write_logs("got an error while running scraper:" + str(e) + " (see error log for details)", verbose=True)
        space.write_error(exc, verbose=True)
    if not error:
        space.write_job_log(f'made {total_requests} requests and collected a total of {google_img_count + baidu_img_count} images over {printable_time(seconds=time.time()-ts)}', verbose=True)
    else:
        space.write_job_log(f'failed to finish with error (details in errors.json), run terminated after {printable_time(seconds=time.time()-ts)}', verbose=True)
    print("process finished")