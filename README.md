# PATS Dashboard API examples

Use Python to retrieve and analyze your PATS insect monitoring data through the
Dashboard API v2. This repository includes examples for:

- **Trap-Eye:** insect counts and sticky-card images.
- **PATS-C:** insect counts, individual detection features, flight trajectories and video.
- **Metadata:** available insect classes, sections and device locations.

The examples retrieve data accessible to your account. They do not change your
sections or devices.

## Getting started

Use Python 3.10 or newer. Create a virtual environment and install the dependencies:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Interactive plot windows need a [Matplotlib GUI backend](https://matplotlib.org/stable/users/explain/figure/backends.html).
If your desktop Python environment has none, install one with
`python -m pip install PyQt5`. Qt is optional and is not needed to run the tests.

You need a PATS account with access to the relevant sections. An API-only account
can also be used; it needs the same section permissions as other accounts.

Create a `.env` file in the repository root:

```dotenv
pats_user="your_username"
pats_passw="your_password"
```

These are the existing environment-variable names. You can also set them directly
in your environment. `.env` is ignored by Git; keep credentials and tokens private.

`main.py` uses production (`https://pats-c.com`) by default. To use beta, change
its `PatsService` constructor to:

```python
pats_service = PatsService(
    user=user, passw=passw, server="https://beta.pats-c.com", timeout=180
)
```

Use the base URL without `/api/v2`. Beta is used for testing and may differ from
production. All data methods use v2 in either environment.

Run the examples:

```sh
python main.py
```

The script selects the first available section and the last 31 days of data.
Edit the section selection and date range in `main.py` as needed. It displays
plots and a Trap-Eye image when available, and downloads one PATS-C example video
to `temp_video.mkv` (overwriting that file). Run it on a desktop to view the plots
and images. Close the plot windows to finish.

Devices without integer `row_id` and `post_id` coordinates are skipped for the
PATS-C detection-features example with an informational message. The script tries
other PATS-C devices, while counts remain available independently. Flight-track
and video downloads use the `uid` of a retrieved detection.

## Authentication

Authentication uses **`POST /token`** with form-encoded credentials, not JSON:

```python
import requests

response = requests.post(
    "https://pats-c.com/token",
    data={"username": "your_username", "password": "your_password"},
    timeout=45,
    allow_redirects=False,
)
response.raise_for_status()
access_token = response.json()["access_token"]
```

Subsequent requests include this header:

```text
Authorization: Bearer <access_token>
```

`PatsService` handles this automatically using a `requests.Session`. It raises
`PatsServiceError` for HTTP failures, redirects and connection/time-out errors,
without logging passwords, tokens or response bodies. An expired token requires
a new `PatsService` instance; this example does not refresh tokens automatically.
A 401 or 403 can indicate invalid credentials, an expired token or insufficient
access to a section.

## Available read-only endpoints

All endpoints below use `GET` and Bearer authentication.

| Endpoint | Returned data |
| --- | --- |
| `/api/v2/detection_classes` | Detection-class metadata keyed by string class IDs. |
| `/api/v2/sections` | Active sections visible to your account, including their configured detection classes. |
| `/api/v2/spots` | Device locations grouped into `trapeye`, `c`, `marker` and `gateway` lists. |
| `/api/v2/counts` | JSON containing Trap-Eye daily counts and PATS-C daily or hourly counts. |
| `/api/v2/trapeye_photo_list` | Available processed photo timestamps for a row/post location, newest first. |
| `/api/v2/download_trapeye_photo` | JPEG image bytes for a listed timestamp. |
| `/api/v2/download_detection_features` | Individual PATS-C detections for a row/post location and detection class. |
| `/api/v2/download_c_flight_track` | Flight-track records for a detection UID. |
| `/api/v2/download_c_video` | Binary video for a detection UID; the Python example downloads Matroska. |

Section metadata keeps two separate photo-frequency fields:
`n_weekly_trapeye_photos` is the configured number of photos to process per week;
`n_weekly_trapeye_photos_contract` is the contracted number (zero means no
Trap-Eye contract is configured).

## Python usage examples

The snippets below continue from the same client and section. Choose dates in the
section's timezone; the client formats them without converting timezones.

### Retrieve sections and insect counts

```python
from datetime import datetime, timedelta

from main import read_credentials
from pats_service import PatsService

user, passw = read_credentials()
client = PatsService(user, passw, timeout=180)
sections = client.download_sections()  # list of section dictionaries
if not sections:
    raise SystemExit("No sections available for this account.")
section = sections[0]
section_id = section["id"]
spots = client.download_spots(section_id)

end = datetime.now()
start = end - timedelta(days=31)
class_ids = [item["id"] for item in section["detection_classes"]]
counts = client.download_counts(
    start, end, section_id, class_ids, bin_mode="D", average_24h_bin=True
)
print(counts["trapeye"])
print(counts["c"])
```

Counts are returned unchanged as a dictionary containing `trapeye` and `c` lists.
Pass an empty class-ID list to use the section's configured classes. `bin_mode="h"`
selects hourly PATS-C counts; Trap-Eye counts remain daily. Dates are sent as
`YYYYMMDD`. PATS-C bins span local noon on the start date up to, excluding, local
noon on the end date; Trap-Eye counts include both boundary dates. Missing values
may be `None`, and the first Trap-Eye new count may be unavailable because it has
no previous measurement.

`average_24h_bin=True` adds `avg_counts_24h`: hourly totals across the range,
ordered from noon through the following morning. Despite the parameter name,
these values are sums, not arithmetic averages.

`download_spots()` retains its existing `snapping_mode` argument for Python caller
compatibility, but the current API ignores it and returns stored locations.

### Download a Trap-Eye image

```python
if spots["trapeye"]:
    spot = spots["trapeye"][0]
    photos = client.download_trapeye_photo_list(
        section_id, spot["row_id"], spot["post_id"], start, end
    )
    if photos:
        image = client.download_trapeye_photo(
            section_id, spot["row_id"], spot["post_id"], photos[0]
        )
        image.save("trapeye.jpg")
```

The photo list contains `YYYYMMDD_HHMMSS` strings. Pass a timestamp unchanged as
`photo_id`. The service opens the JPEG bytes and returns a Pillow `Image.Image`.
An empty photo list is normal when no processed images match the range.

### Retrieve PATS-C detections and download media

```python
c_spot = next(
    (spot for spot in spots["c"]
     if all(type(spot.get(key)) is int for key in ("row_id", "post_id"))),
    None,
)
c_class = next(
    (item for item in section["detection_classes"] if item["available_in_c"]),
    None,
)
if c_spot is not None and c_class is not None:
    detections = client.download_c_detection_features(
        section_id, c_spot["row_id"], c_spot["post_id"], c_class["id"], start, end
    )
    if not detections.empty:
        uid = detections["uid"].iloc[0]
        track = client.download_c_flight_track(section_id, uid)
        video = client.download_c_video(section_id, uid)
        with open("detection.mkv", "wb") as output:
            output.write(video)
```

Detection features require both location coordinates and a detection class enabled
for PATS-C in that section. Times are sent as `YYYYMMDD_HHMMSS` in the section's
timezone, with both boundaries included. Features and tracks return pandas
DataFrames, including empty DataFrames when the API returns no records.

Use `raw_stereo=True` with `download_c_video()` for raw stereo video. Media may be
unavailable even when a detection exists; catch `PatsServiceError` as shown in
`main.py`. Rendering can take more than a minute, so the examples use a 180-second
request timeout; the service default remains 45 seconds.

## Visualization examples

`plot_examples.py` contains `ExamplePlots` methods for PATS-C counts over time,
24-hour distributions, Trap-Eye new counts, detection duration versus insect size,
and 3D flight trajectories. `main.py` demonstrates them when data is available.
The plotting code also includes `trapeye_counts_to_excel()` to export counts by
insect class; using it requires a pandas Excel writer backend such as `openpyxl`.

## API reference

For the complete parameter and response reference, use Swagger:

- [Production API reference](https://pats-c.com/api/v2/docs)
- [Beta API reference](https://beta.pats-c.com/api/v2/docs)

## Tests

Run the lightweight mocked HTTP tests without credentials or network access:

```sh
python -m unittest discover -s tests -v
```

Compatibility: the public service methods and return types are preserved, except
that `download_c_detection_features()` no longer accepts `system_id`. Call it with
`section_id`, `row_id`, `post_id`, `detection_class_id`, `start_date` and `end_date`.
HTTP failures now raise `PatsServiceError` instead of exiting the Python process.
