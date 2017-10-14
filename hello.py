SERVER_URL = "http://8ecdd1ab.ngrok.io"

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import requests
from flask import Flask, request, send_from_directory
import requests
import configparser
import boto3

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

except KeyError:
    print("Missing keys in the config.ini file")

# to upload files for serving images to fb
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    )

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

# send image file
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
    msg = data['entry'][0]['messaging'][0]

    sender_id = msg['sender']['id']         # person sending msg
    recipient_id = msg["recipient"]["id"]   # our page id
    message_text = msg['message']['text']   # txt of msg
    nlp_json = msg["message"]["nlp"]['entities'] # nlp parsed dict

    # send is_typing msg
    is_typing(sender_id)

    print("---printing the data we get from facebook---")
    print(data)
    print("---------------------------------")


    # put code here to make sense of the nlp dict
    # extract datetime, intent and so on from the nlp

    nlp = {}
    for key in nlp_json.keys():
        nlp[key] = nlp_json[key][0]["value"]
        nlp[key+"_confidence"] = nlp_json[key][0]["confidence"]
        if key == "datetime":
            nlp["date_grain"] = nlp_json[key][0]["grain"]
    
    # then use the intent to call the relevant function
    # have a dict which maps intent to function

    # dummy messages to check i send a message through
    reply(sender_id, "your msg was: " + message_text)
    reply(sender_id, "parsing your msg:")
    reply(sender_id, str(nlp))

    if nlp["intent"] == "spend":
        print("spending loop entered")
        cost_of(sender_id, nlp["search_query"])
    
    return "ok", 200

def reply(user_id, msg=None, image_url=None):
    """takes in user_id and a msg and sends it"""
    if image_url:
        image_url_test = 'https://i.imgur.com/g99oNUh.png'
        print(image_url)

        # FB only displays images from sites with SSL certificates
        data = {'recipient': {'id': '1718968874810833'}, 
                'message': {'attachment': 
                {'type': 'image', 
                'payload': {'url': image_url_test }}}}
    else:
        data = {"recipient": {"id": user_id}, 
                "message": {"text": msg}}

    print("---reply data dict----")
    print(data)
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
    
# to ab able to eyeball if the server is up and running on the interwebs
@app.route('/hello')
def hello():
    print("the hello function ran")
    return "<h1> Testing this Hello World biz</H1>"


# raw csv file from pocketbook for testing
data = pd.read_csv("data/pocketbook-export.csv")

def cost_of(user_id, what, when=None):
    # ignoring the date for now
    if what in data.category.values:
        total_spend = -data[data.category.values == what]["amount"].sum()
        
        # lets tell the user how much was spent on this category
        msg = f"you spent {total_spend} at {what}"
        reply(user_id, msg)

        # lets plot something
        plt.plot(data[data.category.values == what]["amount"])
        plt.title("Spending on" + what)
        plt.xlabel("Dates"), plt.ylabel("Dollars")
        image_name = "test.png"
        plt.savefig("static/" + image_name)

        s3.upload_file("static/test.png", "paisabot", aws_access_key_id)
        
        # Generate the URL to get 'key-name' from 'bucket-name'
        url = s3.generate_presigned_url(ClientMethod='get_object', 
                    Params={'Bucket': 'paisabot', 
                    'Key': image_name})

        reply(user_id, image_url=url)

    else: # dealing for when the users category isn't found
        msg = f"Can't find {when} in your transactions, pls try something else"
        reply(user_id, msg)
        
    
if __name__ == "__main__":
    app.run()