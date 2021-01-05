import boto3
from botocore.client import Config
from boto3.s3.transfer import S3Transfer
import csv
from datetime import datetime
import json
from pandas import read_excel
import requests
from translate_gcp import machine_translate

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
transfer = S3Transfer(client)

# List all buckets on your account.
try:
    response = client.list_buckets()
    spaces = [space['Name'] for space in response['Buckets']]
    print("Spaces List: %s" % spaces)
except Exception as e:
    print("Could not access Spaces bucket, are your key/ID valid?", str(e))

def load_json_file(fname):
    if '.json' not in fname:
        fname += '.json'
    r = requests.get(f'{bucket_endpoint}/{fname}')
    if not r.status_code == 200:
        return []
    return r.json()

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
    return r['ResponseMetadata']['HTTPStatusCode']

def request_and_write_image(url, spaces_fname):
    try:
        r = requests.get(url, stream=True)
    except Exception as e:
        print(url, e)
        return
    print(r.status_code, "getting image", url)
    if not r.ok:
        return
    # write locally
    with open('temp', 'wb') as f:
        for block in r.iter_content(1024):
            if not block:
                break
            f.write(block)
    return _write_public('temp', spaces_fname)

def write_json_file(fname, contents):
    # write a file to upload
    with open(fname, 'w') as f:
        f.write(json.dumps(contents))
    return _write_public(fname)

def write_search_results(contents, search_engine):
    datestring = str(datetime.utcnow().date())
    json_fname = f'search_results/{search_engine}_searches_{datestring}.json'
    try:
        # print("getting file", json_fname)
        r = requests.get(f'{bucket_endpoint}/{json_fname}')
        # print(r.status_code, "getting file", json_fname)
        j = json.loads(r.text)
    except json.decoder.JSONDecodeError: # no file exists
        j = []
    
    status = write_json_file(json_fname, j + contents)

    img_count = 0
    for term_results in contents:
        term = term_results['english_term'] + '_' + term_results['chinese_term']
        for url in term_results['urls']:
            spaces_fname = f'images/{search_engine}/{term}/{datestring}__{img_count}.jpg'
            request_and_write_image(url, spaces_fname)
            img_count += 1
    return img_count

def write_error(s, verbose=False):
    file_contents = load_error_file()
    new_contents = [{'timestamp':str(datetime.utcnow()), 'error':s}] + file_contents
    status_code = write_json_file('errors.json', new_contents)
    if verbose:
        print("got error:", s)
        print("writing to file:", status_code)

def write_logs(s, verbose=False):
    if verbose:
        print(s)
    file_contents = load_json_file('log.json')
    new_contents = [{'timestamp':str(datetime.utcnow()), 'log':s}] + file_contents
    status_code = write_json_file('log.json', new_contents)
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
    print("writing to", fname, df)
    df.to_excel(fname, index=False)

    # upload the file we just wrote
    transfer.upload_file(fname, j['bucket'], fname)
    # make that file public
    r = client.put_object_acl(ACL='public-read', Bucket=j['bucket'], Key=fname)
    print(r)

def load_termlist():
    config = load_config()
    base_url = f'https://{config["bucket"]}.{config["region"]}.digitaloceanspaces.com/'
    # read the excel file and make sure blank cells are empty strings and not NaNs
    df = read_excel(base_url + 'termlist.xlsx').fillna('')
    needs_translation = False
    for i,row in df.fillna('').iterrows():
        try:
            english = row['english']
            chinese = row['chinese']
        except Exception as e:
            print("could not parse row:", row, e)
            continue        
        if (english and not chinese) or (chinese and not english):
            needs_translation = True
    if needs_translation:
        df = machine_translate(df)
    return df
