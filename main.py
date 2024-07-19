from plot_examples import ExamplePlots
from pats_service import PatsService
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import logger
import os

logger.init_logger(logger=logger.logger)


def read_credentials() -> tuple[str, str]:
    cred_file = './.auth'
    if os.path.exists(cred_file):
        with open(cred_file, 'r', encoding='utf-8') as creds_file:
            user = creds_file.readline().strip()
            passw = creds_file.readline().strip()
            return user, passw
    else:
        raise FileNotFoundError('Error: Super secret .auth authorization not found')


if __name__ == "__main__":
    # Read the login credentials from the ".auth" file.
    user, passw = read_credentials()

    # Initialize "patsService" and "examplePlots" classes.
    pats_service = PatsService(user=user, passw=passw)
    example_plots = ExamplePlots()

    # Retrieve the detection classes and sections from Pats servers.
    insect_table = pats_service.download_detection_classes()
    sections = pats_service.download_sections()

    # Pick an section to be used in the example.
    # Then we get the insect ids that are available for the choses section.
    example_section = sections[0]  # A random section for the example.
    available_insect_ids = [insect["id"] for insect in example_section["detection_classes"]]

    # Download the spots of all sensors in the example section,
    # here you can find information about individual sensors, like the location.
    spots = pats_service.download_spots(section_id=example_section["id"])

    # Download the counts from all sensors in the example section,
    # for the selected insect(s), for the selected date range.
    today = datetime.today()
    past_date = datetime.today() - timedelta(days=31)
    counts = pats_service.download_counts(start_date=today, end_date=past_date, section_id=example_section, detection_class_ids=available_insect_ids)

    # If there are "c" counts in the received counts. Then show some example plots from them.
    if len(counts['c']):
        example_plots.c_binned_per_day_plot(counts, example_section, insect_table)
        example_plots.c_24h_distribution_plot(counts, example_section, insect_table)

    # If we received trapeye counts, show a example plot from it.
    if len(counts['trapeye']):
        example_plots.trapeye_plot(counts, example_section, insect_table)

    # up to this point Trap-Eye and PATS-C data is virtually the same.
    # However when we go lower TrapEye periodically photographes a bulk and PATS-C stereo-video records individuals.
    # Thus we will split them up, lets start with an image from a Trap-Eye!
    some_row_id = None
    some_post_id = None
    some_system_id = None

    if len(spots['trapeye']):
        # For the example select a random row and post id.
        some_row_id = spots['trapeye'][0]['row_id']
        some_post_id = spots['trapeye'][0]['post_id']

        # Get the list with available photos from the pats server.
        # Then download the first photo from that list and show it.
        photo_list = pats_service.download_trapeye_photo_list(example_section['id'], some_row_id, some_post_id, past_date, today)
        image = pats_service.download_trapeye_photo(example_section['id'], some_row_id, some_post_id, photo_list[0])
        image.show()

    # Now, let's go get a flight track and a video from PATS-C!
    if len(spots['c']):
        # Lets again select a random row and post for the example.
        if spots['c'][0]['row_id'] is None or spots['c'][0]['post_id'] is None:
            some_system_id = spots['c'][0]['system_id']  # legacy for not all systems have a row/post location.
        else:
            some_row_id = spots['c'][0]['row_id']
            some_post_id = spots['c'][0]['post_id']

        # Select the first insect that is available for pats-c
        some_insect_class: dict = next((item for item in example_section['detection_classes'] if item['available_in_c']), {})

        # Initialize a start and end date, and set the time to 12:00:00:00 precisely.
        start_datetime = (datetime.today() - timedelta(days=31)).replace(hour=12, minute=0, second=0, microsecond=0)
        end_datetime = (datetime.today() - timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)

        # Download the detections in the example section, from the specified sensor, from the specified insect class, in the specified time frame.
        # And make an scatter plot from it.
        df_detections = pats_service.download_c_detection_features(example_section['id'], some_row_id, some_post_id, some_system_id, some_insect_class['id'], start_datetime, end_datetime)
        example_plots.c_scatter_plot(df_detections, some_insect_class)

        # From the first detection we downloaded, get the unique id.
        # We will download the flight track of the insect in this detection, and show a plot of it.
        some_insect = df_detections['uid'].iloc[0]
        df_flight = pats_service.download_c_flight_track(example_section['id'], some_insect)
        example_plots.c_flight_3d_plot(df_flight)

        # We can also download the video of the insect.
        # Word of warning: this download can easily take over a minute, as the render is being done on demand on the edge.
        mkv_data = pats_service.download_c_video(example_section['id'], some_insect)
        with open("temp_video.mkv", "wb") as file:
            file.write(mkv_data)  # open with any normal video player, e.g. vlc

    # Show the plots, the program will not terminate while the plots are open.
    plt.show(block=True)
