from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    return 'Index Page, i.e this is the <h2>index page </h2>'

@app.route('/hello')
def hello():
    return "<h1> Testing this Hello World biz</H1>"

if __name__ == "__main__":
    app.run()