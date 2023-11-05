#!/usr/bin/env python3
# pylint: disable= line-too-long, missing-function-docstring,missing-class-docstring, invalid-name,  broad-exception-raised, unused-import,missing-timeout
from typing import Dict, List, Tuple
import os
import json
from datetime import date, timedelta
import requests
import pandas as pd
import matplotlib.pyplot as plt

# PATS RESTfull api usage example. Perform the following steps:
# 1. Choose the server
# 2. Create a .auth file with the pats-c user on the first line and password one the second line
# 3. Run this script
# 4. Profit

beta_server_dns = 'https://beta.pats-c.com/'
main_server_dns = 'https://pats-c.com/'
pats_local_testing = 'http://127.0.0.1:5000/'
server = beta_server_dns


def read_creds() -> Tuple[str, str]:
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


def download_detection_classes(session: requests.sessions.Session) -> Dict:
    headers = {'Content-Type': 'application/json'}
    response = session.get(server + 'api/detection_classes', headers=headers)
    if response.status_code != 200:
        raise Exception('Download insect table failed: ' + str(response.status_code) + ' msg: ' + response.text)
    return json.loads(response.text)['detection_classes']


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


def download_counts(session: requests.sessions.Session, section_id: int, detection_class_ids: List[int], start_date: date, end_date: date) -> Dict:
    headers = {'Content-Type': 'application/json'}
    data = {
        'section_id': section_id,
        'start_date': start_date.strftime('%Y%m%d'),
        'end_date': end_date.strftime('%Y%m%d'),
        'detection_class_ids': detection_class_ids,  # optional. Defaults to None, in which case all available counts are returned
    }
    response = session.get(server + 'api/counts', headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        raise Exception('Download counts failed: ' + str(response.status_code) + ' msg: ' + response.text)

    return json.loads(response.text)


def example_c_plot(counts: Dict, section: Dict, insect_table: Dict) -> None:
    for patsc in counts['c']:
        df = pd.DataFrame.from_records(patsc['counts'])
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        df = df.set_index('date')
        plt.figure()
        for insect_id in df.columns:
            insect = insect_table[insect_id]
            df[insect_id].plot(label=insect['label'])

        label = section['customer_name'] + ' '
        if section['greenhouse_name'] is not None:
            label += section['greenhouse_name'] + ' '
        if section['name'] is not None:
            label += section['name']
        label = label.strip()
        plt.title(f"PATS-C @ {label} row {patsc['row_id']} post {patsc['post_id']}")
        plt.xlabel('Date')
        plt.ylabel('Insect flights')
        plt.legend()


def example_trapeye_plot(counts: Dict, section: Dict, insect_table: Dict) -> None:
    trapeye = counts['trapeye'][0]
    df = pd.DataFrame.from_records(trapeye['new_counts'])
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df = df.set_index('date')
    plt.figure()
    for insect_id in df.columns:
        insect = insect_table[insect_id]
        df[insect_id].plot(label=insect['label'] + ' (' + insect['bb_label'] + ')')

    label = section['customer_name'] + ' '
    if section['greenhouse_name'] is not None:
        label += section['greenhouse_name'] + ' '
    if section['name'] is not None:
        label += section['name']
    label = label.strip()
    plt.title(f"Trap-Eye @ {label} row {trapeye['row_id']} post {trapeye['post_id']}")
    plt.xlabel('Date')
    plt.ylabel('Insects new on the card')
    plt.legend()


if __name__ == "__main__":
    session = requests.Session()
    login(session)

    insect_table = download_detection_classes(session)  # download a dict of dicts with all our insects (and rats, birds, ...). In the sections you can find which insects are actually available.
    sections = download_sections(session)  # download all sections meta data list of dicts
    section = sections[0]  # just a random section for the example
    insect_ids = [d['id'] for d in section['detection_classes']]
    spots = download_spots(session, section['id'])  # download two dicts (trap-eyes and c systems) listing all spots for this section.
    counts = download_counts(session, section['id'], insect_ids, date.today() - timedelta(days=100), date.today())  # download the counts for all spots in the section, for the selected insect(s), for the selected date range

    example_c_plot(counts, section, insect_table)
    example_trapeye_plot(counts, section, insect_table)

    plt.show(block=True)
