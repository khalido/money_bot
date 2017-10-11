import requests
from flask import Flask, request
import requests
import configparser

# api keys are in config.ini to keep them out of github
config = configparser.ConfigParser()
config.read('config.ini')
try:
    APP_ID = config['facebook']["APP_ID"]
    PAGE_ACCESS_TOKEN = config['facebook']["PAGE_ACCESS_TOKEN"]
    VERIFY_TOKEN = config['facebook']["VERIFY_TOKEN"]
except KeyError:
    print("Missing keys in the config.ini file")

print(VERIFY_TOKEN)

# the webby stuff, powered by flask

app = Flask(__name__)

# handle verification from fb to authenticate the app
@app.route('/', methods=['GET'])
def handle_verification():
    return request.args['hub.challenge']


# handle incoming messages and reply to them
@app.route('/', methods=['POST'])
def handle_incoming_messages():
    data = request.json
    msg = data['entry'][0]['messaging'][0]

    sender_id = msg['sender']['id']         # person sending msg
    recipient_id = msg["recipient"]["id"]   # our page id
    message_text = msg['message']['text']   # txt of msg

    print("---printing the data we get from facebook---")
    print(data)

    reply(sender_id, message_text[::-1])
    return "ok", 200

def reply(user_id, msg):
    """takes in user_id and a msg and sends it"""
    data = {
        "recipient": {"id": user_id},
        "message": {"text": msg}
    }

    post_url = "https://graph.facebook.com/v2.6/me/messages?access_token=" + PAGE_ACCESS_TOKEN
    resp = requests.post(post_url, json=data)
    
    print("---"*10)
    print(resp.content)
    print(msg, "msg sent")

# to ab able to eyeball if the server is up and running on the interwebs
@app.route('/hello')
def hello():
    return "<h1> Testing this Hello World biz</H1>"

    
if __name__ == "__main__":
    app.run()
