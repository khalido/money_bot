
import configparser

from rasa_core.channels import HttpInputChannel
from rasa_core.channels.facebook import FacebookInput
from rasa_core.agent import Agent
from rasa_core.interpreter import RegexInterpreter

# api keys are in config.ini to keep them out of github
config = configparser.ConfigParser()
config.read('config.ini')
try:
    APP_ID = config['facebook']["APP_ID"]
    PAGE_ACCESS_TOKEN = config['facebook']["PAGE_ACCESS_TOKEN"]
    VERIFY_TOKEN = config['facebook']["VERIFY_TOKEN"]
    APP_SECRET = config['facebook']["APP_SECRET"]
    PAGE_ID = config['facebook']["PAGE_ID"]
except KeyError:
    print("Missing keys in the config.ini file")

print("----checking tokens loaded from config----")
print(APP_ID, VERIFY_TOKEN, PAGE_ACCESS_TOKEN, APP_SECRET, PAGE_ID)
print("----end of tokens")

# load your trained agent
agent = Agent.load("models/policy/init", interpreter=RegexInterpreter())
print("---Agent Loaded---")

input_channel = FacebookInput(
   fb_verify=VERIFY_TOKEN,
   fb_secret=APP_SECRET,
   fb_tokens=[{PAGE_ID:PAGE_ACCESS_TOKEN}],
   debug_mode=True
)

# or `agent.handle_channel(...)` for synchronous handling
agent.handle_channel(HttpInputChannel(5000, "/", input_channel))