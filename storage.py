
from datetime import datetime
import requests

'''
For storing the results of the scraping
'''

BASE_URL = 'http://api.firewallcafe.com/'

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
        'search_term_initial_language_confidence':'test',
        'search_term_initial_language_alternate_code':'test',
        'search_term_translation':search['chinese_term'],
        'search_term_translation_language_code':'test',
        'search_term_status_banned':'test',
        'search_term_status_sensitive':'test',
        'search_schema_initial':'test'
    })
    print(r.status_code, r.text)

def post_image(image):
    print(image)

def save_search_results(results):
    print(results)

if __name__ == "__main__":
    save_search_results([])