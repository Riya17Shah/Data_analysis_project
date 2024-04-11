
import pandas as pd
import numpy as np
import requests
from googleapiclient.discovery import build
import matplotlib.pyplot as plt
import seaborn as sns

api_key = '###'

channel_id = 'UCoOae5nYA7VqaXzerajD0lg'
api_key = '###'

youtube = build('youtube','v3',developerKey = api_key)

def get_channel(youtube,channel_id):


    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=channel_id)

    response = request.execute()

    data = {'channelName': response['items'][0]['snippet']['title'],
                'subscribers': response['items'][0]['statistics']['subscriberCount'],
                'views': response['items'][0]['statistics']['viewCount'],
                'totalVideos': response['items'][0]['statistics']['videoCount'],
                'playlistId': response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        }

    return data

channel_stats = get_channel(youtube,channel_id)

print(channel_stats)

channel_data = pd.DataFrame(channel_stats,index=[0])

print(channel_data)

playlist_id = 'UUoOae5nYA7VqaXzerajD0lg'

def get_video_ids(youtube, playlist_id):

    video_ids = []

    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=playlist_id,
        maxResults = 50
    )
    response = request.execute()

    for item in response['items']:
        video_ids.append(item['contentDetails']['videoId'])

    next_page_token = response.get('nextPageToken')
    while next_page_token is not None:
        request = youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId = playlist_id,
                    maxResults = 50,
                    pageToken = next_page_token)
        response = request.execute()

        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])

        next_page_token = response.get('nextPageToken')

    return video_ids


def get_video_details(youtube, video_ids):

   all_video_info = []

   for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(video_ids[i:i+50])
        )
        response = request.execute()

        for video in response['items']:
            stats_to_keep = {'snippet': ['channelTitle', 'title', 'description', 'tags', 'publishedAt'],
                             'statistics': ['viewCount', 'likeCount', 'favouriteCount', 'commentCount'],
                             'contentDetails': ['duration', 'definition', 'caption']
                            }
            video_info = {}
            video_info['video_id'] = video['id']

            for k in stats_to_keep.keys():
                for v in stats_to_keep[k]:
                    try:
                        video_info[v] = video[k][v]
                    except:
                        video_info[v] = None

            all_video_info.append(video_info)

   return pd.DataFrame(all_video_info)

video_ids = get_video_ids(youtube, playlist_id)

len(video_ids)

video_df = get_video_details(youtube, video_ids)
video_df.head()

"""# Data Pre-processing"""

video_df.info()

# converting columns to integer type
num_col = ['viewCount','likeCount','favouriteCount','commentCount']
video_df[num_col] = video_df[num_col].apply(pd.to_numeric,errors='coerce',axis = 1)

# parse the publishedAt column
from datetime import datetime

def parse_time(timestamp):
  dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
  return dt.day,dt.month,dt.year

video_df['Day'],video_df['Month'],video_df['Year'] = zip(*video_df['publishedAt'].apply(parse_time))

!pip install isodate

# convert duration to seconds
import isodate

def parse_duration(duration):
    dur = isodate.parse_duration(duration)
    return dur.total_seconds()

video_df['total_seconds'] = video_df['duration'].apply(lambda x: parse_duration(x))

# Add number of tags
video_df['tagsCount'] = video_df['tags'].apply(lambda x: 0 if x is None else len(x))

video_df.head(3)

"""# Data Analysis"""

# Which one is the most popular video ?

colors = sns.color_palette('Paired', n_colors=len(video_df))
ax = sns.barplot(x = 'title',y = 'viewCount',data = video_df.sort_values('viewCount',ascending=False)[0:19],palette=colors)
plt = ax.set_xticklabels(ax.get_xticklabels(),rotation = 90)

colors = sns.color_palette('Paired', n_colors=len(video_df))
ax = sns.barplot(x = 'title',y = 'likeCount',data = video_df.sort_values('likeCount',ascending=False)[0:19],palette=colors)
plt = ax.set_xticklabels(ax.get_xticklabels(),rotation = 90)

"""# From above two analysis we can say that in most videos which are getting higher viewcount are also getting higher number of like count."""



sns.set(style='whitegrid')
ax = sns.scatterplot(x = 'likeCount',y = 'total_seconds',data =video_df)
ax.set_xticklabels(ax.get_xticks(), rotation=90)

"""# From the above observation we can say that as the duration of video is increasing the like counts are not.

# This shows that people like to watch and like those videos which are less than 2000 seconds.
"""

video_per_month = video_df.groupby('Month',as_index=False).size()
video_per_year = video_df.groupby('Year',as_index=False).size()

"""# In year 2023 , highest amount of videos are uploaded."""

sns.barplot(x='Year',y = 'size',data=video_per_year)

"""#In both the months March and December highest number of videos are uploaded."""

sns.barplot(x='Month',y = 'size',data=video_per_month)

sns.barplot(x='Year',y = video_df['viewCount'],data=video_per_year)

"""# From the above graph we can see that year 2020 has highest number of viewcount. So, we can easily say that during covid pandamic people tend to watch more youtube videos."""

sns.barplot(x='Month',y = video_df['viewCount'],data=video_per_month)

"""# From above graph we can say that in month of October and May the viewcount has spiked up."""

