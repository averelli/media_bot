import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.colors import rgb2hex
from connect_db import send_query
import pandas as pd
import numpy as np
import io

# define figure and buffer so they can be closed from another function
image_buffer = None
fig = None

def plot_report(type: str, date_start):
    """
    Returns a plot of data for the specific date range given the start date

    Args:
        type (str): takes either reading or shows
        date_start (datetime): takes a datetime object to specify the start of the range

    Returns:
        (None): Creates a plot
    """

    # get global vars
    global image_buffer, fig
    
    # get data for the plot based on the type param
    if type == "reading":
        df = pd.DataFrame(send_query("""
                                        SELECT 
                                            l.date,
                                            b.title,
                                            round(l.percentage::numeric / 100::numeric * b.word_count::numeric) AS words
                                        FROM reading.books_log l JOIN reading.book b on b.book_id = l.book_id
                                        WHERE date >= %s
                                        ORDER BY DATE;
                                    """, 
                                    (date_start,)))
    elif type == "shows":
        df = pd.DataFrame(send_query("""
                                        SELECT 
                                            l.date,
                                            s.title,
                                            sum(e.length)
                                        FROM shows.shows_log l join shows.episode e on e.episode_id = l.episode_id join shows.show s on e.show_id = s.show_id
                                        WHERE date >= %s
                                        GROUP BY l.date, s.title
                                        ORDER BY date;                                                                            
                                    """,
                                    (date_start,)))
        
    # set the columns
    df.columns = ["date", "title", "value"]
    
    # get unique titles
    unique_labels = df["title"].unique()

    # set up the figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot the data
    # if there are a lot of titles, there will be no legend and no colors for the bars
    if len(unique_labels) > 20:
        ax.bar(df["date"], df["value"],  zorder=2)
    else:
        # create a dict of colors for each label
        colors = [rgb2hex(color) for color in plt.cm.tab20.colors]
        label_colors = dict(zip(unique_labels, colors))

        # add a color column to the df
        df["color"] = df["title"].map(label_colors)

        ax.bar(df["date"], df["value"], color=df["color"],  zorder=2)

        # create a legend
        # map labels to colors
        legend_labels = {label: mpatches.Patch(color=color) for label, color in label_colors.items()}

        plt.legend(handles = legend_labels.values(), labels = legend_labels.keys(), loc='best')

    # Format x-axis as dates
    start_date = df["date"].min()
    end_date = df["date"].max()

    # ticks at the start of the range and each month
    # Get the start of the months
    monthly_ticks = pd.date_range(start=start_date, end=end_date, freq='MS')

    # Include the starting date explicitly
    all_ticks = [start_date] + list(monthly_ticks)
    ax.set_xticks(all_ticks)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))   

    # add y-ticks 
    y_max = int(df["value"].max())
    y_ticks = np.arange(0, y_max + 1, y_max / 4)
    plt.yticks(y_ticks)

    # add a grid 
    ax.grid(axis='x', linestyle='--', alpha=0)
    ax.grid(axis='y', linestyle='--', alpha=0.7, zorder=1)

    # set a background color
    fig.patch.set_facecolor('#262735')
    ax.set_facecolor("#323447")

    # set colors for the plot border and ticks
    ax.spines['bottom'].set_color("#f8faf7")
    ax.spines['top'].set_color("#f8faf7") 
    ax.spines['right'].set_color("#f8faf7")
    ax.spines['left'].set_color("#f8faf7")
    ax.tick_params(which="both", colors="#f8faf7")

    # Set labels and title
    plt.xlabel("Date", color="#f8faf7")

    label_param = "Words" if type == "reading" else "Minutes watched"
    plt.ylabel(label_param, color="#f8faf7")
    plt.title(f"{label_param} read over time", color="#f8faf7")

    # create a buffer to store the plot as an image
    image_buffer = io.BytesIO()
    plt.savefig(image_buffer, format="png")
    image_buffer.seek(0)

    return image_buffer


def close_plots():
    """Close the fig and buffer used for the plots"""

    global image_buffer, fig

    if image_buffer and not image_buffer.closed:
        image_buffer.close()
        buffer = None
    
    if fig:
        plt.close(fig)
        fig = None
