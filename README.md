# API Documentation
This document describes the various endpoints available in the pats RESTfullAPI, their purposes, request parameters, and expected responses.

## POST

### 1. ${server}/token

#### Request body token

The request body for the token endpoint can be found below. Here the username, and the password are the login credentials for your pats account. They are the same credentials to log into the [pats website]("https://pats-c.com/login").

```JSON
{
    "username": "str",
    "password": "str"
}
```

#### Description token

Retrieves the API token corresponding to the provided pats account. This token will be used for authentication in all other endpoints.

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

- `bb_label`: **considered legacy**, it stands for "Biobest label", and is internally used by a partner corporation.
- `id`: this is the same id as the insect id.
- `label`: latin name of the detection class.
- `short_name`: english name of the detection class.

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
- 'detection_classes`:
    - `available_in_c`: flag whether this detection class is available for pats-c.
    - `available_in_trapeye`: flag whether this detection class is available for trapeye's.
    - `benificial`: flag whether this detection class (insect) is good or bad.
    - `c_level_x`: a threshold set on the [website]("https://pats-c.com/login").
    - `id`: insect id.
    - `trapeye_level`: a threshold set on the [website]("https://pats-c.com/login").

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

#### Request body spots

The request body can be found below. Here the `section_id` is the id of the section from which the spots will be retrieved. `map_snapping` is a flag that either snaps the sensor locations to the map or not, with `map_snapping` turned on lines of sensors will be straighter.

```JSON
{
    "section_id": "str",
    "map_snapping": 1
}
```

#### Description spots

The spots endpoint will return information of all the individual "c" , and "trapeye" sensors.

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

#### Request body counts

The request body can be found below. Some notes:

- `average_24h_bin` is a boolean flag represented as an int. When `average_24h_bin` is set to 1, you will also retrieve information about the number of detections on different hours of the day.
- `start_date` and `end_date` are string representing dates. The format should be: "%Y%m%d".
- `detection_class_ids` is a list of insect ids in the form of a string. The format should be _"insectId1,insectId2,insectId3..."_.
- `bin_mode` is a string and should either be `D` or `H`. Which stand for daily or hourly binning respectively.

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

#### Description counts

The counts endpoint is used to download counts from the pats servers. Counts are the number of detections of a certain detection class.

#### Response body counts

This endpoint also returns 2 elements: `c` and `trapeye`.

In `c` the counts of all pats-c sensors in the provided section in between the provided time span will be returned. Every sensor has three elements:

- `counts`: the counts on different timestamps (`datetime` in format "%Y%m%d_%H%M%S"). Each count contains all the insect ids that the pats-c counts in this section.
- `post_id` and `row_id` form together the location of the sensor.

in `trapeye` you get a little more information. You get the `absolute_count`, which contains, not at all surprisingly, the absolute count of a insect, but also the difference with the previous absolute count. There is also the `new_count`, which is the new count since the last count.

For the sharp reader, the `new_count` are indeed the same as the "diff" fields in the `absolute_count` element.

There are some NaN values in the response body. Both the `new_count` as the "diff" elements get calculated by taking the difference with the `previous_absolute` count and the new `absolute_count`.
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
