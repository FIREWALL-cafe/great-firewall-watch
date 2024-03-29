from datetime import datetime
import json
import requests
from watch_utils import BAIDU, GOOGLE

'''
For storing the results of the scraping
'''

# note: this will be superceded by any API URL defined in config.json
# BASE_URL = 'https://api.firewallcafe.com'
BASE_URL = 'https://test-api.firewallcafe.com'
with open('config.json') as f:
    config = json.loads(f.read())
    try:
        BASE_URL = config['api_url']
    except:
        pass
print('saving search objects to', BASE_URL)

def get_ip():
    import socket
    r = requests.get('https://api.ipify.org?format=json', timeout=10)
    if r.status_code == 200:
        return r.json()['ip']
    else:
        print("ipify call failed, using Python socket library to lookup IP address")
        host_name = socket.gethostname() 
        host_ip = socket.gethostbyname(host_name) 
        return host_ip

def post_search(result, ip_address=None):
    if not ip_address:
        ip_address = get_ip()
    body = {
        'search_timestamp': int(1000*result.ts),
        # location of instance this is deployed on
        'search_location': config['location'] if 'location' in config else config['region'],
        'search_ip_address': ip_address,
        'search_client_name': result.label,

        # what do these two terms mean?
        'search_engine_initial': None,
        'search_engine_translation': None,

        'search_term_initial': result.english_term,
        'search_term_initial_language_code':'EN',
        'search_term_initial_language_confidence':1.0,
        'search_term_initial_language_alternate_code': None,
        'search_term_translation': result.chinese_term,
        'search_term_translation_language_code':'zh-CN',
        'search_term_status_banned': False,
        'search_term_status_sensitive': False,
        'search_schema_initial': None,
        'secret': config['api_secret']
    }
    print("post_search body:", body)
    r = requests.post(BASE_URL + '/createSearch', timeout=10, data=body)
    if r.status_code > 300:
        print("could not POST search", r.status_code, r.text)
        return None
    post_result = r.json()[0]
    if 'name' in post_result and post_result['name'] == 'error':
        print("could not POST search", post_result['english_term'])
        return None
    return post_result

def post_images(search_id, search_engine, urls, original_urls=[]):
    if len(urls) > 0:
        print(f"posting {len(urls)} images associated with search ID {search_id}", end=' ')
        body = {
            'search_id': search_id,
            'image_search_engine': search_engine,
            'urls': urls,
            'original_urls': original_urls,
            'image_ranks': [i+1 for i,_ in enumerate(urls)],
            'secret': config['api_secret']
        }
        r = requests.post(BASE_URL + '/saveImages', timeout=50, data=body)
        if r.status_code >= 300:
            try:
                print("result:", r.status_code, r.json())
            except json.decoder.JSONDecodeError:
                print("result:", r.status_code, r.text)
        else:
            print("result:", r.status_code)
    else:
        pass

def save_search_results(results):
    '''
    Given a set of searches that the scraper has created, post each individually to 
    the /createSearch endpoint. spaces_interface.write_search_results should have
    created a new list in each result object of the Digital Ocean URLs
    '''
    search_term_to_id = {}
    print(f"saving {results.length} search terms")
    for term,result in results.iterterm():
        try:
            post_result = post_search(result, '192.168.0.1')
            if not post_result:
                raise Exception("failed to post result for term " + term)
            if len(result.urls[GOOGLE]) != len(result.get_datalake_urls(GOOGLE)):
                post_images(post_result["search_id"], GOOGLE, result.get_datalake_urls(GOOGLE))
            else:
                post_images(post_result["search_id"], GOOGLE, result.get_datalake_urls(GOOGLE), result.urls[GOOGLE])
            if len(result.urls[BAIDU]) != len(result.get_datalake_urls(BAIDU)):
                post_images(post_result["search_id"], BAIDU, result.get_datalake_urls(BAIDU))
            else:
                post_images(post_result["search_id"], BAIDU, result.get_datalake_urls(BAIDU), result.urls[BAIDU])
            search_term_to_id[result.combined_term()] = post_result["search_id"]
        except Exception as e:
            print(f"got error on {term}: \n{e}")
    return search_term_to_id

if __name__ == "__main__":
    from results import ResultSet, ResultSetList
    import time
    result = ResultSet('bunny', '')
    result.add(['google.com', 'bunnies.io'], GOOGLE)
    result.set_datalake_urls(['datalake.com/google.com', 'datalake.com/bunnies.io'], GOOGLE)
    results = ResultSetList()
    results.add(result)
    save_search_results(results)