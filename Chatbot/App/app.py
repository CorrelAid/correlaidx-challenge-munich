#imports
from flask import Flask, render_template, request #we need flask to visualize Python such that JavaScript and Python understand each other
import spacy #spacy is useful for chatbots and works with nlp
from string import punctuation
import numpy
nlp = spacy.load("de_core_news_sm") #German
from spacy.matcher import Matcher #for patterns #maybe not needed in the end
from spacy.tokens import Doc #maybe not needed in the end
matcher = Matcher(nlp.vocab) #mabye not needed in the end
import io #really needed?
import random #really needed?
from flask import Response
from flask import send_from_directory #to download files
from flask import send_file #to download files

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

# additional charts
import seaborn as sns
import geopandas as gpd


app = Flask(__name__) #this is needed to initialise flask
#define app routes which reappear in the Javascript part on index.html
@app.route("/")
def index():
    filePath = "downloads/data.csv"
    if os.path.exists(filePath):
        os.remove(filePath)
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
    city = first.text.capitalize() # handle lowercase input
    global regions
    regions = get_regions().query("level == 'nuts2'") #this recognizes if the city is in Bavaria #nuts1 are states of Germany; nuts2 are substates; nuts3 are cities
    parents = regions.query('parent == "09"') #09 is the id of Bavaria; here we find out the ids of the subregions of Bavaria which have the Bavaria id "09" as a parent
    ids = parents.index
    regions = get_regions().query("level == 'nuts3'") #
    global cities
    cities = regions.query('(parent == "091") | (parent == "092") | (parent == "093") | (parent == "095") | (parent == "096") | (parent == "097")') #to filter the cities which have one of the subregions as a parent
    name = "name.str.contains('"+city+"')"
    match = cities.query(name, engine='python')
    if match.empty:
        return str(city+" ist keine Stadt in Bayern, oder?") #--> repeat question
    else:
        global myid
        myid = match.index[0] #at the moment, simply the first one out of the "Landkreis" of the city and the city is chosen - needs to be changed 
        return str(city+" ist eine schöne Stadt! Gibt es ein Thema, das dich zu " +city+" besonders interessiert? Bitte gib einen Begriff wie 'Abfälle', 'Unfälle' oder 'Geld' ein")
    

def get_hotwords(text):
    """Extract topic from the user input
    """
    result = []
    pos_tag = ['PROPN', 'ADJ', 'NOUN'] 
    doc = nlp(text.lower()) 
    for token in doc:
        if(token.text in nlp.Defaults.stop_words or token.text in punctuation):
            continue
        if(token.pos_ in pos_tag):
            result.append(token.text)
                
    return result 


@app.route("/get2") #this is called by the JavaScript function getSecondResponse
def get_bot_response_zwei():
    global userText_two
    userText_two = request.args.get('msg_second')
    description = "long_description.str.contains('"+get_hotwords(userText_two)[0]+"')" #this checks the long description of the table for the input topic #first check short_description to be done
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

def get_chart2(): #this is calling the chart
    q = Query.region(myid)
    field = table.iloc[0]
    field = field.name
    f1 = q.add_field(field)
    #f1.get_info()
    results = q.results()
    df = results.set_index('year')
    #Save df as csv
    df.to_csv('downloads/data.csv', sep='\t')
    
    # get other data from same "Regierungsbezirk"
    myid_parent = regions.loc[myid]["parent"]
    regions_nuts3_sub = regions.query('(parent == "' + myid_parent + '")')
    q = Query.region(list(regions_nuts3_sub.index))
    q.add_field(field)
    regions_nuts3_sub = q.results()
    
    fig = sns.relplot(x = "year", y = field, 
                      hue = "name", 
                      data = regions_nuts3_sub)

    return fig.fig

def get_chart_map(): #this is calling the chart

    # get multiple regions
    q = Query.region(list(cities.index))
    field = table.iloc[0]
    field = field.name
    q.add_field(field)
    results_nuts3 = q.results()
        
    # read in shps
    shp_nuts2 = gpd.read_file("shp/bavaria_nuts2")
    # shp_nuts3 = gpd.read_file("shp/bavaria_nuts3")
    
    # average datenguide (or extract last year)
    # results_nuts2_lastyear = results_nuts2[results_nuts2["year"] == max(results_nuts2["year"])]
    results_nuts3_lastyear = results_nuts3[results_nuts3["year"] == max(results_nuts3["year"])]
    
    # prep for merging
    results_nuts3_lastyear = results_nuts3_lastyear.drop_duplicates()
    results_nuts3_lastyear.loc[:, "name2"] = results_nuts3_lastyear["name"].str.replace(", Landkreis", "")
    results_nuts3_lastyear.loc[:, "name2"] = results_nuts3_lastyear["name2"].str.replace(", Landeshauptstadt", "")
    
    # merge datenguide data
    plot_data = shp_nuts2.merge(results_nuts3_lastyear, 
                                left_on="NAME_2", 
                                right_on="name2")

    # plot 
    fig = plot_data.plot(column = field, legend = True)

    return fig.get_figure()



@app.route('/static/images/plot.png')  #at the moment, the plot is first converted to a png
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
    app.run() #this runs the app by Flask

    