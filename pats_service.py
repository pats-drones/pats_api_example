# file: pats_service.py
import json
import logging
import sys
from datetime import datetime
from io import BytesIO
from typing import List, Optional

import pandas as pd
import requests
from PIL import Image


class PatsServiceError(Exception):
    pass


class PatsService:
    def __init__(
        self,
        user: str,
        passw: str,
        server: str = "https://pats-c.com",
        # server: str = "https://beta.pats-c.com", # beta server: be aware, not stable and used for experimental stuff
        # server: str = "http://127.0.0.1:5000",  # local testing
        timeout: int = 45,
    ):
        """Constructor method for the "PatsService" class.
        Takes care of retrieving the access_token.

        Args:
            user (str): username of the account from where we are retrieving information.
            passw (str): password of the account from where we are retrieving information.
            server (str, optional): URL to the server. Defaults to "https://pats-c.com".
            timeout(int, optional): number of seconds before any requests made to the server will timeout. Defaults to 45 seconds.
        """
        self.logger = logging.getLogger(name="log")
        self.server: str = server
        self.timeout: int = timeout
        self.token: str = self.__retrieve_token_from_server(user, passw, server)

    def __retrieve_token_from_server(self, user: str, passw: str, server: str) -> str:
        """Private method to retrieve api token from server.
        If retrieving the token fails, the program exits with exit code 1.
        As there is no way to gracefully recover.

        Args:
            user (str): username of the account from which the token is to be retrieved.
            passw (str): password of the account from which the token is to be retrieved.
            server (str): the url to the server.

        Returns:
            str: the access token, that can be used for GET requests.
        """
        self.logger.debug("Retrieving token from pats server")

        # Initialize header.
        request_body = {"username": user, "password": passw}

        # Send request, and validate response code.
        response = requests.post(server + "/token", request_body, timeout=self.timeout)
        if response.status_code != 200:
            self.logger.critical(
                f"Retrieving token from server failed: {response.status_code!s}, msg: {response.text}",
                exc_info=True,
            )
            sys.exit(1)

        self.logger.info(f"Successfully retrieved API token from server: {self.server}")
        return response.json()["access_token"]

    def download_detection_classes(self) -> dict:
        """Download detection classes from pats server.
        Detection classes are insects (and rats, birds, ect.) from pats.
        Via the "sections" endpoint you can find out which are actually available.

        json example:
            {
                "detection_classes": {
                    "1": {
                        "bb_label": null,
                        "id": 1,
                        "label": "Chrysodeixis chalcites",
                        "short_name": "Tomato looper / Turkse mot"
                    },
                    "2": {
                        "bb_label": "ta",
                        "id": 3,
                        "label": "Tuta absoluta",
                        "short_name": "Tomato leafminer"
                    }
                }
            }

        Returns:
            dict: dict containing all detection classes in json format.
                    An example of the format can be found above.

        """
        self.logger.debug("Retrieving detection classes from pats server")

        # Initialize headers.
        headers = {"Authorization": "Bearer " + self.token}

        # Send request, and validate response code.
        response = requests.get(self.server + "/api/detection_classes", headers=headers, timeout=self.timeout)
        if response.status_code != 200:
            self.logger.critical(f"Download detection classes failed: {response.status_code!s}, msg: {response.text}")
            sys.exit(1)

        self.logger.info("Successfully retrieved detection classes from pats server")
        return response.json()["detection_classes"]

    def download_sections(self) -> dict:
        """Download sections from pats server.
        Sections contain a lot of meta data.

        json example:
            {
                "sections": [
                    {
                        "crop": "some_crop",
                        "customer_name": "company_name",
                        "detection_classes": [
                            {
                                "available_in_c": 0,
                                "available_in_trapeye": 1,
                                "bb_label": "ta",
                                "beneficial": 0,
                                "c_level_1": 5,
                                "c_level_2": 15,
                                "c_level_3": 30,
                                "c_level_4": 50,
                                "id": 3,
                                "label": "Tuta absoluta",
                                "short_name": "Tomato leafminer",
                                "trapeye_level_1": 1,
                                "trapeye_level_2": 5,
                                "trapeye_level_3": 10,
                                "trapeye_level_4": 15
                            },
                        ],
                        "greenhouse_name": "your_greenhouse_name",
                        "hubspot_company_id": 0123456789,
                        "id": 123,
                        "label": "section_label",
                        "n_weekly_trapeye_photos": 3,
                        "name": "a_name",
                        "timezone": "Europe/Amsterdam"
                    }
                ]
            }
        }

        Returns:
            dict: dict containing all sections. Each section contains meta data about it self,
                  and a list of detection classes available to that section.
        """
        self.logger.debug("Retrieving sections from pats server")

        # Initialize headers.
        headers = {"Authorization": "Bearer " + self.token}

        # Send request, and validate response code.
        response = requests.get(self.server + "/api/sections", headers=headers, timeout=self.timeout)
        if response.status_code != 200:
            self.logger.critical(f"Download sections failed: {response.status_code!s}, msg: {response.text}")
            sys.exit(1)

        self.logger.info("Successfully sections from pats server")
        return json.loads(response.text)["sections"]
        # return response.json()['sections'] # this doesn't work for me? Maybe a python 3.10 issue?

    def download_spots(self, section_id: int, snapping_mode: str = "disabled") -> dict:
        """Method used to download the spots from the Pats server.
        The json consists of two dictionaries, the first containing the spots for c systems,
        and the second containing spots for trapeye systems.

        json example:
            {
                "c": [
                    {
                        "label": "a_label",
                        "latitude": 12.3456789,
                        "longitude": 9.8765432,
                        "post_id": 21,
                        "row_id": 42,
                        "system_id": 123
                    },
                ],
                 "trapeye": [
                    {
                        "latitude": 98.76543210987654,
                        "longitude": 1.2345678901234,
                        "post_id": 42,
                        "row_id": 21,
                        "unit_id": 9876
                    },
                ]
            }

        Args:
            section_id (int, optional): the id of the section for which the spots will be downloaded.
            snapping_mode(str, optional): sets the map snapping mode on the hand placed location of sensors. Defaults to 'disabled'. Options:
                'auto': automatic selection between row/post mode
                'row': snap using the assumption most trapeyes are placed in rows
                'post': snap using the assumption most trapeyes are placed in posts
                'disabled': no snapping, return orignaly scanned gps locations
            map_snapping(int, optional): to be deprecated in a future release in favor of snapping_mode

        Returns:
            dict: a dict containing the json response body.
        """
        self.logger.debug("Downloading spots from pats server")

        # Initialize header and request body.
        headers = {"Authorization": "Bearer " + self.token}
        params = {"section_id": str(section_id), "snapping_mode": snapping_mode}

        # Send request, and validate response code.
        response = requests.get(self.server + "/api/spots", headers=headers, params=params, timeout=self.timeout)
        if response.status_code != 200:
            self.logger.critical(
                f"Download spots failed: {response.status_code}, msg: {response.text}",
                exc_info=True,
            )
            sys.exit(1)

        self.logger.info("Successfully retrieved spots from pats servers")
        return response.json()

    def download_counts(
        self,
        start_date: datetime,
        end_date: datetime,
        section_id: int,
        detection_class_ids: List[int],
        bin_mode: str = "D",
        average_24h_bin: bool = False,
    ):
        """Method used to download counts from the Pats server.
        The datetime format received from the pats server is: "%Y%m%d_%H%M%S".

        Note that the in the trapeye measurements, the first absolute count has NaN values in the diff rows.
        This is because the difference is the difference between the previous absolute count, and the new one. If there is not
        a previous absolute count NaN will be returned.
        The same explanation for new counts. This gets calculated with the diff between two absolute counts.

        json example:
            {
                "c": [
                    {
                        "counts": [
                            {
                                "1": 0,
                                "2": 0,
                                "datetime": "20240708_120000"
                            },
                            {
                                "1": 0,
                                "2": 0,
                                "datetime": "20240708_130000"
                            },
                        ],
                        "post_id": 21,
                        "row_id": 42
                    }
            ],
                "trapeye": [
                    {
                        "absolute_count": [
                            {
                                "24": 1.0,
                                "25": 0.0,
                                "26": 0.0,
                                "27": 0.0,
                                "28": 8.0,
                                "3": 0.0,
                                "date": "20240709",
                                "lir_diff": NaN,
                                "mr_diff": NaN,
                                "nc_diff": NaN,
                                "ta_diff": NaN,
                                "tr_diff": NaN,
                                "wv_diff": NaN
                            },
                            {
                                "24": 1.0,
                                "25": 0.0,
                                "26": 0.0,
                                "27": 0.0,
                                "28": 8.0,
                                "3": 0.0,
                                "date": "20240711",
                                "lir_diff": 0.0,
                                "mr_diff": 0.0,
                                "nc_diff": 0.0,
                                "ta_diff": 0.0,
                                "tr_diff": 0.0,
                                "wv_diff": 0.0
                            },
                        ],
                        "new_counts": [
                            {
                                "24": NaN,
                                "25": NaN,
                                "26": NaN,
                                "27": NaN,
                                "28": NaN,
                                "3": NaN,
                                "date": "20240709"
                            },
                            {
                                "24": 0.0,
                                "25": 0.0,
                                "26": 0.0,
                                "27": 0.0,
                                "28": 0.0,
                                "3": 0.0,
                                "date": "20240711"
                            },
                        ],
                        "post_id": 2,
                        "row_id": 34
                    },

        Args:
            start_date (datetime): start date from which the downloaded counts will start.
            end_date (datetime): end date to which counts will be downloaded.
            section_id (int, optional): id of the section for which counts will be downloaded.
            detection_class_ids (list[int], optional): list of insect ids, for which counts will be downloaded.
            bin_mode (str, optional): EITHER 'D' OR 'h'!! corresponds to daily or hourly binning respectively . Defaults to "D".
            average_24h_bin (bool, optional): boolean flag, whether to include daily insect distribution within
                                              the selected date range or not. Defaults to False.
            Following pandas, bin_mode 'H' will be deprecated in a future release

        Returns:
            dict: response body containing the counts in json format.
        """
        self.logger.debug("Retrieving counts from pats server")
        # Make sure all provided parameters are in the right format, and are the right type.
        section_id_str: str = str(section_id)
        start_date_formatted: str = start_date.strftime("%Y%m%d")
        end_date_formatted: str = end_date.strftime("%Y%m%d")
        detection_class_ids_str: str | None = ",".join(map(str, detection_class_ids)) if detection_class_ids else None
        average_24h_bin_num: int = int(average_24h_bin)

        # Initialize the header and request body.
        headers = {"Authorization": "Bearer " + self.token}
        params = {
            "section_id": section_id_str,
            "start_date": start_date_formatted,
            "end_date": end_date_formatted,
            "detection_class_ids": detection_class_ids_str,
            "bin_mode": bin_mode,
            "average_24h_bin": average_24h_bin_num,
        }

        # Send request, and validate response code.
        response = requests.get(self.server + "/api/counts", headers=headers, params=params, timeout=self.timeout)
        if response.status_code != 200:
            self.logger.critical(
                f"Download counts failed: {response.status_code}, msg: {response.text}",
                exc_info=True,
            )
            sys.exit(1)

        self.logger.info("Successfully retrieved counts from pats servers")
        return response.json()

    def download_trapeye_photo_list(self,
                                    section_id: int,
                                    row_id: int,
                                    post_id: int,
                                    start_date: datetime,
                                    end_date: datetime) -> list:
        """Download the list with available photos from the trapeye.

        json example:
            {
                "photos": [
                    "20240713_140300",
                    "20240713_120300",
                    "20240711_140300",
                    "20240711_120500",
                    "20240709_140200",
                ]
            }

        Args:
            section_id (int): the id of the section where the photos were taken.
            row_id (int): the row id of the sensor that took the photos.
            post_id (int): the post id of the sensor that took the photos.
            start_date (datetime): the earliest date of the returned photos.
            end_date (datetime): the latest date of the returned photos.

        Returns:
            list: list with names of the available photos. Names are in the format "%Y%m%d_%H%M%S".
        """
        self.logger.debug("Downloading trapeye photo list")
        start_date_formatted: str = start_date.strftime("%Y%m%d")
        end_date_formatted: str = end_date.strftime("%Y%m%d")

        # Initialize the header and request body.
        headers = {"Authorization": "Bearer " + self.token}
        params = {
            "section_id": str(section_id),
            "row_id": str(row_id),
            "post_id": str(post_id),
            "start_date": start_date_formatted,
            "end_date": end_date_formatted,
        }

        # Send request, and validate response code.
        response = requests.get(self.server + "/api/trapeye_photo_list", headers=headers, params=params, timeout=self.timeout)
        if response.status_code != 200:
            self.logger.critical(
                f"Download photo list failed: {response.status_code}, msg: {response.text}",
                exc_info=True,
            )
            sys.exit(1)

        self.logger.info("Successfully downloaded photo list from pats server")
        return response.json()["photos"]

    def download_trapeye_photo(self, section_id: int, row_id: int, post_id: int, photo_id: str) -> Image.Image:
        """Download a trapeye photo from pats, and open it.

        Args:
            section_id (int): the section in which the photo was taken.
            row_id (int): the id of the row the sensor that took the photo is located.
            post_id (int): the id of the post the sensor that took the photo is located.
            photo_id (str): the name of the photo, found in the photo list.

        Returns:
            Image.Image: the downloaded image.
        """
        self.logger.debug(f"Downloading trapeye photo: {photo_id}")
        # Initialize the header and request body.
        headers = {"Authorization": "Bearer " + self.token}
        params = {
            "section_id": str(section_id),
            "row_id": str(row_id),
            "post_id": str(post_id),
            "datetime": photo_id,
        }

        # Send request, and validate response code.
        response = requests.get(self.server + "/api/download_trapeye_photo", headers=headers, params=params, timeout=self.timeout)
        if response.status_code != 200:
            self.logger.critical(
                f"Download photo failed: {response.status_code}, msg: {response.text}",
                exc_info=True,
            )
            raise PatsServiceError(response.text)

        return Image.open(BytesIO(response.content))

    def download_c_detection_features(self,
                                      section_id: int,
                                      row_id: Optional[int],
                                      post_id: Optional[int],
                                      system_id: Optional[int],
                                      detection_class_id: int,
                                      start_date: datetime,
                                      end_date: datetime) -> pd.DataFrame:
        """Download c detection features from pats.
        The row_id, post_id and system_id are optional, this is to ensure backwards compatibility.
        The system_id's are legacy, and should be avoided. New behavior is the combination of row_id and post_id.

        The datetime in the response body is in the format "%Y%m%d_%H%M%S".
        All units are in SI base units.

        json example:
            {
                "data": [
                    {
                        "datetime": "20240708_222545",
                        "dist_traject": 3.3145574200059627,
                        "dist_traveled": 3.0434154152926607,
                        "duration": 2.5037559999998393,
                        "light_level": 0.22657637142857143,
                        "post_id": 21,
                        "row_id": 43,
                        "size": 0.014341787433628319,
                        "start_datetime": "Mon, 08 Jul 2024 20:25:45 GMT",
                        "uid": 012345678,
                        "vel_max": 1.7198010272426867,
                        "vel_mean": 1.2854506213467454,
                        "vel_std": 0.2336045734746302
                    },
                ]
            }

        Args:
            section_id (int): the id of the section where this c sensor is located.
            row_id (Optional[int]): the id of the row the sensor is located.
            post_id (Optional[int]): the id of the post the sensor is located.
            system_id (Optional[int]): deprecated! the id of the system that took the measurements.
            detection_class_id (int): the id of the detection class, these ids can be found via the "download_detection_classes" endpoint.
            start_date (datetime): the start date of the measurements, date of the earliest measurement.
            end_date (datetime): the end date of the measurements, date of the latest measurement.

        Returns:
            pd.DataFrame: pandas dataframe containing the information contained in data.
        """
        self.logger.debug("Retrieving c detection features")
        # Format the start and end date.
        start_date_formatted: str = start_date.strftime("%Y%m%d_%H%M%S")
        end_date_formatted: str = end_date.strftime("%Y%m%d_%H%M%S")

        # Initialize the header and request body.
        headers = {"Authorization": "Bearer " + self.token}
        params = {}

        # system_id is legacy code, this if statement is to ensure backward compatibility.
        # The preferred body is the one with a row and post id.
        if system_id is None:
            params = {
                "section_id": str(section_id),
                "row_id": str(row_id),
                "post_id": str(post_id),
                "detection_class_id": str(detection_class_id),
                "start_datetime": start_date_formatted,
                "end_datetime": end_date_formatted,
            }
        else:
            params = {
                "section_id": str(section_id),
                "system_id": str(system_id),
                "detection_class_id": str(detection_class_id),
                "start_datetime": start_date_formatted,
                "end_datetime": end_date_formatted,
            }

        # Send request, and validate response code.
        response = requests.get(self.server + "/api/download_detection_features", headers=headers, params=params, timeout=self.timeout)
        if response.status_code != 200:
            self.logger.critical(
                f"Download c detection features failed: {response.status_code}, msg: {response.text}",
                exc_info=True,
            )
            sys.exit(1)

        self.logger.info("Successfully downloaded c detection features")
        return pd.DataFrame.from_records(response.json()["data"])

    def download_c_flight_track(self, section_id: int, detection_uid: int) -> pd.DataFrame:
        """Download c flight track from pats server.

        All units are in SI standard base units.

        json example:
            {
                "data": [
                    {
                        "Unnamed: 32": NaN,
                        "acc_valid_insect": 0,
                        "disparity_insect": 20.8008,
                        "elapsed": 1207.1165,
                        "foundL_insect": 1,
                        "fp": "fp_not_a_fp",
                        "hunt_id": -1,
                        "imLx_insect": 28,
                        "imLx_pred_insect": -1.0,
                        "imLy_insect": 268,
                        "imLy_pred_insect": -1.0,
                        "light_level": 0.226651,
                        "motion_sum_insect": 36,
                        "n_frames_lost_insect": 0,
                        "n_frames_tracking_insect": 1,
                        "posX_insect": 1.8169,
                        "posY_insect": -1.227,
                        "posZ_insect": -1.52218,
                        "pos_valid_insect": 1,
                        "radius_insect": 0.0102218,
                        "rs_id": 108478,
                        "saccX_insect": 0.0,
                        "saccY_insect": 0.0,
                        "saccZ_insect": 0.0,
                        "score_insect": 0.0,
                        "size_insect": 4.47214,
                        "sposX_insect": 1.8169,
                        "sposY_insect": -1.227,
                        "sposZ_insect": -1.52218,
                        "svelX_insect": 0.0,
                        "svelY_insect": 0.0,
                        "svelZ_insect": 0.0,
                        "vel_valid_insect": 0
                    },
                ]
            }


        Args:
            section_id (int): the id of the section where the detection took place.
            detection_uid (int): the unique id of the detection.

        Returns:
            pd.DataFrame: pandas dataframe containing the information contained in data.
        """
        self.logger.debug("Retrieving c flight track")
        # Initialize the header and request body.
        headers = {"Authorization": "Bearer " + self.token}
        params = {
            "section_id": str(section_id),
            "detection_uid": str(detection_uid),
        }

        # Send request, and validate response code.
        response = requests.get(self.server + "/api/download_c_flight_track", headers=headers, params=params, timeout=self.timeout)
        if response.status_code != 200:
            self.logger.critical(
                f"Download c flight track failed: {response.status_code}, msg: {response.text}",
                exc_info=True,
            )
            sys.exit(1)

        self.logger.info(f"Successfully downloaded c flight track from: {detection_uid}")
        return pd.DataFrame.from_records(response.json()["data"])

    def download_c_video(self, section_id: int, detection_uid: int, raw_stereo: bool = False) -> bytes:
        """Download c video from pats.

        Args:
            section_id (int): the id of the section where the detection was done.
            detection_uid (int): the unique id of a detection from which the video will be downloaded.
            raw_stereo (bool, optional): flag to enable requesting the raw stereo. Defaults to False.

        Returns:
            bytes: the requested video.
        """
        self.logger.debug("Retrieving c video from pats")
        raw_stereo_num: int = int(raw_stereo)

        # Initialize the header and request body.
        headers = {"Authorization": "Bearer " + self.token}
        params = {
            "section_id": str(section_id),
            "detection_uid": str(detection_uid),
            "raw_stereo": str(raw_stereo_num)
        }

        # Send request, and validate response code.
        response = requests.get(self.server + "/api/download_c_video", headers=headers, params=params, timeout=self.timeout)
        if response.status_code != 200:
            self.logger.critical(
                f"Download c video failed: {response.status_code}, msg: {response.text}",
                exc_info=True,
            )
            sys.exit(1)

        self.logger.info(f"Successfully downloaded c video from detection: {detection_uid}")
        return response.content
