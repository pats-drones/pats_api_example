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
`python -m pip install PyQt5`.

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
| `/api/v2/detection_classes` | Detection-class metadata keyed by string class IDs, including `available_in_vertel`. |
| `/api/v2/sections` | Active sections visible to your account; its class list currently omits Vertel-only classes. |
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
start = end - timedelta(days=30)  # 31 inclusive calendar days
counts_model = "vertel"  # or "beedrill"
counts = client.download_counts(
    start, end, section_id, detection_class_ids=[], bin_mode="D",
    average_24h_bin=True, model=counts_model,
)
print(counts["trapeye"])
print(counts["c"])
```

Counts are returned unchanged as a dictionary containing `trapeye` and `c` lists.

`average_24h_bin=True` adds `avg_counts_24h`: hourly totals across the range,
ordered from noon through the following morning. Despite the parameter name,
these values are sums, not arithmetic averages.

`download_spots()` retains its existing `snapping_mode` argument for Python caller
compatibility, but the current API ignores it and returns stored locations.

### Choose a counting model

`model` is mandatory, keyword-only and has no default. The lowercase,
case-sensitive choices select the Trap-Eye counting model:

- `beedrill`: existing Epotentia/Beedrill counts and their existing response format.
- `vertel`: Vertel counts, with daily counts and quality information.

Choose one request for your example:

```python
# Existing Epotentia/Beedrill counts:
counts = client.download_counts(start, end, section_id, [], model="beedrill")
```

```python
# Vertel counts instead:
counts = client.download_counts(start, end, section_id, [], model="vertel")
```

PATS-C counts, binning and the 24-hour distribution are unaffected by `model`.
The Beedrill path currently includes existing Epotentia history without filtering
historical model configurations; the name does not guarantee that all historical
measurements were produced by Beedrill.

### Detection classes

An empty `detection_class_ids=[]` selects all classes configured for the section
and supported by the chosen counting model. PATS-C uses its configured PATS-C
classes. To select particular insects, pass IDs such as
`detection_class_ids=[3, 24]`; unsupported or unconfigured IDs add no series.

Use `client.download_detection_classes()` (`GET /api/v2/detection_classes`)
for class names and `available_in_vertel`. This boolean indicates that a class
supports Vertel monitoring; it does not mean the class is configured for your
section. The catalogue includes Vertel-only classes. `/api/v2/sections` currently
omits those classes and does not include `available_in_vertel` in its class
objects, so do not build the default counts filter from that list.

```python
insect_table = client.download_detection_classes()
for class_id, metadata in insect_table.items():
    if metadata["available_in_vertel"]:
        print(class_id, metadata["label"])
```

### Interpret Trap-Eye results

Each Trap-Eye item contains `row_id`, `post_id` and daily series. Numeric records
have a `date` in `YYYYMMDD` format and string detection-class IDs as keys.
Series are grouped by **historical row/post position**, not hardware serial
number. Replacing hardware at the same position shares its series; moving it to
another position creates a separate series.

| Series | Meaning |
| --- | --- |
| `absolute_count` | Daily absolute insect counts on the card. |
| `new_counts` | New insect counts returned by the API. |
| `weekly_counts` | Vertel only: stored weekly insect counts. |
| `quality` | Vertel only: quality flags for each date, aligned with the numeric series. |

Beedrill retains its existing structure without `weekly_counts` or `quality`.
The API calculates the values; the client does not recalculate or interpolate.
For a Vertel response, read all series and their quality together:

```python
for position in counts["trapeye"]:  # An empty list is a normal result.
    print("Position:", position["row_id"], position["post_id"])
    print("Daily absolute counts:", position["absolute_count"])
    print("New counts:", position["new_counts"])
    quality_by_date = {entry["date"]: entry for entry in position["quality"]}
    for weekly in position["weekly_counts"]:
        quality = quality_by_date[weekly["date"]]
        print("Weekly counts:", weekly, "Quality:", quality)
        if quality["weekly_count_incomplete"]:
            print("Weekly value may be held; not a newly validated measurement.")
```

Every `quality` entry includes `date` and these booleans:

- `processed_photo_available`: a processed photo is available for this date.
- `weekly_count_incomplete`: the weekly observation is incomplete. A returned
  weekly value may be carried forward and **must not be interpreted as a newly
  validated measurement**.
- `card_replaced`: a card replacement was recorded.
- `lost_previous_boxes`: tracking of previous insect boxes was lost.

JSON `null` becomes Python `None`: the measurement is unavailable, **not zero**.
Zero is an actual stored zero. A first new count may be unavailable without a
previous measurement. Keep missing values and inspect quality flags rather than
filling gaps or treating held weekly values as fresh observations.

Vertel returns only positions with matching measurements in the requested range;
an included position can still have all-null values. No matching measurements or
unavailable Vertel storage can return `trapeye: []`; this alone does not establish
that no insects were present.

### Date ranges

Start and end dates must be valid calendar dates, with the end on or after the
start. The API counts both boundary dates when enforcing these limits:

| `bin_mode` | Maximum inclusive calendar days |
| --- | --- |
| `D` (daily) | 366 |
| `h` or `H` (hourly) | 31 |

For 31 inclusive dates use `end - timedelta(days=30)` as the start. Invalid,
reversed or excessive ranges are rejected, rather than truncated.

Dates are sent as `YYYYMMDD`. PATS-C bins span local noon on the start date up to,
excluding, local noon on the end date. Trap-Eye counts include both boundary dates
and **remain daily even when requesting hourly PATS-C counts**. Use dates in the
section's timezone; the client does not convert timezones.

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
24-hour distributions, Trap-Eye new and Vertel weekly counts, detection duration versus insect size,
and 3D flight trajectories. `main.py` demonstrates them when data is available.
The plotting code also includes `trapeye_counts_to_excel()` to export counts by
insect class; using it requires a pandas Excel writer backend such as `openpyxl`.
Install that optional backend with `python -m pip install openpyxl`.

```python
from plot_examples import ExamplePlots

plots = ExamplePlots()
plots.trapeye_plot(counts, section, insect_table)  # Both models: new counts
plots.trapeye_plot(counts, section, insect_table, weekly=True)  # Vertel, if available
plots.trapeye_counts_to_excel(counts, insect_table, "trapeye_counts.xlsx")
```

Trap-Eye plots show the first returned position. Missing values remain gaps
without dropping valid counts for other classes. Weekly plots show incomplete
values as separate crosses, labeled as not newly validated. The Excel export
keeps new counts by position and leaves unavailable measurements blank. Quality
flags remain in the API response and are not exported. It raises `ValueError` if there are no
Trap-Eye counts to export.

## API reference

For the complete parameter and response reference, use Swagger:

- [Production API reference](https://pats-c.com/api/v2/docs)
- [Beta API reference](https://beta.pats-c.com/api/v2/docs)
