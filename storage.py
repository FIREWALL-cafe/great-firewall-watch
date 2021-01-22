
from datetime import datetime
import requests

'''
For storing the results of the scraping
'''

# BASE_URL = 'http://api.firewallcafe.com'
BASE_URL = 'http://159.89.80.47'

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
    print(search)
    r = requests.post(BASE_URL + '/createSearch', data={
        'search_timestamp':search['ts'],
        # location of instance this is deployed on
        'search_location': 'new_york_city',
        # not sure there is a reliable way to get the IP address without hardcoding it, and that won't be great if we're using a proxy
        'search_ip_address': ip_address,
        'search_client_name':'rowan_scraper_tests',

        # what do these two terms mean?
        'search_engine_initial':'test',
        'search_engine_translation':'test',

        'search_term_initial':search['english_term'],
        'search_term_initial_language_code':'EN',
        'search_term_initial_language_confidence':0,
        'search_term_initial_language_alternate_code':'test',
        'search_term_translation':search['chinese_term'],
        'search_term_translation_language_code':'test',
        'search_term_status_banned':False,
        'search_term_status_sensitive':False,
        'search_schema_initial':'test'
    })
    return r.json()



def post_images(search_id, search_engine, urls):
    print(image)
    r = requests.post(BASE_URL + '/saveImage', data={
        "search_id": search_id,
        "image_search_engine": search_engine,
        "image_href": url
    })    

def save_search_results(results, search_engine):
    search = post_search({'ts':123456543, 'english_term':'bunny', 'chinese_term':'asdf'}, '192.168.0.1')
    # for each result, for each url in result['urls'], call post image
    post_images(search["search_id"], search_engine, results['urls'])

if __name__ == "__main__":
    save_search_results([])