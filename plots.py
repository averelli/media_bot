import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.colors import rgb2hex
from connect_db import send_query
import pandas as pd
import numpy as np

def plot_report(type, date_start):
    # get data for the plot based on the type param
    if type == "reading":
        df = pd.DataFrame(send_query("""
                                        SELECT l.date,
                                            b.title,
                                            round(l.percentage::numeric / 100::numeric * b.word_count::numeric) AS words
                                        FROM reading.books_log l JOIN reading.book b on b.book_id = l.book_id
                                        WHERE date >= %s
                                        ORDER BY DATE;
                                    """, 
                                    (date_start,)))
    df.columns = ["date", "title", "words"]
    
    # get unique titles
    unique_labels = df["title"].unique()

    # set up the figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot the data
    # if there are a lot of titles, there will be no legend and no colors for the bars
    print('len is ', len(unique_labels))
    if len(unique_labels) > 20:
        ax.bar(df["date"], df["words"],  zorder=2)
    else:
        # create a dict of colors for each label
        colors = [rgb2hex(color) for color in plt.cm.tab20.colors]
        label_colors = dict(zip(unique_labels, colors))

        # add a color column to the df
        df["color"] = df["title"].map(label_colors)
        print(len(colors))

        ax.bar(df["date"], df["words"], color=df["color"],  zorder=2)

        # create a legend
        # map labels to colors
        legend_labels = {label: mpatches.Patch(color=color) for label, color in label_colors.items()}

        plt.legend(handles = legend_labels.values(), labels = legend_labels.keys(), loc='best')

    # Format x-axis as dates
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    

    # plot all the dates in the interval, so will not skip empty days
    all_dates = pd.date_range(start=df["date"].min(), end=df["date"].max(), freq='D')
    ax.set_xticks(all_dates)    

    # rotate x-axis labels for better visibility
    plt.xticks(rotation=45)

    # add y-ticks 
    y_max = int(df["words"].max())
    y_ticks = np.arange(0, y_max + 1, y_max / 4)
    plt.yticks(y_ticks)


    # add a grid 
    ax.grid(axis='x', linestyle='--', alpha=0)
    ax.grid(axis='y', linestyle='--', alpha=0.7, zorder=1)

    # set a background color
    fig.patch.set_facecolor('#262735')
    ax.set_facecolor("#323447")

    ax.spines['bottom'].set_color("#f8faf7")
    ax.spines['top'].set_color("#f8faf7") 
    ax.spines['right'].set_color("#f8faf7")
    ax.spines['left'].set_color("#f8faf7")
    ax.tick_params(which="both", colors="#f8faf7")

    # Set labels and title
    plt.xlabel("Date", color="#f8faf7")
    plt.ylabel("Words", color="#f8faf7")
    plt.title("Words read over time", color="#f8faf7")

    

    # Show the plot
    plt.show()

plot_report('reading', '2023-10-01')