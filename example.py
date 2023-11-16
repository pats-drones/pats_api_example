#!/usr/bin/env python3
# pylint: disable= line-too-long, missing-function-docstring,missing-class-docstring, invalid-name,  broad-exception-raised, unused-import,missing-timeout
from typing import Dict, List, Tuple
from io import BytesIO
import os
import json
from datetime import date, datetime, timedelta
from PIL import Image
import requests
import pandas as pd
import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D
# PATS RESTfull api usage example. Perform the following steps:
# 1. Choose the server
# 2. Create a .auth file with the pats-c user on the first line and password one the second line
# 3. Run this script
# 4. Profit

beta_server_dns = 'https://beta.pats-c.com/'
main_server_dns = 'https://pats-c.com/'
pats_local_testing = 'http://127.0.0.1:5000/'
server = pats_local_testing


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


def download_trapeye_photo_list(session: requests.sessions.Session, section_id: int, row_id: int, post_id: int, start_date: date, end_date: date) -> Image:
    headers = {'Content-Type': 'application/json'}
    data = {
        'section_id': str(section_id),
        'row_id': str(row_id),
        'post_id': str(post_id),
        'start_date': start_date.strftime('%Y%m%d'),
        'end_date': end_date.strftime('%Y%m%d'),
    }
    response = session.get(server + 'api/trapeye_photo_list', headers=headers, data=json.dumps(data))

    if response.status_code != 200:
        raise Exception('Download photo list failed: ' + str(response.status_code) + ' msg: ' + response.text)

    return json.loads(response.text)['photos']


def download_trapeye_photo(session: requests.sessions.Session, section_id: int, row_id: int, post_id: int, datetime_str: str) -> Image:
    headers = {'Content-Type': 'application/json'}
    data = {
        'section_id': str(section_id),
        'row_id': str(row_id),
        'post_id': str(post_id),
        'datetime': datetime_str,
    }
    response = session.post(server + 'api/download_trapeye_photo', headers=headers, data=json.dumps(data))

    if response.status_code != 200:
        raise Exception('Download photo failed: ' + str(response.status_code) + ' msg: ' + response.text)

    return Image.open(BytesIO(response.content))


def download_c_detection_features(session: requests.sessions.Session, section_id: int, row_id: int, post_id: int, detection_class_id: int, start_datetime: datetime, end_datetime: datetime) -> Image:
    headers = {'Content-Type': 'application/json'}
    data = {
        'section_id': str(section_id),
        'row_id': str(row_id),
        'post_id': str(post_id),
        'detection_class_id': str(detection_class_id),
        'start_datetime': start_datetime.strftime('%Y%m%d_%H%M%S'),
        'end_datetime': end_datetime.strftime('%Y%m%d_%H%M%S'),
    }
    response = session.get(server + 'api/download_detection_features', headers=headers, data=json.dumps(data))

    if response.status_code != 200:
        raise Exception('Download c data failed: ' + str(response.status_code) + ' msg: ' + response.text)

    return pd.DataFrame.from_records(json.loads(response.text)['data'])


def download_c_flight_track(session: requests.sessions.Session, section_id: int, detection_uid: int) -> Image:
    headers = {'Content-Type': 'application/json'}
    data = {
        'section_id': str(section_id),
        'detection_uid': str(detection_uid),
    }
    response = session.get(server + 'api/download_c_flight_track', headers=headers, data=json.dumps(data))

    if response.status_code != 200:
        raise Exception('Download flight track failed: ' + str(response.status_code) + ' msg: ' + response.text)

    return pd.DataFrame.from_records(json.loads(response.text)['data'])


def download_c_video(session: requests.sessions.Session, section_id: int, detection_uid: int) -> Image:
    headers = {'Content-Type': 'application/json'}
    data = {
        'section_id': str(section_id),
        'detection_uid': str(detection_uid),
        'convert_to_mp4': False,  # optional, defaults to False
        'raw_stereo': False  # optional, defaults to False
    }
    response = session.get(server + 'api/download_c_video', headers=headers, data=json.dumps(data))

    if response.status_code != 200:
        raise Exception('Download flight track failed: ' + str(response.status_code) + ' msg: ' + response.text)

    return response.content


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


def example_c_scatter_plot(detections_df: pd.DataFrame, insect_class: Dict):
    plt.figure(figsize=(10, 6))
    plt.scatter(detections_df['duration'], detections_df['size'])
    plt.title(f'PATS-C {insect_class["label"]} detections')
    plt.xlabel('Duration [s]')
    plt.ylabel('Size [m]')
    plt.grid(True)


def example_c_flight_3d_plot(df_flight: pd.DataFrame):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(df_flight['sposX_insect'], df_flight['sposY_insect'], df_flight['sposZ_insect'])

    ax.set_xlabel('X Position')
    ax.set_ylabel('Y Position')
    ax.set_zlabel('Z Position')


if __name__ == "__main__":
    with requests.Session() as session:
        login(session)
        insect_table = download_detection_classes(session)  # download a dict of dicts with all our insects (and rats, birds, ...). In the sections you can find which insects are actually available.
        sections = download_sections(session)  # download all sections meta data list of dicts
        section = sections[0]  # just a random section for the example
        insect_ids = [d['id'] for d in section['detection_classes']]
        spots = download_spots(session, section['id'])  # download two dicts (trap-eyes and c systems) listing all spots for this section.
        counts = download_counts(session, section['id'], insect_ids, date.today() - timedelta(days=100), date.today())  # download the counts for all spots in the section, for the selected insect(s), for the selected date range

        example_c_plot(counts, section, insect_table)
        example_trapeye_plot(counts, section, insect_table)

        # up to this point Trap-Eye and PATS-C data is virtually the same. However when we go lower TrapEye periodically photographes a bulk and PATS-C stereo-video records individuals.

        # First, let's get an image from a Trap-Eye
        if spots['trapeye']:
            row_id = spots['trapeye'][0]['row_id']  # just a random row and post for the example
            post_id = spots['trapeye'][0]['post_id']
            photo_list = download_trapeye_photo_list(session, section['id'], row_id, post_id, date.today() - timedelta(days=100), date.today())
            image = download_trapeye_photo(session, section['id'], row_id, post_id, photo_list[0])
            image.show()

        # Now, let's go get a flight track and video from PATS-C
        if spots['c']:
            # just a random row, post and insect for the example
            row_id = spots['c'][0]['row_id']
            post_id = spots['c'][0]['post_id']
            insect_class: Dict = next((item for item in section['detection_classes'] if item['available_in_c']), {})

            start_datetime = (datetime.today() - timedelta(days=100)).replace(hour=12, minute=0, second=0, microsecond=0)
            end_datetime = (datetime.today() - timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
            df_detections = download_c_detection_features(session, section['id'], row_id, post_id, insect_class['id'], start_datetime, end_datetime)
            example_c_scatter_plot(df_detections, insect_class)
            some_insect = df_detections['uid'].iloc[0]
            df_flight = download_c_flight_track(session, section['id'], some_insect)
            example_c_flight_3d_plot(df_flight)
            mkv_data = download_c_video(session, section['id'], some_insect)  # Warning: this can easily take over a minute. The render is being done on demand on the edge. Also, there are concurrency issues. Only one render per edge system may be done at the same time.
            with open("temp_video.mkv", "wb") as file:
                file.write(mkv_data)  # open with any normal video player, e.g. vlc

    plt.show(block=True)
