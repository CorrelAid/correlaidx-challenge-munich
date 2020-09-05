# imports
from spacy.matcher import Matcher  # for patterns
import plotly.graph_objs as go
import dash_core_components as dcc
import dash_html_components as html
import dash_bio as dashbio
import dash
from six import PY3
import six.moves.urllib.request as urlreq
import json
import matplotlib
import pandas as pd
from datenguidepy import Query
from datenguidepy.query_helper import get_regions, get_statistics
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from flask import Response
import random
import io
from spacy.tokens import Doc
from flask import Flask, render_template, request
from flask import send_file #to download files

import spacy
import numpy
nlp = spacy.load("de_core_news_sm")  # German
matcher = Matcher(nlp.vocab)


# Here comes the regionaldatenbank.de part
# These are the steps given by Correlaid:
# %load_ext autoreload
# %autoreload

if not os.path.basename(os.getcwd()) == "datenguide-python":
    os.chdir("..")


# %matplotlib inline


app = Flask(__name__)
# define app routes


@app.route("/")
def index():
    filePath = "downloads/data.csv"
    if os.path.exists(filePath):
        os.remove(filePath)
    return render_template("index.html")

@app.route("/get")
# function for the bot response
def get_bot_response():
    userText = request.args.get('msg')
    pd.set_option('display.max_colwidth', 150)
    # get the ID of Berlin by querying all states by name
    get_regions().query("name == 'Bayern'")
    city_one = nlp(userText)  # nlp makes the text readable for spacy
    # ents recognizes names of cities, important persons, countries,...
    first = city_one.ents[0]
    global city
    city = first.text
    # this recognizes if the city is in Bavaria
    regions = get_regions().query("level == 'nuts2'")
    parents = regions.query('parent == "09"')
    #ids = parents.index
    regions = get_regions().query("level == 'nuts3'")
    cities = regions.query(
        '(parent == "091") | (parent == "092") | (parent == "093") | (parent == "095") | (parent == "096") | (parent == "097")')
    name = "name.str.contains('"+city+"')"
    match = cities.query(name, engine='python')
    if match.empty:
        # --> repeat question
        return str(city+" ist keine Stadt in Bayern, oder?")
    else:
        global myid
        # at the moment, simply the first one out of the "Landkreis" of the city and the city is chosen - needs to be changed
        myid = match.index[0]
        return str(city+" ist eine schöne Stadt! Gibt es ein Thema, das dich zu " + city+" besonders interessiert? Bitte gib einen Begriff wie 'Abfälle', 'Unfälle' oder 'Geld' ein")


@app.route("/get2")
def get_bot_response_zwei():
    global userText_two
    userText_two = request.args.get('msg_second')
    # first check short_description
    description = "long_description.str.contains('"+userText_two+"')"
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
    return str("Unten hast du einen Plot zum Thema "+"'"+userText_three+"'"+".")


def get_chart():
    q = Query.region(myid)
    field = table.iloc[0]
    field = field.name
    f1 = q.add_field(field)
    # f1.get_info()
    results = q.results()
    df = results.set_index('year')
    #Save df as csv
    df.to_csv('downloads/data.csv', sep='\t')
    
    # #Plotpy, not working this way, maybe good for a non static plot later? 
    # fig = go.Figure()
    # fig.add_trace(
    #     go.Scattergl(
    #         x=df.index,
    #         y=df[field],
    #         mode="lines+markers",
    #         name="AI1302",
    #     )
    # )
    # fig.update_xaxes(title_text="Time")
    # fig.update_yaxes(title_text=term+" in " +city)
    # fig.show

    #Using matplotlib instead of plotly:
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    xs = x=df.index
    ys = y=df[field]
    axis.plot(xs, ys, linestyle='--', marker='o', color='b')
    axis.set_xlabel('Time')
    axis.set_ylabel(term+" in " +city)    
    return fig



@app.route('/static/images/plot.png')
def plot_png():
    try: 
        fig = get_chart()
        # os.remove('/static/images/plot.png') #this replaces the plot in the /static/images folder
        output = io.BytesIO()
        # canvas.print_png(output)
        # response = make_response(output.getvalue())
        # response.mimetype = 'image/png'
        FigureCanvas(fig).print_png(output)
        return Response(output.getvalue(), mimetype='image/png')
    except:
        error = "no file"
        return error


@app.route('/download')
def download_file():
    try:
        #return send_from_directory('./download/', filename='data.csv', as_attachment=True, cache_timeout=0)
        path = "downloads/data.csv"
        return send_file(path, as_attachment=True, cache_timeout=0)
    except FileNotFoundError:
        abort(404)


if __name__ == "__main__":
    app.run()
