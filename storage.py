
from datetime import datetime
import requests

'''
For storing the results of the scraping
'''

BASE_URL = 'http://api.firewallcafe.com'
# BASE_URL = 'http://159.89.80.47'

def get_ip():
    r = requests.get('https://api.ipify.org?format=json')
    if r.status_code == 200:
        return r.json()['ip']
    else:
        print("ipify call failed, using Python socket library to lookup IP address")
        host_name = socket.gethostname() 
        host_ip = socket.gethostbyname(host_name) 
        return host_ip

def post_search(search, ip_address=None):
    if not ip_address:
        ip_address = get_ip()
    r = requests.post(BASE_URL + '/createSearch', data={
        'search_timestamp': int(1000*search['ts']),
        # location of instance this is deployed on
        'search_location': 'automated_scraper',
        # not sure there is a reliable way to get the IP address without hardcoding it, and that won't be great if we're using a proxy
        'search_ip_address': ip_address,
        'search_client_name':'automated_scraper',

        # what do these two terms mean?
        'search_engine_initial': None,
        'search_engine_translation': None,

        'search_term_initial':search['english_term'],
        'search_term_initial_language_code':'EN',
        'search_term_initial_language_confidence':1.0,
        'search_term_initial_language_alternate_code': None,
        'search_term_translation':search['chinese_term'],
        'search_term_translation_language_code':'zh-CN',
        'search_term_status_banned': False,
        'search_term_status_sensitive': False,
        'search_schema_initial': None
    })
    return r.json()[0]

def post_images(search_id, search_engine, urls):
    print("posting images associated with search ID", search_id)
    body = {
        "search_id": search_id,
        "image_search_engine": search_engine,
        "urls": urls,
        "image_ranks": [i+1 for i,_ in enumerate(urls)]
    }
    # print(body)
    r = requests.post(BASE_URL + '/saveImages', data=body)
    print("result:", r.status_code)

def save_search_results(results, search_engine, url_list=None):
    search_term_to_id = {}
    for result in results:
        print("result", result)
        search = post_search(result, '192.168.0.1')
        # for each result, for each url in result['urls'], call post image
        # print("search", search)
        if 'name' in search and search['name'] == 'error':
            print("could not POST search", result['english_term'])
        post_images(search["search_id"], search_engine, url_list if url_list is not None else result['urls'])
        search_term_to_id[result['english_term']] = search["search_id"]
    return search_term_to_id

if __name__ == "__main__":
    import time
    save_search_results([{'english_term':'bunny', 'chinese_term':'', 'ts':time.time() }], url_list=['google.com', 'baidu.com'])