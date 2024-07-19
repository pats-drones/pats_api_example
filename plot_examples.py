import matplotlib.pyplot as plt
import pandas as pd

class ExamplePlots():
    def __generate_label(self, section: dict) -> str:
        """Private helper method, generates the label used in naming a plot.

        Args:
            section (dict): dict containing information about a section.

        Returns:
            str: the label used in titeling plots.
        """
        label: str = section['customer_name'] + ' '
        if section['greenhouse_name'] is not None:
            label += section['greenhouse_name'] + ' '
        if section['name'] is not None:
            label += section['name']
        return label.strip()

    def example_c_binned_per_day_plot(self, counts: dict, section: dict, insect_table: dict) -> None:
        """Plot an example plot with counts binned per day.

        Args:
            counts (dict): the response body out of the counts endpoint.
            section (dict): the section from where these counts originate.
            insect_table (dict): dictionary containing the detection classes.
        """
        # Loop over all pats c sensors.
        for patsc in counts['c']:
            # Retrieve information from this sensor.
            # Read in a pandas dataframe with all counts from this sensor.
            df = pd.DataFrame.from_records(patsc['counts'])
            post_id = patsc["post_id"]
            row_id = patsc["row_id"]

            # In case of bin_mode "D" we have a 'date', in case of bin_mode H we have 'datetime' instead.
            # Here we uniformize to column name with "date".
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            else:
                df['date'] = pd.to_datetime(df['datetime'], format='%Y%m%d_%H%M%S')
                df = df.drop(columns=['datetime'])

            # Set the date column as index.
            df = df.set_index('date')

            # Start the figure, and generate the label to be used in the title.
            plt.figure()
            label = self.__generate_label(section=section)

            # Since we set the date to be the index, all columns left are insect ids.
            for insect_id in df.columns:
                insect = insect_table[insect_id]
                df[insect_id].plot(label=insect['label'])

            # Add the title to the plot, and give names to the axes. Also add a legend to the plot.
            plt.title(f"PATS-C @ {label} row {row_id} post {post_id}")
            plt.xlabel('Date')
            plt.ylabel('Insect flights')
            plt.legend()

   
