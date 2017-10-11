import requests
from flask import Flask
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



# the webby stuff, powered by flask

app = Flask(__name__)

@app.route('/', methods=['GET'])
def handle_verification():
    return request.args['hub.challenge']

@app.route('/hello')
def hello():
    return "<h1> Testing this Hello World biz</H1>"

@app.route('/webhook', methods=['POST'])
def webhook():
    verify_token_from_fb = request.args.get('hub.verify_token')
    if VERIFY_TOKEN == verify_token_from_fb:
        return request.args.get('hub.challenge')
    
    return "test"

if __name__ == "__main__":
    app.run()
