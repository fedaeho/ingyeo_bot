#%%
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as pltdt
import seaborn as sns
import holidays

kr_holidays = holidays.KR()

plt.rcParams["font.family"] = "NanumSquareOTF"

#%%
def sleep_parser():
    df = pd.read_csv("sleep_message.csv")
    data = list()
    for author, content in zip(df.author, df.content):
        for con in content.split("\n"):
            month_day, hour_min, sleepwake = con.split()
            month, day = month_day.split("/")
            hour, min = hour_min.split(":")
            if min == "??":
                min = 30
            dt = datetime.datetime(
                year=2020 + 1 * (month != "12"),
                month=int(month),
                day=int(day),
                hour=int(hour),
                minute=int(min),
            )
            if sleepwake == "취침":
                sleep_dt = dt
            else:
                data.append({"author": author, "sleep_dt": sleep_dt, "wake_dt": dt})
                # data.append({"author":author, "Datetime":dt, "Sleep":sleepwake[0]=="취", "Wake":sleepwake[0]=="기"})

    df_log = pd.DataFrame(columns=["author", "sleep_dt", "wake_dt"])
    df_log = df_log.append(data)
    df_log.sleep_dt = pd.to_datetime(df_log.sleep_dt)
    df_log.wake_dt = pd.to_datetime(df_log.wake_dt)

    df_log.to_csv("sleep_log.csv", index=False)


def log_preprocess(author):
    df_log = pd.read_csv("sleep_log.csv")
    data_sleep = df_log[df_log.author == author].copy()
    data_sleep.sleep_dt = pd.to_datetime(data_sleep.sleep_dt)
    data_sleep.wake_dt = pd.to_datetime(data_sleep.wake_dt)

    # Make a new column with date component only
    data_sleep["Date"] = data_sleep["sleep_dt"].dt.normalize()
    start_date = data_sleep["Date"].iloc[0]

    data_sleep["day_number"] = (data_sleep["Date"] - start_date).dt.days + 1

    # Convert timestamp to decimal hours
    data_sleep["sleep_timestamp_hour"] = (
        data_sleep["sleep_dt"].dt.hour + data_sleep["sleep_dt"].dt.minute / 60
    )
    data_sleep["wake_timestamp_hour"] = (
        data_sleep["wake_dt"].dt.hour + data_sleep["wake_dt"].dt.minute / 60
    )

    # Compute duration in decimal hours
    data_sleep["duration"] = (
        data_sleep["wake_timestamp_hour"] - data_sleep["sleep_timestamp_hour"]
    )

    # Find the index of session that extend into the next day
    index = data_sleep["wake_dt"].dt.normalize() > data_sleep["Date"]

    # Holiday & Weekend Check
    data_sleep["holiday"] = data_sleep["wake_dt"].map(
        lambda x: (x in kr_holidays) or (x.weekday() >= 5)
    )

    # Compute the offset duration to be plotted the next day
    data_sleep.loc[index, "offset"] = data_sleep["wake_timestamp_hour"]

    # Compute the current day duration, cut off to midnight
    data_sleep.loc[index, "duration"] = 24 - data_sleep["sleep_timestamp_hour"]

    data_sleep.to_csv(f"{author}.csv", index=False)

    return index, data_sleep


def sleep_24h(author):
    index, data_sleep = log_preprocess(author)
    # Plot setup
    sns.set(font="NanumSquareOTF", style="darkgrid")

    figure, ax = plt.subplots()
    BAR_SIZE = 1

    # Find sessions with offsets and plot the offset with day_number+1
    data_sleep.loc[index].apply(
        lambda row: ax.broken_barh(
            [(row["day_number"] + 1, BAR_SIZE)],
            [0, row["offset"]],
            facecolor="C3" if row["holiday"] else "C0",
        ),
        axis=1,
    )

    # Loop through each row and plot the duration
    data_sleep.apply(
        lambda row: ax.broken_barh(
            [(row["day_number"], BAR_SIZE)],
            [row["sleep_timestamp_hour"], row["duration"]],
            facecolor="C3" if row["holiday"] else "C0",
        ),
        axis=1,
    )

    # date_num(xaxis size) revision
    date_num = data_sleep["day_number"].max()
    if data_sleep["offset"].iloc[-1] > 0:
        date_num += 1

    title = f"{author}-Sleep 24h"

    # Figure settings
    TITLE_FONT_SIZE = 25
    AXIS_FONT_SIZE = 15
    TITLE_HEIGHT_ADJUST = 1.02

    start_date = data_sleep["Date"].iloc[0]
    # Create the tick labels
    hour_labels = ["{}:00".format(h) for h in range(0, 24)]
    day_labels = [
        (start_date + datetime.timedelta(days=j)).strftime("%m/%d")
        for j in range(date_num)
    ]

    # Set title and axis labels
    ax.set_title(title, fontsize=TITLE_FONT_SIZE, y=TITLE_HEIGHT_ADJUST)
    ax.set_xlabel("Day", fontsize=AXIS_FONT_SIZE)
    ax.set_ylabel("Time", fontsize=AXIS_FONT_SIZE)

    # Format y axis - clock time
    ax.set_yticks(range(24))
    ax.set_ylim(0, 24)
    ax.set_yticklabels(hour_labels)
    # ax.invert_yaxis()

    # Format x axis - bottom, week number
    ax.set_xlim(1, date_num + 1)
    ax.set_xticks(range(1, date_num + 1))
    # ax.xaxis.set_ticks(date_num)
    ax.set_xticklabels(day_labels, rotation="vertical", ha="left")

    # plt.grid()
    plt.tight_layout()
    plt.savefig(f"{author}_24h.png")

    return f"{author}_24h.png"


#%%
def sleep_stat(author):
    index, data_sleep = log_preprocess(author)
    start_date = data_sleep["Date"].iloc[0]

    data_sleep["year_week"] = data_sleep["wake_dt"].map(lambda x: x.isocalendar()[:2])
    data_sleep["total_duration"] = data_sleep["duration"] + data_sleep["offset"].fillna(0)
    data_sleep["day_number"][index] += 1

    data_sleep = data_sleep.groupby(["day_number", "holiday", "year_week"], as_index=False)['total_duration'].sum()
    # print(data_sleep)

    data_sleep_week = data_sleep["total_duration"].groupby(data_sleep["year_week"])

    ds_week = data_sleep_week.aggregate("mean").reset_index()
    errors = data_sleep_week.aggregate("std").reset_index()

    # Plot setup
    sns.set(font="NanumSquareOTF", style="darkgrid")

    figure, axes = plt.subplots(1, 2, figsize=(20, 10))
    ax_day, ax_week = axes

    # date_num(xaxis size) revision
    date_num = data_sleep["day_number"].max()

    data_sleep.plot.bar(
        x="day_number",
        y="total_duration",
        ax=ax_day,
        color=data_sleep["holiday"].map(lambda x: "C3" if x else "C0"),
    )

    title = f"{author}-Sleep Stat"

    # Figure settings
    TITLE_FONT_SIZE = 25
    AXIS_FONT_SIZE = 15
    TITLE_HEIGHT_ADJUST = 1.02

    figure.suptitle(title, fontsize=TITLE_FONT_SIZE)
    # Create the tick labels
    # hour_labels = ["{}:00".format(h) for h in range(0,24)]
    day_labels = [
        (start_date + datetime.timedelta(days=j)).strftime("%m/%d")
        for j in range(date_num)
    ]

    # Set title and axis labels
    ax_day.set_title("Dayily chart", fontsize=TITLE_FONT_SIZE, y=TITLE_HEIGHT_ADJUST)
    ax_day.set_xlabel("Day", fontsize=AXIS_FONT_SIZE)
    ax_day.set_ylabel("Time", fontsize=AXIS_FONT_SIZE)

    # Format y axis - clock time
    # ax_day.set_yticks(range(24))
    # ax_day.set_ylim(0, 24)
    # ax_day.set_yticklabels(hour_labels)
    # ax_day.invert_yaxis()

    # Format x axis - bottom, week number
    ax_day.set_xlim(0, date_num + 1)
    ax_day.set_xticks(range(1, date_num + 1))
    # ax_day.xaxis.set_ticks(date_num)
    ax_day.set_xticklabels(day_labels, rotation="vertical")

    ds_week.plot.bar(yerr=errors, capsize=4, ax=ax_week)
    week_labels = ds_week.year_week.map(lambda x: f"{x[0]}/W{x[1]}")

    ax_week.set_title("Weekly chart", fontsize=TITLE_FONT_SIZE, y=TITLE_HEIGHT_ADJUST)
    ax_week.set_xlabel("Week", fontsize=AXIS_FONT_SIZE)
    ax_week.set_ylabel("Time", fontsize=AXIS_FONT_SIZE)

    # Format x axis - bottom, week number
    # ax_week.set_xlim(0, date_num+1)
    # ax_week.set_xticks(range(1,date_num+1))
    # ax_week.xaxis.set_ticks(date_num)
    ax_week.set_xticklabels(week_labels, rotation="vertical")

    # plt.grid()
    plt.tight_layout()
    plt.savefig(f"{author}_stat.png")
    
    return f"{author}_stat.png"


if __name__ == "__main__":
    # from matplotlib import font_manager
    # for font in font_manager.fontManager.ttflist:
    #     if 'Nanum' in font.name:
    #         print(font.name, font.fname)

    # font_manager._rebuild()

    sleep_parser()
    