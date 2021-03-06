import boto3
from botocore.client import Config
from boto3.s3.transfer import S3Transfer, TransferConfig
import csv
from datetime import datetime
import hashlib
import imagehash
import imghdr
import json
from pandas import read_excel
from PIL import Image
import requests
import traceback
from translate_gcp import machine_translate
from urllib import parse
from watch_utils import combined_term, BAIDU, GOOGLE

'''
This is for reporting errors and statistics about the scraping rather than the results of the scraping itself
'''

with open('config.json') as f:
    j = json.loads(f.read())
bucket_endpoint = f'https://{j["bucket"]}.{j["region"]}.digitaloceanspaces.com'
# Initialize a session using DigitalOcean Spaces.
session = boto3.session.Session()
client = session.client('s3',
                        region_name=j['region'],
                        endpoint_url=f'https://{j["region"]}.digitaloceanspaces.com',
                        aws_access_key_id=j['access_key_id'],
                        aws_secret_access_key=j['secret_access_key'])
config = TransferConfig(use_threads=False, max_concurrency=1)
transfer = S3Transfer(client, config=config)

# List all buckets on your account.
try:
    response = client.list_buckets()
    spaces = [space['Name'] for space in response['Buckets']]
    print("Spaces List: %s" % spaces)
except Exception as e:
    print("Could not access Spaces bucket, are your key/ID valid?", str(e))

def hash_image(fname):
    return imagehash.phash(Image.open(fname))

def image_fname(fname):
    hashed = hash_image(fname)
    ext = imghdr.what(fname)
    if ext == 'jpeg':
        ext = 'jpg'
    return f'{hashed}.{ext}'

def load_json_file(fname):
    if '.json' not in fname:
        fname += '.json'
    r = requests.get(f'{bucket_endpoint}/{fname}')
    if not r.status_code == 200:
        return []
    return r.json()

def load_text_file(fname):
    r = requests.get(f'{bucket_endpoint}/{fname}')
    if not r.status_code == 200:
        return ""
    return r.text

def load_error_file(suffix=''):
    if suffix:
        r = requests.get(f'{bucket_endpoint}/errors_{suffix}.json')
    else:
        r = requests.get(f'{bucket_endpoint}/errors.json')
    if r.status_code == 200:
        # print("found the file")
        return r.json()
    else:
        # print("did not find the error file", r)
        return []

def _write_public(fname, new_fname=None):
    # assumes we already have a locally written file

    # if new_fname isn't specified, then just use fname as the name we're uploading
    if not new_fname:
        new_fname = fname
    # print('uploading', fname, 'to', new_fname)

    # upload the file we just wrote
    transfer.upload_file(fname, j['bucket'], new_fname)
    # make that file public
    r = client.put_object_acl(ACL='public-read', Bucket=j['bucket'], Key=new_fname)
    # print("_write_file:", f'{bucket_endpoint}/{new_fname}')
    return r['ResponseMetadata']['HTTPStatusCode']

def request_and_write_image(url, spaces_folder):
    try:
        r = requests.get(url, stream=True)
    except Exception as e:
        print(url, e)
        return
    # print(r.status_code, "getting image", url)
    if not r.ok:
        return
    # write locally
    with open('temp', 'wb') as f:
        for block in r.iter_content(1024):
            if not block:
                break
            f.write(block)
    spaces_fname = image_fname('temp')
    status = _write_public('temp', f'{spaces_folder}/{spaces_fname}')
    if status < 400:
        return spaces_fname

def write_json_file(fname, contents):
    # write a file to upload
    with open(fname, 'w') as f:
        f.write(json.dumps(contents))
    return _write_public(fname)

def write_text_file(fname, contents):
    with open(fname, 'w') as f:
        f.write(contents)
    return _write_public(fname)

def write_search_results(results):
    '''
    Receives a list of result objects, each one a search with a term and the resulting image URLs.
    Returns the number of images retrieved, and a dictionary mapping the term to the new URLs stored
    on Digital Ocean
    '''
    datestring = str(datetime.utcnow().date())
    json_fname = f'search_results/searches_{datestring}.json'
    try:
        # print("getting file", f'{bucket_endpoint}/{json_fname}')
        r = requests.get(f'{bucket_endpoint}/{json_fname}')
        # print(r.status_code, "getting file", json_fname)
        j = json.loads(r.text)
    except json.decoder.JSONDecodeError: # no file exists
        j = []
    print(f"writing {results.length} search results")
    # status = write_json_file(json_fname, j + results_list)
    
    img_count = 0
    for term,result in results.iterterm():
        for search_engine in [BAIDU, GOOGLE]:
            datalake_urls = []
            for url in result.urls[search_engine]:
                spaces_folder = 'images/hashed'
                fname = request_and_write_image(url, spaces_folder)
                if fname:
                    img_count += 1
                    datalake_urls.append(f'{bucket_endpoint}/{spaces_folder}/{fname}')
            result.set_datalake_urls(datalake_urls, search_engine)
    return img_count

def write_error(s, verbose=False):
    try:
        file_contents = load_error_file()
    except Exception as e:
        exc = traceback.format_exc()
        print("could not load errors.json file from DigitalOcean")
        print(exc)
        return
    new_contents = [{'timestamp':str(datetime.utcnow()), 'error':s}] + file_contents
    status_code = write_json_file('errors.json', new_contents)
    if verbose:
        print("got error:", s)
        print("writing to errors.json:", status_code)
    status_code = write_text_file("error.txt", str(datetime.utcnow()) + ': ' + s)
    if verbose:
        print("writing to error.txt", status_code)

def write_logs(s, verbose=False):
    if verbose:
        print(s)
    try:
        file_contents = load_json_file('log.json')
    except Exception as e:
        exc = traceback.format_exc()
        print("could not load log.json file from DigitalOcean")
        print(exc)
        return
    new_contents = [{'timestamp':str(datetime.utcnow()), 'log':s}] + file_contents
    status_code = write_json_file('log.json', new_contents)
    if verbose:
        if status_code < 300:
            print('wrote to log:', s)
        else:
            print('failed to write to log:', s)

def write_job_log(s, verbose=False):
    if verbose:
        print(s)
    file_contents = load_text_file('jobs.txt')
    new_contents = f'[{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC] {s}\n{file_contents}'
    status_code = write_text_file('jobs.txt', new_contents)
    
    if verbose:
        if status_code < 300:
            print('wrote to log:', s)
        else:
            print('failed to write to log:', s)

def load_config():
    with open('config.json') as f:
        return json.loads(f.read())

def write_termlist(df):
    fname = "termlist.xlsx"
    print(f"writing to {fname}\n", df.info())
    df.to_excel(fname, index=False)

    # upload the file we just wrote
    transfer.upload_file(fname, j['bucket'], fname)
    # make that file public
    r = client.put_object_acl(ACL='public-read', Bucket=j['bucket'], Key=fname)
    print("termlist write result:", r['ResponseMetadata']['HTTPStatusCode'])
    
def create_link_columns(df):
    '''
    Use the "english" and "chinese" columns in the termlist to create links to the digitalocean folders 
    with image results for the given terms
    '''
    def formatted_link(row, search_engine):
        # print("row:", row)
        if not row['english'] or not row['chinese']:
            return ''
        spaces_endpoint = f"https://cloud.digitalocean.com/spaces/{j['bucket']}?path="
        folder_name = f"images/{search_engine}/{combined_term(row['english'], row['chinese'])}"
        # link format: '=HYPERLINK(\"\"; \"{3}\")'
        # return f'=HYPERLINK("{spaces_endpoint + parse.quote_plus(folder_name)}", "{folder_name}")'
        return spaces_endpoint + parse.quote_plus(folder_name)
    df['link_google'] = df.apply(lambda row: formatted_link(row, GOOGLE), axis='columns')
    df['link_baidu'] = df.apply(lambda row: formatted_link(row, BAIDU), axis='columns')
    return df

def load_termlist():
    config = load_config()
    base_url = f'https://{config["bucket"]}.{config["region"]}.digitaloceanspaces.com/'
    # read the excel file and make sure blank cells are empty strings and not NaNs
    try:
        df = read_excel(base_url + 'termlist.xlsx').fillna('')
    except:
        client.put_object_acl(ACL='public-read', Bucket=j['bucket'], Key='termlist.xlsx')
        try:
            df = read_excel(base_url + 'termlist.xlsx').fillna('')
        except:
            raise Exception("failed to load termlist at " + base_url + 'termlist.xlsx')

    needs_translation = False
    for i,row in df.fillna('').iterrows():
        try:
            english = row['english']
            chinese = row['chinese']
        except Exception as e:
            print('*'*20, "could not parse row:", row, e)
            continue        
        if (english and not chinese) or (chinese and not english):
            needs_translation = True
    if needs_translation:
        df = machine_translate(df)
    df = create_link_columns(df)
    write_termlist(df)
    return df

def update_termlist(termlist, results):
    # update the termlist to have links to the searches in the API
    pass