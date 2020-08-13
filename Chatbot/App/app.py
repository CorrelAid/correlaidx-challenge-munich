#imports
from flask import Flask, render_template, request
import spacy
import numpy
nlp = spacy.load("de_core_news_sm") #German
from spacy.matcher import Matcher #for patterns
from spacy.tokens import Doc
matcher = Matcher(nlp.vocab)
import io
import random
from flask import Response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure


### Here comes the regionaldatenbank.de part
### These are the steps given by Correlaid:
#%load_ext autoreload
#%autoreload

import os
if not os.path.basename(os.getcwd()) == "datenguide-python":
    os.chdir("..")
    
    
from datenguidepy.query_helper import get_regions, get_statistics
from datenguidepy import Query
import pandas as pd
import matplotlib
#%matplotlib inline



import json
import six.moves.urllib.request as urlreq
from six import PY3

import dash
import dash_bio as dashbio
import dash_html_components as html
import dash_core_components as dcc

import plotly.graph_objs as go



app = Flask(__name__)
#define app routes
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/get")
#function for the bot response
def get_bot_response():
    userText = request.args.get('msg')
    pd.set_option('display.max_colwidth', 150)
    # get the ID of Berlin by querying all states by name
    get_regions().query("name == 'Bayern'") 
    city_one = nlp(userText) #nlp makes the text readable for spacy
    first = city_one.ents[0] #ents recognizes names of cities, important persons, countries,...
    global city
    city = first.text
    regions = get_regions().query("level == 'nuts2'") #this recognizes if the city is in Bavaria
    parents = regions.query('parent == "09"')
    ids = parents.index
    regions = get_regions().query("level == 'nuts3'")
    cities = regions.query('(parent == "091") | (parent == "092") | (parent == "093") | (parent == "095") | (parent == "096") | (parent == "097")')
    name = "name.str.contains('"+city+"')"
    match = cities.query(name, engine='python')
    if match.empty:
        return str(city+" ist keine Stadt in Bayern, oder?") #--> repeat question
    else:
        global myid
        myid = match.index[0] #at the moment, simply the first one out of the "Landkreis" of the city and the city is chosen - needs to be changed 
        return str(city+" ist eine schöne Stadt! Gibt es ein Thema, das dich zu " +city+" besonders interessiert? Bitte gib einen Begriff wie 'Abfälle', 'Unfälle' oder 'Geld' ein")
    
@app.route("/get2")
def get_bot_response_zwei():
    global userText_two
    userText_two = request.args.get('msg_second')
    description = "long_description.str.contains('"+userText_two+"')" ##first check short_description
    global table
    table = get_statistics().query(description, engine='python')
    global term
    term = table['short_description'].iloc[0]
    reply = "Interessiert dich zu "+city+" das Thema "+"'"+term+"'"+"?"
    # First filter tables in which Bavaria plays a role, then ask this
    # Right now, only yes as a reply possible
    return str(reply)


@app.route("/get3")
def get_bot_response_drei():
    userText_three = request.args.get('msg_third')
    plot_png()
    return str("Unten hast du einen Plot zum Thema "+"'"+userText_two+"'"+".")


def get_chart():
    q = Query.region(myid)
    field = table.iloc[0]
    field = field.name
    f1 = q.add_field(field)
    #f1.get_info()
    results = q.results()
    df = results.set_index('year')
    fig = go.Figure()
    fig.add_trace(
        go.Scattergl(
            x=df.index,
            y=df[field],
            mode="lines+markers",
            name="AI1302",
        )
    )
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text=term+" in " +city)
    fig.show
    return fig

   


@app.route('/static/images/plot.png')
def plot_png():
    try: 
        fig = get_chart()
        os.remove('/static/images/plot.png')
        output = io.BytesIO()
        canvas.print_png(output)
        response = make_response(output.getvalue())
        response.mimetype = 'image/png'
        return response
    except:
        error = "no file"
        return error





if __name__ == "__main__":
    app.run()