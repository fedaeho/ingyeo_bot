import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as pltdt
import seaborn as sns

plt.rcParams['font.family'] = 'NanumSquareOTF'

def sleep_parser():
    df = pd.read_csv('sleep_message.csv')
    data = list()
    for author, content in zip(df.author, df.content):
        for con in content.split("\n"):
            month_day, hour_min, sleepwake = con.split()
            month, day = month_day.split("/")
            hour, min = hour_min.split(":")
            if min=="??":
                min = 30 
            dt = datetime.datetime(year=2020+1*(month!="12"),month=int(month), day=int(day), hour=int(hour), minute=int(min))
            if sleepwake == "취침":
                sleep_dt = dt
            else:
                data.append({"author":author, "sleep_dt":sleep_dt, "wake_dt":dt})
                # data.append({"author":author, "Datetime":dt, "Sleep":sleepwake[0]=="취", "Wake":sleepwake[0]=="기"})

    df_log = pd.DataFrame(columns=["author", "sleep_dt", "wake_dt"])
    df_log = df_log.append(data)
    df_log.sleep_dt = pd.to_datetime(df_log.sleep_dt)
    df_log.wake_dt = pd.to_datetime(df_log.wake_dt)

    df_log.to_csv('sleep_log.csv', index=False)


def draw_sleep(author):
    df_log = pd.read_csv('sleep_log.csv')
    data_sleep=df_log[df_log.author==author]
    data_sleep.sleep_dt = pd.to_datetime(data_sleep.sleep_dt)
    data_sleep.wake_dt = pd.to_datetime(data_sleep.wake_dt)

    # Make a new column with date component only
    data_sleep['Date'] = data_sleep['sleep_dt'].dt.normalize()
    start_date = data_sleep['Date'].iloc[0]
    end_date = data_sleep['Date'].iloc[-1]

    data_sleep['day_number'] = (data_sleep['Date'] - start_date).dt.days + 1

    # Convert timestamp to decimal hours
    data_sleep['sleep_timestamp_hour'] = data_sleep['sleep_dt'].dt.hour + \
            data_sleep['sleep_dt'].dt.minute / 60
    data_sleep['wake_timestamp_hour'] = data_sleep['wake_dt'].dt.hour + \
            data_sleep['wake_dt'].dt.minute / 60

    # Compute duration in decimal hours
    data_sleep['duration'] = data_sleep['wake_timestamp_hour'] - data_sleep['sleep_timestamp_hour']

    # Find the index of session that extend into the next day
    index = data_sleep['wake_dt'].dt.normalize() > data_sleep['Date']

    # Compute the offset duration to be plotted the next day
    data_sleep.loc[index, 'offset'] = data_sleep['wake_timestamp_hour']

    # Compute the current day duration, cut off to midnight
    data_sleep.loc[index, 'duration'] = 24 - data_sleep['sleep_timestamp_hour']

    data_sleep.to_csv(f'{author}.csv', index=False)
    # Plot setup
    sns.set(font="NanumSquareOTF",style="darkgrid")

    figure, ax = plt.subplots()
    BAR_SIZE = 1

    # Find sessions with offsets and plot the offset with day_number+1
    data_sleep.loc[index].apply(lambda row: ax.broken_barh(
        [(row['day_number'] + 1, BAR_SIZE)], [0, row['offset']]), axis=1)

    # Loop through each row and plot the duration
    data_sleep.apply(lambda row: ax.broken_barh(
        [(row['day_number'] , BAR_SIZE)],
        [row['sleep_timestamp_hour'], row['duration']]), axis=1)

    date_num = data_sleep['day_number'].max()
    if data_sleep['offset'].iloc[-1]:
        date_num+=1

    title=f"{author}-Sleep"

    # Figure settings
    TITLE_FONT_SIZE = 25
    AXIS_FONT_SIZE = 15
    TITLE_HEIGHT_ADJUST = 1.02

    # Create the tick labels
    hour_labels = ["{}:00".format(h) for h in range(0,24)]
    day_labels = [(start_date + datetime.timedelta(days=j)).strftime("%m/%d") for j in range(date_num)]

    # Set title and axis labels
    ax.set_title(title, fontsize=TITLE_FONT_SIZE, y=TITLE_HEIGHT_ADJUST)
    ax.set_xlabel('Day', fontsize=AXIS_FONT_SIZE)
    ax.set_ylabel('Time', fontsize=AXIS_FONT_SIZE)

    # Format y axis - clock time
    ax.set_yticks(range(24))
    ax.set_ylim(0, 24)
    ax.set_yticklabels(hour_labels)
    # ax.invert_yaxis()

    # Format x axis - bottom, week number
    ax.set_xlim(1, date_num+1)
    ax.set_xticks(range(1,date_num+1))
    # ax.xaxis.set_ticks(date_num)
    ax.set_xticklabels(day_labels, rotation="vertical")

    # plt.grid()
    plt.tight_layout()
    plt.savefig(f"{author}.png")


    return f"{author}.png"


if __name__=="__main__":
    # from matplotlib import font_manager
    # for font in font_manager.fontManager.ttflist:
    #     if 'Nanum' in font.name:
    #         print(font.name, font.fname)
            
    # font_manager._rebuild()

    sleep_parser()