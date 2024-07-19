from datetime import datetime
import sys
import logging
import requests


class PatsService:
    def __init__(
        self,
        user: str,
        passw: str,
        server: str = "https://beta.pats-c.com",
        timeout: int = 3,
    ):
        """Constructor method for the "PatsService" class.
        Takes care of retrieving the access_token.

        Args:
            user (str): username of the account from where we are retrieving information.
            passw (str): password of the account from where we are retrieving information.
            server (str, optional): URL to the server. Defaults to "https://beta.pats-c.com".
            timeout(int, optional): number of seconds before any requests made to the server will timout.
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
                f"Retrieving token from server failed: {str(response.status_code)}, msg: {response.text}",
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
        headers = {'Authorization': 'Bearer ' + self.token}

        # Send request, and validate response code.
        response = requests.get(self.server + '/api/detection_classes', headers=headers, timeout=self.timeout)
        if response.status_code != 200:
            self.logger.critical(f"Download detection classes failed: {str(response.status_code)}, msg: {response.text}")
            sys.exit(1)

        self.logger.info("Sucessfully retrieved detection classes from pats server")
        return response.json()['detection_classes']

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
                                "benificial": 0,
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
            dict: dict containg all sections. Each section contains meta data about it self,
                  and a list of detection classes available to that section.
        """
        self.logger.debug("Retrieving sections from pats server")

        # Initialize headers.
        headers = {'Authorization': 'Bearer ' + self.token}

        # Send request, and validate response code.
        response = requests.get(self.server + '/api/detection_classes', headers=headers, timeout=self.timeout)
        if response.status_code != 200:
            self.logger.critical(f"Download sections failed: {str(response.status_code)}, msg: {response.text}")
            sys.exit(1)

        self.logger.info("Sucessfully sections from pats server")
        return response.json()['sections']

    def download_spots(self, section_id: int, map_snapping: bool = True) -> dict:
        """Method used to download the spots from the Pats server.

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
            map_snapping(bool, optional): flag to turn on map snapping on the hand placed location of sensors. Defaults to True.

        Returns:
            dict: a dict containing the json response body.
        """
        self.logger.debug("Downloading spots from pats server")

        # Convert boolean to int.
        map_snapping_num: int = int(map_snapping == True)

        # Initialize header and request body.
        headers = {"Authorization": "Bearer " + self.token}
        params = {"section_id": str(section_id), "map_snapping": map_snapping_num}

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
        detection_class_ids: list[int],
        bin_mode: str = "D",
        average_24h_bin: bool = False,
    ):
        """Method used to download counts from the Pats server.
        The datetime format received from the pats server is: "%Y%m%d_%H%M%S"

        Note that the in the trapeye measurements, the first absolute count has NaN values in the diff rows.
        This is because the differnce is the differnce between the previous absolute count, and the new one. If there is not
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
            bin_mode (str, optional): EITHER 'D' OR 'H'!! corresponds to daily or hourly binning respectively . Defaults to "D".
            average_24h_bin (bool, optional): boolean flag, whether to include daily insect distribution within
                                              the selected date range or not. Defaults to False.

        Returns:
            dict: response body containing the counts in json format.
        """
        self.logger.debug("Retrieving counts from pats server")
        # Make sure all provided parameters are in the right format, and are the right type.
        section_id_str: str = str(section_id)
        start_date_formatted: str = start_date.strftime('%Y%m%d')
        end_date_formatted: str = end_date.strftime('%Y%m%d')
        detection_class_ids_str: str | None = ",".join(map(str, detection_class_ids)) if detection_class_ids else None
        average_24h_bin_num: int = int(average_24h_bin == True)

        # Initialize the header and request body
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
