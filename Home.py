##Some useful things for the future:
## st.write_stream for outputting text generated by OpenAI
##
##
import streamlit as st ##1.12.0 originally
import datetime
from datetime import date
import os

from streamlit_image_coordinates import streamlit_image_coordinates     ##manually select points for posture evaluation
#from streamlit_image_comparison import image_comparison                 ##compare two postures
#from streamlit_plotly_events import plotly_events                       ##interactively view data on graphs
import streamlit_authenticator as stauth                                ##user auth. in YAML

import numpy as np
import matplotlib.pyplot as plt           ##new
from openai import OpenAI

import plotly.express as px                                             
import pandas as pd
from PIL import Image
import mediapipe as mp
import math as m
import cv2

import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
##from pymongo_get_database import get_database

import s3fs
from st_files_connection import FilesConnection

import yaml
from yaml.loader import SafeLoader
from dontcommit import my_config

st.set_page_config(
    page_title="Posture Priority",
    page_icon="🚶",
    layout="centered",
    initial_sidebar_state='auto'
)

CURR_DATE = str(date.today())
st.title('Posture Priority')
st.subheader("Today is " + CURR_DATE[6:])
username, password, s3_key, s3_secret, GPT_key = my_config()

@st.cache_resource()
def init_connection():
    uri = "mongodb+srv://"+ username + ":" + password + "@capstonedbv1.wzzhaed.mongodb.net/?retryWrites=true&w=majority&appName=CapstoneDBv1"# Create a new client and connect to the server
    return uri

client = MongoClient(init_connection(), server_api=ServerApi('1')) 

# Send a ping to confirm a successful connection  
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
    st.write("Connection to database failed. Invalid credentials")

db = client.test_database
collection = db['test_PP']

fs = s3fs.S3FileSystem(anon=False, key=s3_key, secret=s3_secret)        ##init s3 filesystem
#openai.api_key = GPT_key                                                ##init openai
GPT_Client = OpenAI(api_key=GPT_key)


##################################################
#this is gonna be in cloud or db for end product v
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

##temp vars for class or similar
dailyPhotoUploadPrompt = True

if st.session_state["authentication_status"]:
    ##authenticator.logout()
    st.write(f'Welcome *{st.session_state["name"]}*')
    loggedIn = True
    currUser = st.session_state["username"]
    ##activeDates = fs.open("posturepriorityawsbucket/"+currUser, mode='rb').read()

    #Generate a response from ChatGPT using the question chat message
    #question = "What are some exercises or stretches to improve " + my_Posture + "?"
    #st.write(question)
    #response = GPT_Client.chat.completions.create(model = "gpt-3.5-turbo",
    #messages = [
    #    {"role": "user", "content": question}
    #],
    #max_tokens=100,
    #temperature=0.9,
    #frequency_penalty=0.5,
    #presence_penalty=0.5)

    #Extract the answer from the response
    #answer = response.choices[0].message.content

    # Print the returned output from the LLM model
    #st.write(str(answer))

    if dailyPhotoUploadPrompt:
        uploaded_file = st.file_uploader("Upload a photo for today")
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            st.image(bytes_data)

            s3 = s3fs.S3FileSystem(anon=False)                                              ##uses default credentials
            if st.button("Upload this photo?"):
                with fs.open('posturepriorityawsbucket/'+currUser+'_'+CURR_DATE, 'wb') as f: ##insert photo to s3 cloud
                    f.write(bytes_data)

                post = {
                    "username": currUser,
                    "photo": 'posturepriorityawsbucket/'+currUser+'_'+CURR_DATE,
                    "date": CURR_DATE
                }
                collection.insert_one(post) ##.inserted_id                                  ##insert post to db
                dailyPhotoUploadPrompt = False

    st.header("Or, view an existing photo")

    ## jank
    d = str(st.date_input("Select a date"))
    st.write(d)
    photo_posted = collection.find_one({"username": currUser, "date": d,})

    if photo_posted:
        st.write("A photo was uploaded on this day")
        #temp = str(currUser + '_'+d)
        view_photo = fs.open("posturepriorityawsbucket/" + currUser + '_' + d, mode='rb').read()
        #st.image(temp)
        st.image(view_photo)
        ##streamlit_image_coordinates(fs.open("posturepriorityawsbucket/"+currUser+'_'+d, mode='rb'))

    else:
        st.write("No photo was uploaded on this day")




else:
    st.subheader("Log in or sign up to get started")
    st.page_link("pages/Login.py", label="Log in here", icon="💾")

#st.image(fs.open("posturepriorityawsbucket/abc123.png", mode='rb').read())

#### MODEL I THINK ###
# Initialize MediaPipe modules
# Initialize MediaPipe modules
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Function to process uploaded image and detect landmarks
def process_image(image):
    with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:  # Adjust confidence thresholds as needed
        results = pose.process(image)
        return results.pose_landmarks

# Function to draw landmarks and connections on the image
def draw_landmarks(image, landmarks):
    annotated_img = image.copy()
    point_spec = mp_drawing.DrawingSpec(color=(220, 100, 0), thickness=-1, circle_radius=5)
    line_spec = mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
    mp_drawing.draw_landmarks(
        annotated_img,
        landmark_list=landmarks,
        connections=mp_pose.POSE_CONNECTIONS,
        landmark_drawing_spec=point_spec,
        connection_drawing_spec=line_spec
    )
    return annotated_img

# Function to extract landmark coordinates
def extract_landmark_coordinates(landmarks, img_width, img_height):
    l_knee_x = int(landmarks.landmark[mp_pose.PoseLandmark.LEFT_KNEE].x * img_width)
    l_knee_y = int(landmarks.landmark[mp_pose.PoseLandmark.LEFT_KNEE].y * img_height)
    # Extract other landmark coordinates similarly...
    return l_knee_x, l_knee_y  # Return coordinates of the left knee

# Function to visualize landmark coordinates
def visualize_landmark_coordinates(image, l_knee_x, l_knee_y):
    fig, ax = plt.subplots()
    ax.imshow(image[:, :, ::-1])
    ax.plot(l_knee_x, l_knee_y, 'ro')  # Plot left knee coordinates
    plt.show()
    
def findAngle(x1, y1, x2, y2):
    theta = m.acos( (y2 -y1)*(-y1) / (m.sqrt(
        (x2 - x1)**2 + (y2 - y1)**2 ) * y1) )
    degree = int(180/m.pi)*theta
    return degree



# Main Streamlit app logic
if __name__ == "__main__":
    # Page title and header
    curr_date = str(date.today())
    st.title('Posture Priority')
    st.subheader(curr_date)

    # File upload section
    uploaded_file = st.file_uploader("Upload a photo for ")
    if uploaded_file is not None:
        image = np.array(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        # Detect landmarks and draw on the image
        landmarks = process_image(image)
        annotated_image = draw_landmarks(image, landmarks)
        st.image(annotated_image, channels="BGR", caption="Landmarks and Connections Detected")

        # Extract and print landmark coordinates
        img_width, img_height = image.shape[1], image.shape[0]
        l_knee_x, l_knee_y = extract_landmark_coordinates(landmarks, img_width, img_height)
        ##st.write(f"Left knee coordinates: ({l_knee_x}, {l_knee_y})")
        
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        results = pose.process(image)

        
        h, w = image.shape[:2]

        # Use lm and lmPose as representative of the following methods.
        lm = results.pose_landmarks
        lmPose = mp_pose.PoseLandmark
        # Left shoulder.
        l_shldr_x = int(lm.landmark[lmPose.LEFT_SHOULDER].x * w)
        l_shldr_y = int(lm.landmark[lmPose.LEFT_SHOULDER].y * h)

        # Right shoulder.
        r_shldr_x = int(lm.landmark[lmPose.RIGHT_SHOULDER].x * w)
        r_shldr_y = int(lm.landmark[lmPose.RIGHT_SHOULDER].y * h)

        # Left ear.
        l_ear_x = int(lm.landmark[lmPose.LEFT_EAR].x * w)
        l_ear_y = int(lm.landmark[lmPose.LEFT_EAR].y * h)

        # Left hip.
        l_hip_x = int(lm.landmark[lmPose.LEFT_HIP].x * w)
        l_hip_y = int(lm.landmark[lmPose.LEFT_HIP].y * h)
        neck_inclination = findAngle(l_shldr_x, l_shldr_y, l_ear_x, l_ear_y)
        torso_inclination = findAngle(l_hip_x, l_hip_y, l_shldr_x, l_shldr_y)

        if neck_inclination > 40 or neck_inclination > 10:
            st.write("bad posture")
        else:
            st.write("good")

        # Visualize landmark coordinates on the image
        visualize_landmark_coordinates(image, l_knee_x, l_knee_y)