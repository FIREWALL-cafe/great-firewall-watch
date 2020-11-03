import boto3
from botocore.client import Config
from boto3.s3.transfer import S3Transfer
import datetime
import json
import requests

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
response = client.list_buckets()
spaces = [space['Name'] for space in response['Buckets']]
print("Spaces List: %s" % spaces)

def create_error_file(suffix=''):
    # r = requests.put()
    pass

def load_error_file(suffix=''):
    if suffix:
        r = requests.get(f'{bucket_endpoint}/errors_{suffix}.json')
    else:
        r = requests.get(f'{bucket_endpoint}/errors.json')
    if r.status_code == 200:
        print("found the file")
        return r.json()
    else:
        print("did not find the file", r)
        return []

# def get_auth_headers():
#     credential_string = f'{j["access_key_id"]}/{datetime.datetime.now().strftime("%Y%m%d")}/{j["region"]}/s3/aws4_request'


#     print(credential_string)
#     headers = {
#         "Credential": credential_string
#         "Authorization": "AWS4-HMAC-SHA256"
#     }

def write_error(s):
    file_contents = load_error_file()
    # new_contents = f'{datetime.datetime.now()} {s}\n' + file_contents
    new_contents = [{'timestamp':str(datetime.datetime.utcnow()), 'error':s}] + file_contents
    with open('errors.json', 'w') as f:
        f.write(json.dumps(new_contents))
    # upload the file we just wrote
    transfer.upload_file('errors.json', j['bucket'], 'errors.json')
    # make that file public
    r = client.put_object_acl(ACL='public-read', Bucket=j['bucket'], Key="errors.json")
    print(r)
