#imports
from flask import Flask, render_template, request #we need flask to visualize Python such that JavaScript and Python understand each other
import spacy #spacy is useful for chatbots and works with nlp
import numpy
nlp = spacy.load("de_core_news_sm") #German
from spacy.matcher import Matcher #for patterns #maybe not needed in the end
from spacy.tokens import Doc #maybe not needed in the end
matcher = Matcher(nlp.vocab) #mabye not needed in the end
import io #really needed?
import random #really needed?
from flask import Response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas #for the plot
from matplotlib.figure import Figure


#%load_ext autoreload
#%autoreload
import os #really needed?
if not os.path.basename(os.getcwd()) == "datenguide-python":
    os.chdir("..")
    
    
from datenguidepy.query_helper import get_regions, get_statistics #this is the Correlaid package
from datenguidepy import Query
import pandas as pd #df
import matplotlib
#%matplotlib inline


import json
import six.moves.urllib.request as urlreq #really needed?
from six import PY3 #really needed?

import dash
import dash_bio as dashbio
import dash_html_components as html
import dash_core_components as dcc

import plotly.graph_objs as go #for plotting the data



app = Flask(__name__) #this is needed to initialise flask
#define app routes which reappear in the Javascript part on index.html
@app.route("/")
def index():
    return render_template("index.html")


#This is called by the JavaScript function getResponse in index.html
@app.route("/get")
#function for the bot response
def get_bot_response():
    userText = request.args.get('msg') #this is the input text
    pd.set_option('display.max_colwidth', 150)
    # get the ID of Berlin by querying all states by name
    get_regions().query("name == 'Bayern'") 
    city_one = nlp(userText) #nlp makes the text readable for spacy
    first = city_one.ents[0] #ents recognizes names of cities, important persons, countries,...
    global city
    city = first.text
    regions = get_regions().query("level == 'nuts2'") #this recognizes if the city is in Bavaria #nuts1 are states of Germany; nuts2 are substates; nuts3 are cities
    parents = regions.query('parent == "09"') #09 is the id of Bavaria; here we find out the ids of the subregions of Bavaria which have the Bavaria id "09" as a parent
    ids = parents.index
    regions = get_regions().query("level == 'nuts3'") #
    cities = regions.query('(parent == "091") | (parent == "092") | (parent == "093") | (parent == "095") | (parent == "096") | (parent == "097")') #to filter the cities which have one of the subregions as a parent
    name = "name.str.contains('"+city+"')"
    match = cities.query(name, engine='python')
    if match.empty:
        return str(city+" ist keine Stadt in Bayern, oder?") #--> repeat question
    else:
        global myid
        myid = match.index[0] #at the moment, simply the first one out of the "Landkreis" of the city and the city is chosen - needs to be changed 
        return str(city+" ist eine schöne Stadt! Gibt es ein Thema, das dich zu " +city+" besonders interessiert? Bitte gib einen Begriff wie 'Abfälle', 'Unfälle' oder 'Geld' ein")
    
@app.route("/get2") #this is called by the JavaScript function getSecondResponse
def get_bot_response_zwei():
    global userText_two
    userText_two = request.args.get('msg_second')
    description = "long_description.str.contains('"+userText_two+"')" #this checks the long description of the table for the input topic #first check short_description to be done
    global table
    table = get_statistics().query(description, engine='python')
    global term
    term = table['short_description'].iloc[0] #simply takes the first table appearing
    reply = "Interessiert dich zu "+city+" das Thema "+"'"+term+"'"+"?"
    # First filter tables in which Bavaria plays a role, then ask this
    # Right now, only yes as a reply possible
    return str(reply)

#the JavaScript function getThirdResponse is calling this
@app.route("/get3")
def get_bot_response_drei(): #variable names need to be changes
    userText_three = request.args.get('msg_third')
    plot_png()
    return str("Unten hast du einen Plot zum Thema "+"'"+userText_two+"'"+".")


def get_chart(): #this is calling the chart
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



@app.route('/static/images/plot.png')  #at the moment, the plot is first converted to a png
def plot_png():
    try: 
        fig = get_chart()
        os.remove('/static/images/plot.png') #this replaces the plot in the /static/images folder
        output = io.BytesIO()
        canvas.print_png(output)
        response = make_response(output.getvalue())
        response.mimetype = 'image/png'
        return response
    except:
        error = "no file"
        return error




if __name__ == "__main__":
    app.run() #this runs the app by Flask
