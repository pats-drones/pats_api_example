# file: plot_examples.py
from typing import cast

import matplotlib.pyplot as plt
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D


class ExamplePlots():
    def __generate_label(self, section: dict) -> str:
        """Private helper method, generates the label used in naming a plot.

        Args:
            section (dict): dict containing information about a section.

        Returns:
            str: the label used in titeling plots.
        """
        label: str = section["customer_name"] + " "
        if section["greenhouse_name"] is not None:
            label += section["greenhouse_name"] + " "
        if section["name"] is not None:
            label += section["name"]
        return label.strip()

    def c_binned_per_day_plot(self, counts: dict, section: dict, insect_table: dict) -> None:
        """Plot an example plot with counts binned per day.

        Args:
            counts (dict): the response body out of the counts endpoint.
            section (dict): the section from where these counts originate.
            insect_table (dict): dictionary containing the detection classes.
        """
        # Loop over all pats c sensors.
        for patsc in counts["c"]:
            # Retrieve information from this sensor.
            # Read in a pandas dataframe with all counts from this sensor.
            df = pd.DataFrame.from_records(patsc["counts"])
            post_id = patsc["post_id"]
            row_id = patsc["row_id"]

            # In case of bin_mode "D" we have a 'date', in case of bin_mode H we have 'datetime' instead.
            # Here we uniformize to column name with "date".
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
            else:
                df["date"] = pd.to_datetime(df["datetime"], format="%Y%m%d_%H%M%S")
                df = df.drop(columns=["datetime"])

            # Set the date column as index.
            df = df.set_index("date")

            # Start the figure, and generate the label to be used in the title.
            plt.figure()
            label = self.__generate_label(section=section)

            # Since we set the date to be the index, all columns left are insect ids.
            for insect_id in df.columns:
                insect = insect_table[insect_id]
                df[insect_id].plot(label=insect["label"])

            # Add the title to the plot, and give names to the axes. Also add a legend to the plot.
            plt.title(f"PATS-C @ {label} row {row_id} post {post_id}")
            plt.xlabel("Date")
            plt.ylabel("Insect flights")
            plt.legend()

    def c_24h_distribution_plot(self, counts: dict, section: dict, insect_table: dict) -> None:
        """Plot an example plot of the 24h distribution of counts.

        Args:
            counts (dict): the response body out of the counts endpoint.
            section (dict): the section from where these counts originate.
            insect_table (dict): dictionary containing the detection classes.
        """
        # Loop over all pats c sensors.
        for patsc in counts["c"]:
            # Validate the "average_24h_bin" flag was turned on in the /api/count call.
            if "avg_counts_24h" not in patsc:
                return

            # Retrieve information from this sensor.
            # Read in a pandas dataframe with all counts from this sensor.
            df = pd.DataFrame.from_records(patsc["avg_counts_24h"])
            post_id = patsc["post_id"]
            row_id = patsc["row_id"]

            # Start the figure, and generate the label to be used in the title.
            plt.figure()
            label = self.__generate_label(section=section)

            # Loop over all insects, and plot them in the figure.
            for insect_id in df.columns:
                insect = insect_table[insect_id]
                df[insect_id].plot(label=insect["label"])

            # Add the title to the plot, and give names to the axes. Also add a legend to the plot.
            plt.title(f"PATS-C 24h distribution @ {label} row {row_id} post {post_id}")
            plt.xlabel("Hour")
            plt.ylabel("Insect flights")
            plt.legend()

    def trapeye_plot(self, counts: dict, section: dict, insect_table: dict) -> None:
        """Plot and example figure from a trapeye.
        In contrast to the example plots from the c sensors, here we will only show one example plot.
        The plot corresponds to the 0th trap eye sensor.

        Args:
            counts (dict): the response body out of the counts endpoint.
            section (dict): the section from where these counts originate.
            insect_table (dict): dictionary containing the detection classes.
        """
        # Retrieve informatino about the trapeye.
        trapeye = counts["trapeye"][0]
        row_id = trapeye["row_id"]
        post_id = trapeye["post_id"]

        # Read the new counts into a dataframe, drop NaN rows and make the date the index.
        df = pd.DataFrame.from_records(trapeye["new_counts"])
        df.dropna(axis=0, how="any", inplace=True)
        df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
        df = df.set_index("date")

        # Start the figure, and generate the label to be used in the title.
        plt.figure()
        label = self.__generate_label(section=section)

        # Loop over the insects, and add them to the plot.
        for insect_id in df.columns:
            insect = insect_table[insect_id]
            df[insect_id].plot(label=f"""{insect['label']} ({insect['bb_label']})""")

        # Add the title to the plot, and give names to the axes. Also add a legend to the plot.
        plt.title(f"Trap-Eye @ {label} row {row_id} post {post_id}")
        plt.xlabel("Date")
        plt.ylabel("Insects fresh on the card")
        plt.legend()

    def trapeye_counts_to_excel(self, counts: dict, insect_table: dict, file_path: str,) -> None:
        """Save Trap-Eye counts to an Excel workbook grouped by insect class.

        The resulting workbook contains one worksheet per insect. Each worksheet
        has a row for every date and a column for each Trap-Eye sensor,
        mirroring the data that is visualised in :meth:`trapeye_plot`.

        Args:
            counts (dict): the response body out of the counts endpoint.
            insect_table (dict): dictionary containing the detection classes.
            file_path (str): path where the Excel workbook should be stored.
        """

        trapeyes = counts.get("trapeye", [])
        if not trapeyes:
            raise ValueError("No Trap-Eye counts available to export.")

        insect_data: dict[str, pd.DataFrame] = {}
        used_trapeye_labels: set[str] = set()

        for index, trapeye in enumerate(trapeyes):
            trapeye_counts = trapeye.get("new_counts", [])
            if not trapeye_counts:
                continue

            df = pd.DataFrame.from_records(trapeye_counts)
            if df.empty or "date" not in df.columns:
                continue

            df.dropna(axis=0, how="any", inplace=True)
            if df.empty:
                continue

            df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
            df = df.set_index("date")

            label_parts: list[str] = []
            if trapeye.get("row_id") is not None:
                label_parts.append(f"row {trapeye['row_id']}")
            if trapeye.get("post_id") is not None:
                label_parts.append(f"post {trapeye['post_id']}")
            base_label = " ".join(label_parts).strip() or f"trapeye_{index}"

            trapeye_label = base_label
            suffix = 1
            while trapeye_label in used_trapeye_labels:
                suffix += 1
                trapeye_label = f"{base_label}_{suffix}"
            used_trapeye_labels.add(trapeye_label)

            for insect_id in df.columns:
                insect_series = df[insect_id].rename(trapeye_label)
                insect_series = pd.to_numeric(insect_series, errors="coerce")

                if insect_id not in insect_data:
                    insect_data[insect_id] = insect_series.to_frame()
                else:
                    insect_data[insect_id] = insect_data[insect_id].join(
                        insect_series, how="outer"
                    )

        if not insect_data:
            raise ValueError("No Trap-Eye data found to export.")

        sheet_names: set[str] = set()
        with pd.ExcelWriter(file_path) as writer:
            for insect_id, insect_df in insect_data.items():
                insect_df_sorted = insect_df.sort_index()
                insect_df_sorted = insect_df_sorted.sort_index(axis=1)

                insect_info = insect_table.get(insect_id, {})
                sheet_name = (insect_info.get("label") or "").strip()
                if not sheet_name:
                    sheet_name = str(insect_id)

                sheet_name = sheet_name[:31] or str(insect_id)
                base_sheet_name = sheet_name
                counter = 1
                while sheet_name in sheet_names:
                    counter += 1
                    suffix = f"_{counter}"
                    sheet_name = f"{base_sheet_name[:31 - len(suffix)]}{suffix}"
                sheet_names.add(sheet_name)

                insect_df_sorted.to_excel(writer, sheet_name=sheet_name)

    def c_scatter_plot(self, detections_df: pd.DataFrame, insect_class: dict) -> None:
        """Plot an example figure of a scatter plot from detections.

        Args:
            detections_df (pd.DataFrame): dataframe containing detections.
            insect_table (dict): dictionary containing the detection classes.
        """
        # Initialize a 10 by 6 figure, and fill it with points.
        plt.figure(figsize=(10, 6))
        plt.scatter(detections_df["duration"], detections_df["size"])

        # Add labels to the axis, and a title and grid to the plot.
        plt.title(f'PATS-C {insect_class["label"]} detections')
        plt.xlabel("Duration [s]")
        plt.ylabel("Size [m]")
        plt.grid(True)

    def c_flight_3d_plot(self, flight_df: pd.DataFrame) -> None:
        """Plot an example 3d plot of a flight track.

        Args:
            flight_df (pd.DataFrame): dataframe containing the flight track data.
        """
        fig = plt.figure(figsize=(10, 8))
        ax = cast(Axes3D, fig.add_subplot(111, projection="3d"))
        ax.scatter(-flight_df["sposX_insect"], -flight_df["sposZ_insect"], flight_df["sposY_insect"])
        plt.title("Flight track of an insect")
        ax.set_xlabel("X Position")
        ax.set_ylabel("Y Position")
        ax.set_zlabel("Z Position")
