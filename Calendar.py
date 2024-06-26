import streamlit as st ##1.12.0 originally
import datetime
from datetime import date
import os

                                     
import pandas as pd

import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
##from pymongo_get_database import get_database

import s3fs
from st_files_connection import FilesConnection

import yaml
from yaml.loader import SafeLoader
from dontcommit import my_config

#import hydralit_components as hc
from time import sleep
from streamlit_calendar import calendar
#from navigation import make_sidebar
from datetime import datetime, timedelta



#st.set_page_config(page_title="Posture Priority", layout='wide',initial_sidebar_state='collapsed',)
#make_sidebar()

#creates the calendar and returns it
def makeCalendar(dateList):
    calendar_options = {
        "editable": False,
        "selectable": True,
        "headerToolbar": {
            "left": "today prev",
            "center": "title",
            "right": "next dayGridDay,dayGridWeek,dayGridMonth",
        },
        "initialView": "dayGridMonth",
    }
    calendar_events = createEvents(dateList)
    custom_css="""
        .fc {
            width: 40%; /* Change this value to adjust the width */
            height: 40%; /* Change this value to adjust the height */
            background: black;
            border: 1px white
            border radius: 20px
            padding: 10px 10px  
        }
        .fc-event-past {
            opacity: 0.8;
        }
        .fc-event-time {
            font-style: italic;
        }
        .fc-event-title {
            font-weight: 700;
        }
        .fc-toolbar-title {
            font-size: 1.5em;
        }
        .fc-h-event .fc-event-title-container {
            flex-grow: 1;
            flex-shrink: 1;
            min-width: 0px;
        }
    """
    cal = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css)
    return cal

#helper for create events
def streak(dateList, i):
    while i < len(dateList) - 1 and (dateList[i + 1] - dateList[i]).days == 1:
        i += 1
    return i

#creates list of events for calendar
#@dateList = a list of strings in the "%Y-%m-%d" format
def createEvents(dateList):
    eventsList = []
    dateTimes = [datetime.strptime(date_str, "%Y-%m-%d") for date_str in dateList]
    i = 0
    while i < len(dateList):
        end = streak(dateTimes, i)
        if i == end:
            newEvent = {
                "title": "🖼️", #display
                "color": "#FF6C6C", 
                "start": dateTimes[i].strftime("%Y-%m-%d"),
                "end":  dateTimes[i].strftime("%Y-%m-%d"),
                "resourceId": "pic"
            }
        else:
            newEvent = {
                "title": "STREAK",  #display
                "color": "#FF6C6C", 
                "start": dateTimes[i].strftime("%Y-%m-%d"), 
                "end": (dateTimes[end] + timedelta(days=1)).strftime("%Y-%m-%d"), 
                "resourceId": "streak"
            }
        eventsList.append(newEvent)
        i = end + 1
    return eventsList

#placeholder for actual request
def photoRequest(date, photoTaken):
    if photoTaken:
        st.write("There is a photo on, " + date)
    else: 
        st.write("There is no photo on, " + date)


if __name__ == "__main__":
    dateList= ['2024-04-24', '2024-04-25', '2024-04-26', '2024-04-27', '2024-04-28', '2024-05-05', '2024-05-06', '2024-05-07', '2024-05-08', '2024-05-09', '2024-05-16', '2024-05-17', '2024-05-18', '2024-05-19', '2024-05-20', '2024-05-22']
    calendar = makeCalendar(dateList)
    st.write(calendar)
    #click event, should bring up photo
    if calendar.get("callback") == "eventClick":
        date = calendar["eventClick"]["event"]["start"]
        photoRequest(date=date, photoTaken= date in dateList)
    elif calendar.get("callback") == "dateClick":
        date = calendar["dateClick"]["date"].split('T')[0]
        photoRequest(date=date, photoTaken= date in dateList)
    

    