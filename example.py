#!/usr/bin/env python3
# pylint: disable= line-too-long, missing-function-docstring,missing-class-docstring, invalid-name,  broad-exception-raised, unused-import,missing-timeout
from typing import Dict, List
import os
import json
import pandas as pd
from datetime import date
import requests

# PATS RESTfull api usage example. Perform the following steps:
# 1. Choose the server
# 2. Create a .auth file with the pats-c user on the first line and password one the second line
# 3. Run this script
# 4. Profit

beta_server_dns = 'https://beta.pats-c.com/'
main_server_dns = 'https://pats-c.com/'
pats_local_testing = 'http://127.0.0.1:5000/'
server = beta_server_dns


def read_creds():
    cred_file = './.auth'
    if os.path.exists(cred_file):
        with open(cred_file, 'r', encoding='utf-8') as creds_file:
            user = creds_file.readline().strip()
            passw = creds_file.readline().strip()
            return user, passw
    else:
        raise Exception('Error: Super secret .auth authorization not found')


def login(session: requests.sessions.Session) -> None:
    user, passw = read_creds()
    headers = {'Content-Type': 'application/json'}
    data = {
        'username': user,
        'password': passw,
    }
    response = session.post(server + 'login', data=json.dumps(data), headers=headers)
    if response.status_code != 200:
        raise Exception('Login failed: ' + str(response.status_code) + ' msg: ' + response.text)
    elif response.text != 'OK':
        raise Exception('Login failed: ' + response.text)


def download_sections(session: requests.sessions.Session) -> List[Dict]:
    headers = {'Content-Type': 'application/json'}
    response = session.get(server + 'api/sections', headers=headers)
    if response.status_code != 200:
        raise Exception('Download sections failed: ' + str(response.status_code) + ' msg: ' + response.text)
    return json.loads(response.text)['sections']


def download_spots(session: requests.sessions.Session, section_id: int) -> Dict:
    headers = {'Content-Type': 'application/json'}
    data = {
        'section_id': section_id,
        'map_snapping': 1,  # optional: defaults to 0
    }
    response = session.get(server + 'api/spots', headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        raise Exception('Download spots failed: ' + str(response.status_code) + ' msg: ' + response.text)

    return json.loads(response.text)


def download_counts(session: requests.sessions.Session, section_id: int, d: date) -> Dict:
    headers = {'Content-Type': 'application/json'}
    data = {
        'section_id': section_id,
        'date': d.strftime('%Y%m%d'),  # optional. Defaults to today.
    }
    response = session.get(server + 'api/counts', headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        raise Exception('Download counts failed: ' + str(response.status_code) + ' msg: ' + response.text)

    return json.loads(response.text)


if __name__ == "__main__":
    s = requests.Session()
    login(s)
    sections = download_sections(s)
    spots = download_spots(s, sections[0]['id'])
    print(pd.DataFrame.from_records(spots['trapeyes']))
    counts = download_counts(s, sections[0]['id'], date.today())
    print(pd.DataFrame.from_records(counts))
