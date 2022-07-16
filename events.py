from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import boto3
import json
import os
import urllib.parse

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
TICKETS = []


def stringify(date, event_location):

    event_date = datetime.fromisoformat(date.rstrip('Z'))
    short_month = event_date.strftime('%b')
    date_long = event_date.strftime('%A %d %b %Y')
    date_time = event_date.strftime('%I:%M%p')
    location_string = event_location.replace('\n', '<br>')
    location = "https://www.google.com/maps/dir/?api=1&destination=" + urllib.parse.quote(event_location)
    ticket = f"""<div class="row">
        <article class="card">
            <section class="date">
                <time datetime="{date}">
                    <span>{event_date.day}</span><span>{short_month}</span>
                </time>
            </section>
            <section class="card-cont">
                <h3>Jar of flies - An Alice in Chains Tribute</h3>
                <div class="even-date">
                    <i class="fa fa-calendar"></i>
                    <time>
                        <span>{date_long}</span>
                        <span>{date_time}</span>
                    </time>
                </div>
                <div class="even-info">
                    <i class="fa fa-map-marker"></i>
                    <p>
                        {location_string}
                    </p>
                </div>
                <a href="{location}" target="_blank">Directions</a>
            </section>
        </article>
    </div>
    <br>"""

    TICKETS.append(str(ticket))


def get_events():

    KEY = os.getenv('DEVELOPER_KEY')
    CALENDAR_ID = os.getenv('CALENDAR_ID')
    page_token = None

    try:
        now = datetime.now(timezone.utc).astimezone()
        service = build(
            'calendar',
            'v3',
            developerKey=KEY
            )

        while True:
            events = service.events().list(
                calendarId=CALENDAR_ID,
                pageToken=page_token,
                orderBy="startTime",
                singleEvents=True,
                timeMin=now.isoformat()
                ).execute()

            for event in events['items']:
                if 'description' in event.keys():
                    event_description = event['description']
                if 'start' in event.keys():
                    if 'dateTime' in event['start'].keys():
                        event_time = event['start']['dateTime']
                    elif 'date' in event['start'].keys():
                        event_time = event['start']['date']
                if 'location' in event.keys():
                    event_location = event['location']
                stringify(event_time, event_location)
                page_token = events.get('nextPageToken')
            if not page_token:
                break

        service.close()
    except Exception as e:
        print(e)


def lambda_handler(event, context):

    BUCKET = os.getenv('BUCKET_NAME')
    S3_PATH = os.getenv('S3_PATH')

    get_events()

    ticket_list = ''.join(TICKETS)
    encoded_string = ticket_list.encode("utf-8")
    bucket_name = BUCKET
    file_name = "b.html"
    s3_path = S3_PATH + file_name
    s3 = boto3.resource("s3")
    s3.Bucket(bucket_name).put_object(Key=s3_path, Body=encoded_string)
