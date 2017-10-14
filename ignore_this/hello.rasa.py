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

# handle verification challange from fb to authenticate the app

# just bounce back verification token without checking
#@app.route('/', methods=['GET'])
#def handle_verification():
#    return request.args['hub.challenge']

# the better way to handle verification
@app.route('/webhook', methods=['GET'])
def handle_verification():
    if (request.args['hub.verify_token'] == VERIFY_TOKEN):
        print("Verified")
        return request.args['hub.challenge']
    else:
        print("Wrong token")
        return "Error, wrong validation token"

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

    # so we have called a function, now make a text string from it
    # or maybe to function itself returns a text string?
    # since each function will have a diff kind of string

    # so now we have have a text string to send to user,
    # so we can call the reply function which posts it 
    
    # dummy messages to check i send a message through
    reply(sender_id, "your msg was: " + message_text)
    reply(sender_id, "parsing your msg:")
    reply(sender_id, str(nlp))
    
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
    #print(resp.content)
    print(msg, "msg sent")

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
    return "<h1> Testing this Hello World biz</H1>"

    
if __name__ == "__main__":
    app.run()
