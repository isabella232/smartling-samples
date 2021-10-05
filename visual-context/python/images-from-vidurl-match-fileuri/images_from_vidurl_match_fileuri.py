import json
import os
import sys
import time

import requests

sys.path.insert(1, os.path.abspath('..')) # to allow loading module from parent directory
from context_common import authenticate, create_job_with_files

CONTEXT_FILE_URL = 'https://downloads.smartling.com/smartlingsamples/images-from-video-match-fileuri-video1.mp4'
CONTENT_FILE_NAME = 'images-from-vidurl-match-fileuri-contentfile1.json'
JOB_NAME = 'image-from-vidurl-match-fileuri'
LOCALE_IDS = ['fr-FR']
AUTHORIZE = True

def main():
    
    # Read authentication credentials from environment
    user_id = os.environ.get('DEV_USER_IDENTIFIER')
    user_secret = os.environ.get('DEV_USER_SECRET')
    project_id = os.environ.get('DEV_PROJECT_ID')

    if (project_id is None) or (user_id is None) or (user_secret is None):
        print('Missing environment variables. Did you run setenv?')
        sys.exit()

    access_token = authenticate(user_id, user_secret)
    
    create_job_with_files(access_token, project_id, JOB_NAME, [CONTENT_FILE_NAME], LOCALE_IDS, AUTHORIZE)

    # Upload context
    print('Uploading context')
    url = 'https://api.smartling.com/context-api/v2/projects/{0}/contexts'.format(project_id)

    headers = {'Authorization': 'Bearer ' + access_token}
    params = {
        'name': CONTEXT_FILE_URL
        }
    multipart_request_data = {
            '': '' # required to ensure requests send correct content type
        }
    resp = requests.post(url,
                        headers = headers,
                        data = params,
                        files = multipart_request_data)

    if resp.status_code != 200:
        print(resp.status_code)
        print(resp.text)
        sys.exit()

    print('Uploaded context URL.')
    context_uid = resp.json()['response']['data']['contextUid']


    # Match context to strings in the previously uploaded content file
    print('Initiating matching process restricted by file URI...')
    url = 'https://api.smartling.com/context-api/v2/projects/{0}/contexts/{1}/match/async'.format(project_id, context_uid)
    headers = {'Authorization': 'Bearer ' + access_token}
    params = {
        'contentFileUri': CONTENT_FILE_NAME  # we used the file name as the URI when uploading
        }
    resp = requests.post(url,
                        headers = headers,
                        json = params)

    if resp.status_code not in [200, 202]:
        print(resp.status_code)
        print(resp.text)
        sys.exit()

    match_id = resp.json()['response']['data']['matchId']

    # Check matching progress
    print('Context matching process initiated; checking match status...')
    url = 'https://api.smartling.com/context-api/v2/projects/{0}/match/{1}'.format(project_id, match_id)
    headers = {'Authorization': 'Bearer ' + access_token}
    resp = requests.get(url, headers = headers)
    if resp.status_code != 200:
        print(resp.status_code)
        print(resp.text)
        sys.exit()

    match_status = resp.json()['response']['data']['status']

    while match_status != 'COMPLETED':
        print('Waiting for matching to complete; status = ' + match_status)
        time.sleep(5)
        resp = requests.get(url, headers = headers)
        if resp.status_code != 200:
            print(resp.status_code)
            print(resp.text)
            sys.exit()
        match_status = resp.json()['response']['data']['status']

    bindings = resp.json()['response']['data']['bindings']
    print('Matching completed. Number of matches: {0}. \nReview results in Dashboard.'.format(len(bindings)))



if __name__ == '__main__':
    main()


