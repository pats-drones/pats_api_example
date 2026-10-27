# file: pats_service.py
import logging
from datetime import datetime
from io import BytesIO
from typing import List

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
        self.server: str = server.rstrip("/")
        self.timeout: int = timeout
        self.session = requests.Session()
        self.token: str = self.__retrieve_token_from_server(user, passw)
        self.session.headers.update({"Authorization": "Bearer " + self.token})

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        try:
            response = self.session.request(method, self.server + path, timeout=self.timeout, allow_redirects=False, **kwargs)
        except requests.RequestException as exc:
            raise PatsServiceError(f"{method} {path} failed ({type(exc).__name__}); check connectivity or increase timeout.") from None
        if response.status_code != 200:
            raise PatsServiceError(f"{method} {path} failed (HTTP {response.status_code}); check credentials, section access and request parameters.")
        return response

    def __retrieve_token_from_server(self, user: str, passw: str) -> str:
        """Private method to retrieve api token from server.
        Raises PatsServiceError if authentication fails.

        Args:
            user (str): username of the account from which the token is to be retrieved.
            passw (str): password of the account from which the token is to be retrieved.

        Returns:
            str: the access token, that can be used for GET requests.
        """
        self.logger.debug("Retrieving token from pats server")

        # Initialize header.
        request_body = {"username": user, "password": passw}

        # Send request and check the HTTP status.
        response = self._request("POST", "/token", data=request_body)

        token = response.json().get("access_token")
        if not isinstance(token, str) or not token:
            raise PatsServiceError("POST /token returned no access token.")
        self.logger.info(f"Successfully retrieved API token from server: {self.server}")
        return token

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

        # Send request and check the HTTP status.
        response = self._request("GET", "/api/v2/detection_classes")

        self.logger.info("Successfully retrieved detection classes from pats server")
        return response.json()["detection_classes"]

    def download_sections(self) -> list:
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
                        "id": 123,
                        "label": "section_label",
                        "n_weekly_trapeye_photos": 3,
                        "n_weekly_trapeye_photos_contract": 3,
                        "name": "a_name",
                        "timezone": "Europe/Amsterdam"
                    }
                ]
            }
        }

        Returns:
            list: list containing all sections. Each section contains meta data about itself,
                  and a list of detection classes available to that section.
        """
        self.logger.debug("Retrieving sections from pats server")

        # Send request and check the HTTP status.
        response = self._request("GET", "/api/v2/sections")

        self.logger.info("Successfully sections from pats server")
        return response.json()["sections"]

    def download_spots(self, section_id: int, snapping_mode: str = "disabled") -> dict:
        """Method used to download the spots from the Pats server.
        The JSON contains lists grouped as c, trapeye, marker and gateway.

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
            section_id (int): the id of the section for which the spots will be downloaded.
            snapping_mode (str, optional): retained for caller compatibility; ignored by the v2 API.
                Locations are returned as stored by the server.

        Returns:
            dict: a dict containing the json response body.
        """
        self.logger.debug("Downloading spots from pats server")

        # Initialize query parameters.
        params = {"section_id": str(section_id)}

        # Send request and check the HTTP status.
        response = self._request("GET", "/api/v2/spots", params=params)

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

        # Initialize query parameters.
        params = {
            "section_id": section_id_str,
            "start_date": start_date_formatted,
            "end_date": end_date_formatted,
            "detection_class_ids": detection_class_ids_str,
            "bin_mode": bin_mode,
            "average_24h_bin": average_24h_bin_num,
        }

        # Send request and check the HTTP status.
        response = self._request("GET", "/api/v2/counts", params=params)

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

        # Initialize query parameters.
        params = {
            "section_id": str(section_id),
            "row_id": str(row_id),
            "post_id": str(post_id),
            "start_date": start_date_formatted,
            "end_date": end_date_formatted,
        }

        # Send request and check the HTTP status.
        response = self._request("GET", "/api/v2/trapeye_photo_list", params=params)

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
        # Initialize query parameters.
        params = {
            "section_id": str(section_id),
            "row_id": str(row_id),
            "post_id": str(post_id),
            "datetime": photo_id,
        }

        # Send request and check the HTTP status.
        response = self._request("GET", "/api/v2/download_trapeye_photo", params=params)

        return Image.open(BytesIO(response.content))

    def download_c_detection_features(self,
                                      section_id: int,
                                      row_id: int,
                                      post_id: int,
                                      detection_class_id: int,
                                      start_date: datetime,
                                      end_date: datetime) -> pd.DataFrame:
        """Download c detection features from pats.
        Both row_id and post_id are required integers.

        Request times and the response's datetime field use "%Y%m%d_%H%M%S" in the section timezone.
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
            row_id (int): the id of the row the sensor is located.
            post_id (int): the id of the post the sensor is located.
            detection_class_id (int): the id of the detection class, these ids can be found via the "download_detection_classes" endpoint.
            start_date (datetime): the start date of the measurements, date of the earliest measurement.
            end_date (datetime): the end date of the measurements, date of the latest measurement.

        Returns:
            pd.DataFrame: pandas dataframe containing the information contained in data.
        """
        if any(not isinstance(value, int) or isinstance(value, bool) for value in (row_id, post_id)):
            raise ValueError("row_id and post_id must be integers for detection features.")
        self.logger.debug("Retrieving c detection features")
        # Format the start and end date.
        start_date_formatted: str = start_date.strftime("%Y%m%d_%H%M%S")
        end_date_formatted: str = end_date.strftime("%Y%m%d_%H%M%S")

        # Initialize query parameters.
        params = {
            "section_id": str(section_id),
            "row_id": str(row_id),
            "post_id": str(post_id),
            "detection_class_id": str(detection_class_id),
            "start_datetime": start_date_formatted,
            "end_datetime": end_date_formatted,
        }

        # Send request and check the HTTP status.
        response = self._request("GET", "/api/v2/download_detection_features", params=params)

        self.logger.info("Successfully downloaded c detection features")
        return pd.DataFrame.from_records(response.json()["data"])

    def download_c_flight_track(self, section_id: int, detection_uid: int) -> pd.DataFrame:
        """Download c flight track from pats server.

        All units are in SI standard base units.

        json example:
            {
                "data": [
                    {
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
        # Initialize query parameters.
        params = {
            "section_id": str(section_id),
            "detection_uid": str(detection_uid),
        }

        # Send request and check the HTTP status.
        response = self._request("GET", "/api/v2/download_c_flight_track", params=params)

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

        # Initialize query parameters.
        params = {
            "section_id": str(section_id),
            "detection_uid": str(detection_uid),
            "raw_stereo": str(raw_stereo_num)
        }

        # Send request and check the HTTP status.
        response = self._request("GET", "/api/v2/download_c_video", params=params)

        self.logger.info(f"Successfully downloaded c video from detection: {detection_uid}")
        return response.content
