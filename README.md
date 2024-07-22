# API Documentation

This document describes the various endpoints available in the pats RESTfullAPI, their purposes, request parameters, and expected responses.

Word of warning: the code in this repository is meant to show how the endpoints can be used. There is no graceful handling of errors, when an error is raised the program will terminate with a non-zero exit code.

## Getting started guide

below is a short step-by-step plan to get started.

1. Choose the server you want to use, the server url is provided as an argument to the `PatsService` class, and can be one of three servers.
    - beta_server, "https://beta.pats-c.com/". This is the default and links to the development server from pats, this server is not always in sync with production.
    - main_server, "https://pats-c.com/". This is the link to the main server of pats, this is used in production. When you are ready to deploy this server is recommended.
    - local_testing, "http://127.0.0.1:5000/". This URL can be used for local testing, it links to localhost port 5000.
2. Make sure the login credentials are present as environment variables. The username should be named _"pats_user"_, and the pasword should be named _"pats\_passw"_. The easiest way to add them to the environment is by adding a _".env"_ file to the root directory of the project.
3. That is it, you are now ready to run the script!

## POST

### 1. ${server}/token

#### Description token

Retrieves the API token corresponding to the provided pats account. This token will be used for authentication in all other endpoints.

#### Request body token

The request body for the token endpoint can be found below. Here the username, and the password are the login credentials for your pats account. They are the same credentials to log into the [pats website]("https://pats-c.com/login").

```JSON
{
    "username": "str",
    "password": "str"
}
```

#### Response body token

The response body can be seen below.

```JSON
{
    "access_token": "str"
}
```

## GET

### Header

The header is for all GET endpoint the same, it contains the authentication in form of the API key received using the [token endpoint](#1-servertoken). An example header can be found below.

```JSON
{
    "Authorization": "str"
}
```

### 1. ${server}/api/download_detection_classes

_The detection classes endpoint does not have a request body._

#### Description detection classes

The detection classes endpoint retrieves, not surprisingly, all available detection classes. The detection classes are all the insects (and rats, birds, etc.) that pats knows. You can find out which are available to you via the [sections endpoint](#2-serverapisections)

### Response body detection classes

The detection classes response body contains just one element, `detection_classes`. In this element all detection classes can be found, detection classes are mapped to the `insect id` which is an int. Other attributes that can be found in the response body are:

- `bb_label` **considered legacy**, it stands for "Biobest label", and is internally used by a partner corporation.
- `id` this is the same id as the insect id.
- `label` latin name of the detection class.
- `short_name` english name of the detection class.

response body:

```JSON
{
    "detection_classes": {
        "1": {
            "bb_label": null,
            "id": 1,
            "label": "str",
            "short_name": "str"
        },
        ...
    }
}
```

### 2. ${server}/api/sections

_The sections endpoint does not have a request body._

#### Description sections

The sections endpoint retrieves information about the different sections. Sections contain a lot of meta data about a section.

#### Response Body

The response body for the sections endpoint contains an array of section objects. Each section object includes several attributes like:

- `crop`: the crop grown in this section.
- `n_weekly_trapeye_photos`: how often the trapeye's in this section make photos.
- `detection_classes`
    - `available_in_c` flag whether this detection class is available for pats-c.
    - `available_in_trapeye` flag whether this detection class is available for trapeye's.
    - `benificial` flag whether this detection class (insect) is good or bad.
    - `c_level_x` a threshold set on the [website]("https://pats-c.com/login").
    - `id` insect id.
    - `trapeye_level` a threshold set on the [website]("https://pats-c.com/login").

```JSON
{
    "sections": [
        {
            "crop": "str",
            "customer_name": "str",
            "detection_classes": [
                {
                    "available_in_c": 0,
                    "available_in_trapeye": 1,
                    "bb_label": "str",
                    "benificial": 0,
                    "c_level_1": 5,
                    "c_level_2": 15,
                    "c_level_3": 30,
                    "c_level_4": 50,
                    "id": 1,
                    "label": "str",
                    "short_name": "str",
                    "trapeye_level_1": 1,
                    "trapeye_level_2": 5,
                    "trapeye_level_3": 10,
                    "trapeye_level_4": 15
                },
            ],
            "greenhouse_name": "str",
            "hubspot_company_id": 0123456789,
            "id": 123,
            "label": "str",
            "n_weekly_trapeye_photos": 3,
            "name": "str",
            "timezone": "Europe/Amsterdam"
        }
    ]
}
```

### 3. ${server}/api/spots

#### Description spots

The spots endpoint will return information of all the individual "c" , and "trapeye" sensors.

#### Request body spots

The request body can be found below. Here the `section_id` is the id of the section from which the spots will be retrieved. `map_snapping` is a flag that either snaps the sensor locations to the map or not, with `map_snapping` turned on lines of sensors will be straighter.

```JSON
{
    "section_id": "str",
    "map_snapping": 1
}
```

#### Response body spots

In the response body there are two elements: `c` and `trapeye`.

In the `c` element all pats-c sensors in the provided section will be listed. Information about the pats-c sensors is the: `label`, `latitude`, `longitude`, `post_id`, `row_id` and `system_id`.
The post id and row id correspond to the post and row the sensor is placed on.

in the `trapeye` element all trapeye sensors can be found. These don't have a `label`, and instead of a `system_id` they have a `unit_id`.

the response body can be found below.

```JSON
{
    "c": [
        {
            "label": "str",
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
```

### 4. ${server}/api/counts

#### Description counts

The counts endpoint is used to download counts from the pats servers. Counts are the number of detections of a certain detection class.

#### Request body counts

The request body can be found below. Some notes:

- `average_24h_bin` (**OPTIONAL**, defaults to 0) is a boolean flag represented as an int. When `average_24h_bin` is set to 1, you will also retrieve information about the number of detections on different hours of the day.
- `start_date` and `end_date` are string representing dates. The format should be: _%Y%m%d"_.
- `detection_class_ids` (**OPTIONAL**, defaults to None)is a list of insect ids in the form of a string. The format should be _"insectId1,insectId2,insectId3..."_.
- `bin_mode`(**OPTIONAL**, defaults to "D") is a string and should either be `D` or `H`. Which stand for daily or hourly binning respectively.

```JSON
{
    "section_id": "str",
    "start_date": "date",
    "end_date": "date",
    "detection_class_ids": "str",
    "bin_mode": "str",
    "average_24h_bin": 0
}
```

#### Response body counts

This endpoint also returns 2 elements: `c` and `trapeye`.

In `c` the counts of all pats-c sensors in the provided section in between the provided time span will be returned. Every sensor has three elements:

- `counts` the counts on different timestamps (`datetime` in format _"%Y%m%d_%H%M%S"_). Each count contains all the insect ids that the pats-c counts in this section.
- `post_id` and `row_id` form together the location of the sensor.

in `trapeye` you get a little more information. You get the `absolute_count`, which contains, not at all surprisingly, the absolute count of a insect, but also the difference with the previous absolute count. There is also the `new_count`, which is the new count since the last count.

For the sharp reader, the `new_count` are indeed the same as the "diff" fields in the `absolute_count` element.

There are some NaN values in the response body. Both the `new_count` as the "diff" elements get calculated by taking the difference with the `previous_absolute` count and the new `absolute_count`.
The date format in both elements is in the format _"%Y%m%d"_.
Again the `post_id` and `row_id` make up the location of the sensor together.

The response body can be found below.

```JSON
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
                        "post_id": 12,
                        "row_id": 24
                    },
```

### 5. ${server}/api/trapeye_photo_list

#### Description trapeye photo list

Download the list of available photos from a certain trapeye in a certain time span. The id's returned can be used in the [download trapeye photo endpoint](#6-serverapidownload_trapeye_photo).

#### Request body trapeye photo list

The request body can be found below. It contains the following attributes:

- `section_id` the id of the section this sensor is placed in.
- `row_id` and `post_id` are the row and post respectively where this sensor is placed.
- `start_date` and `end_date` represent the start and the end of the time frame from which available photos will be shown. The format for these dates should be _"%Y%m%d"_.

```JSON
{
    "section_id": "str",
    "row_id": "str",
    "post_id": "str",
    "start_date": "str",
    "end_date": "str",
}
```

#### Response body trapeye photo list

The response body contains just one element, `photos`. This contains a list of id's, each id represents a photo. The id's are in the format _"%Y%m%d\_%H%M%S"_.

```JSON
{
    "photos": [
        "20240713_140300",
        "20240713_120300",
        "20240711_140300",
        "20240711_120500",
        "20240709_140200",
    ]
}
```

### 6. ${server}/api/download_trapeye_photo

#### Description download trapeye photo

This endpoint is used to download one of the available trapeye photo's returned by the [trapeye_photo_list](#5-serverapitrapeye_photo_list) endpoint.

#### Request body download trapeye photo

The Request body can be found below.
The first three element: `section_id`, `row_id` and `post_id` are used to identify the sensor that took the photo. The `datetime` element is used to identify the photo, this corresponds to one of the retrieved id's from the [trapeye_photo_list](#5-serverapitrapeye_photo_list) endpoint.

```JSON
{
    "section_id": "str",
    "row_id": "str",
    "post_id": "str",
    "datetime": "str",
}
```

#### Response body download trapeye photo

This endpoint does not have a JSON response body. Instead the response body contains the image in byte format.

### 7. ${server}/api/download_detection_features

#### Description download detection features

The download detection features endpoint is used to download information about a specific detection from a pats-c sensor.

#### Request body download detection features

To ensure backward compatibility this endpoint accepts two request bodies, both are shown below.
The `section_id`, `detection_class_id`, `start_datetime` and `end_datetime` are the same in both request bodies. The section_id represents the section the sensor that made the detections is in. The `detection_class_id` represents an insect id, this specifies from which insect the detections will be that are returned. The `start_datetime` and `end_datetime` represent the start and end of the time frame in which the returned detections were made.

`row_id` and `post_id` represent the position of the sensor that made the detections.

New request body:

```JSON
{
    "section_id": "str",
    "row_id": "str",
    "post_id": "str",
    "detection_class_id": "str",
    "start_datetime": "str",
    "end_datetime": "str",
}
```

`system_id` is a deprecated method to identify sensors.

Legacy request body:

```JSON
{
    "section_id": "str",
    "system_id": "str",
    "detection_class_id": "str",
    "start_datetime": "str",
    "end_datetime": "str",
}
```

#### Response body download detection features

The response body can be found below. It contains information about specific detections. All units are in [SI base units]("https://en.wikipedia.org/wiki/SI_base_unit").

- `datetime` the time on which the detection took place, the format is _"%Y%m%d\_%H%M%S"_.
- `dist_traject` distance as the crow flies between the start and end point of the detection.
- `dist_traveled` the distance flown by the insect during the detection.
- `duration` the duration of the detection.
- `light_level` the light level during the detection.
- `post_id` and `row_id` the post and row the sensor that did the detection is mounted on.
- `size` the estimated size of the insect.
- `start_datetime`the time on which the detection took place in human readable format, information is the same as in `datetime` field.
- `uid` the unique identifier for this detection
- `vel_max`, `vel_mean` and `vel_std` are the max, mean and standard deviation of the velocity of the insect.

```JSON
{
    "data": [
        {
            "datetime": "str",
            "dist_traject": 1.2345678901234567,
            "dist_traveled": 9.8765432109876543,
            "duration": 1.2345678901234567,
            "light_level": 9.8765432109876543,
            "post_id": 21,
            "row_id": 42,
            "size": 0.123456789012345678,
            "start_datetime": "Mon, 08 Jul 2024 20:25:45 GMT",
            "uid": 012345678,
            "vel_max": 9.8765432109876543,
            "vel_mean": 0.1234567890123456,
            "vel_std": 9.8765432109876543
        },
    ]
}
```

### 8. ${server}/api/download_c_flight_track

#### Description c flight track

Endpoint to download the flight track of an insect during a specific detection made by a pats-c sensor.

#### Request body c flight track

The request body can be found below. The `section_id` specifies in which section this detection took place, and the `detection_uid` is the unique identifier for the detection. The `detection_uid` of a measurement can be obtained using the [download_detection_features](#7-serverapidownload_detection_features) endpoint.

```JSON
{
    "section_id": "str",
    "detection_uid": "str",
}
```

#### Response body c flight track

The response body for the c flight track endpoint contains a list of measurement points, all measured in a single detection. The points can be used to reconstruct the flight track during the detection. All units are again in [SI base units]("https://en.wikipedia.org/wiki/SI_base_unit"), except `light_level`. This is a value between 0 and 1 where 1 is the maximum amount of light the camera can measure.

- `acc_valid_insect` ??
- `disparity_insect` ??
- `elapsed` time elapsed since ??
- `foundL_insect` ??
- `fp` ??
- `hunt_id` ??
- `imLx_insect` and `imLy_insect` ??
- `imLx_pred_insect` and `imLy_pred_insect` ??
- `light_level` the light level during this measurement, this is a value between 0 and 1 where 1 corresponds to the maximum light level the camera can measure.
- `motion_sum_insect` ??
- `n_frames_lost_insect` number of frames in a row the camera lost track of the insect. When this reaches 20 frames the detection ends.
- `n_frames_tracking_insect` number of frames in a row the camera is tracking the insect.
- `posX_insect`, `posY_insect` and `posZ_insect` the position of the insect in the viewport of the camera.
- `pos_valid_insect` ??
- `radius_insect` ??
- `rs_id` the id of the measurement.
- `saccX_insect`, `saccY_insect` and `saccZ_insect` ??
- `score_insect` ??
- `size_insect` the estimated size of the insect.
- `sposX_insect`, `sposY_insect` and `sposZ_insect` ??
- `svelX_insect`, `svelY_insect` and `svelZ_insect` ??
- `vel_valid_insect` ??

Response body:

```JSON
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
```

### 9. ${server}/api/download_c_video

#### Description c video

Endpoint used to download the video of a specific detection from a pats-c sensor.

#### Request body c video

The request body can be found below. The `section_id` and the `detection_uid` are used to uniquely identify the detection. The `section_id` represents the section where the pats-c sensor that made the detection is located, and the `detection_uid` is the unique id of the detection made. `raw_stereo` (**OPTIONAL**, defaults to "0"), is a boolean flag that can be used to request the raw stereo from the detection. Even though it is a boolean flag, it should be a string that is either "0", or "1". Here 1 is True, and 0 corresponds to False.

```JSON
{
    "section_id": "str",
    "detection_uid": "str",
    "raw_stereo": "str"
}
```

#### Response body c video

The response body does not contain JSON, as the response body only contains the requested video.
