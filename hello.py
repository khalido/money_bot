SERVER_URL = "http://8ecdd1ab.ngrok.io"
VERBOSE = True

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import requests
from flask import Flask, request, send_from_directory
import requests
import configparser
import boto3
import csv
import feedparser

import utils

# keep track of the last msg received to handle duplicate msgs from fB
last_msg_id = "None at the moment"
last_msg_intent = "None"

# dictionary to store place info
places_info = {}

# api keys are in config.ini to keep them out of github
config = configparser.ConfigParser()
config.read('config.ini')
try:
    APP_ID = config['facebook']["APP_ID"]
    PAGE_ACCESS_TOKEN = config['facebook']["PAGE_ACCESS_TOKEN"]
    VERIFY_TOKEN = config['facebook']["VERIFY_TOKEN"]
    APP_SECRET = config['facebook']["APP_SECRET"]
    PAGE_ID = config['facebook']["PAGE_ID"]
    aws_access_key_id = config['amazon']['aws_access_key_id']
    aws_secret_access_key = config['amazon']['aws_secret_access_key']
    PLACES_API = config['google']['PLACES_API']

except KeyError:
    print("Missing keys in the config.ini file")

# to upload files for serving images to fb
# boto3.resource is a high-level object-oriented API
s3 = boto3.resource('s3', 
                    aws_access_key_id=aws_access_key_id, 
                    aws_secret_access_key=aws_secret_access_key)

# the webby stuff, powered by flask
app = Flask(__name__)

# handle verification challange from fb to authenticate the app
@app.route('/webhook', methods=['GET'])
def handle_verification():
    if (request.args['hub.verify_token'] == VERIFY_TOKEN):
        print("Verified")
        return request.args['hub.challenge']
    else:
        print("Wrong token")
        return "Error, wrong validation token"

# send image file, not using at the moment
@app.route('/static/<path:filename>')
def download_file(filename):
    print("serving up a static file")
    return send_from_directory(app.config['static'],
                               filename, as_attachment=True)

# handle incoming messages and reply to them
@app.route('/webhook', methods=['POST'])
def handle_incoming_messages():
    print("incoming message handling started")
    data = request.json

    print("---printing the data we get from facebook---")
    print(data)
    print("---------------------------------")
    
    msg = data['entry'][0]['messaging'][0]
    
    # hacky way to handle getting repeated messages
    global last_msg_id
    if msg['message']['mid'] == last_msg_id:
        print("this is the same msg as the last one")
        return "ok", 200
    
    last_msg_id = msg['message']['mid']

    sender_id = msg['sender']['id']     
    recipient_id = msg["recipient"]["id"] 

    # send is_typing msg
    is_typing(sender_id)

    # check what kind of msg it is
    if 'attachments' in msg['message'].keys():
        if msg['message']['attachments'][0]['type'] == 'file':
            print("----file received----")
            reply(sender_id, "Attachment received, trying to parse it")
            file_url = msg['message']['attachments'][0]['payload']['url']
            file_name = utils.deal_with_file(sender_id, file_url)
            if file_name:
                msg = utils.new_csv(sender_id, file_name, file_url)
                reply(sender_id, msg)
            else:
                reply(sender_id, "couldn't download your file, try again")
        else:
            reply(sender_id, "Attachment received, can't deal with it, the bot can only deal with transactional data in .csv files for now")  
            reply(sender_id, "Try asking a question, like `how much did I spend on Groceries last month?`")
        # do nothing for now
        return "ok", 200
    else:
        message_text = msg['message']['text']   # txt of msg
        nlp_json = msg["message"]["nlp"]['entities'] # nlp parsed dict
        
        nlp = {} # simplified nlp dict
        for key in nlp_json.keys():
            nlp[key] = nlp_json[key][0]["value"]
            nlp[key+"_confidence"] = nlp_json[key][0]["confidence"]
            if key == "datetime":
                nlp["date_grain"] = nlp_json[key][0]["grain"]
    
    if VERBOSE:
        # echo msg back for debugging
        reply(sender_id, "your msg was: " + message_text)
        # send NLP dict for debugging
        reply(sender_id, str(nlp))

    # open users existing csv data into a dataframe
    print("trying to open the users csv file into a dataframe")
    data = utils.open_user_csv(sender_id)

    if data is None:
        reply(sender_id, "We don't have any data for you yet, pls upload a csv file of your transactions")
        return "ok", 200

    # main if/else loop to make sense of different kinds of intents
    if nlp["intent"] == "spend":
        print("entering spending function")
        cost_of(sender_id, nlp, data)
        print("and we are back from the spending loop")
    else:
        reply(sender_id, "Try asking a question, like `how much did I spend on Groceries last month?`")
    
    return "ok", 200

def reply(user_id, msg=None, image_url=None):
    """takes in user_id and a msg and sends it
    takes in either a msg or image_url, not both"""
    if image_url:
        data = {'recipient': {'id': '1718968874810833'}, 
                'message': {'attachment': 
                {'type': 'image', 
                'payload': {'url': image_url }}}}
    else:
        data = {"recipient": {"id": user_id}, 
                "message": {"text": msg}}

    post_url = "https://graph.facebook.com/v2.6/me/messages?access_token=" + PAGE_ACCESS_TOKEN
    resp = requests.post(post_url, json=data)
    
def is_typing(user_id):
    """sends a is typing msg to user_id"""
    data = {
        "recipient": {"id": user_id},
        "sender_action": "typing_on"
    }
    post_url = "https://graph.facebook.com/v2.6/me/messages?access_token=" + PAGE_ACCESS_TOKEN
    resp = requests.post(post_url, json=data)
    
# to be able to eyeball if the server is up and running on the interwebs
@app.route('/hello')
def hello():
    print("the hello function ran")
    return "<h1> Testing this Hello World biz</H1>. Yes indeed this server is up."


def cost_of(user_id, nlp, data, when=None, date_grain=None):
    """sends cost of category to the user in a msg"""
    print("spending loop actually entered")

    if "search_query" in nlp.keys():
        what = nlp['search_query'].lower()
    else:
        msg = f"NLP error, can't detect your search query, pls try something else"
        reply(user_id, msg)
        return
    
    # dealing with dates
    date_convert = {"day": "D", "week": "W", "month":"M", "year":"A"}
    
    if "datetime" and "date_grain" in nlp.keys():
        when = pd.to_datetime(nlp['datetime'])
        date_grain = date_convert[nlp["date_grain"]]
        date_period = when.to_period(date_grain)
    else:
        nlp['date_grain'] = "All"
        date_period = "All"
    
    # filtering by date
    if what in data.Category.str.lower().values:
        df = data[data.Category.values == what].copy()
        df.amount = df['amount'].apply(abs)
        
        # ideally filter by date here
        if when is not None and date_period is not "All":
            mask = (df.date >= date_period.start_time) & \
                    (df.date <= date_period.end_time)
            df2 = df[mask]
        else:
            df2 = df
            
        # now calculate total spend 
        total_spend = df2["amount"].sum()

        # lets tell the user how much was spent on this category
        msg = f"you spent {total_spend:.2f} on {what.capitalize()} during {date_period}"
        reply(user_id, msg)
        
        # lets plot something
        if total_spend != 0:
            df2.plot.bar(x="date", y="amount")
            #plt.plot(data[data.Category.values == what]["amount"])
            plt.title(f"Spending on {what.capitalize()} during {date_period}")
            plt.xlabel("Dates"), plt.ylabel("Dollars")

            image_name = user_id + "test.png"
            plt.savefig("static/" + image_name)

            # upload image to aws s3
            img_data = open("static/" + image_name, "rb")
            s3.Bucket("paisabot").put_object(Key=image_name, Body=img_data, 
                                    ContentType="image/png", ACL="public-read")

            # Generate the URL to send to facebook and send msg
            url = "http://paisabot.s3.amazonaws.com/" + image_name
            reply(user_id, image_url=url)

    else: # dealing for when the users category isn't found
        msg = f"Can't find {what} in your transactions, pls try something else"
        reply(user_id, msg)

def get_place_info(query="Aldi Broadway", country = "Australia"):
    """takes in a text and returns a google place lookup"""
    
    # return from dict if already looked this up
    if query.lower() in places_info:
        print("returning from dict")
        return places_info[query.lower()]
    
    info = {"address": 0, "location":0, "place_id":0, "types":0}
    
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    payload= {"query": query+" "+country, "key": PLACES_API}
    r = requests.get(url, params=payload)
    
    if r.json()["results"] != []:
        place = r.json()["results"][0]
    else:
        return info
    
    info["address"] = place['formatted_address']
    info["location"] = place['geometry']['location']
    info["place_id"] = place['place_id']
    info["types"] = place['types']
    return info 

queries = ["aldi broadway", "rebel sports", "chemist", "coles"]
places_info = {q.lower(): get_place_info(q) for q in queries}

# to make a nice dataframe of the places dict
#places_info_df = pd.DataFrame.from_dict(places_info, orient="index")
 
if __name__ == "__main__":
    app.run()