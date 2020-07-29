import streamlit as st
import spacy
import numpy
nlp = spacy.load("de_core_news_sm") #German
from spacy.matcher import Matcher #for patterns
from spacy.tokens import Doc
matcher = Matcher(nlp.vocab)

### Here comes the regionaldatenbank.de part
### These are the steps given by Correlaid:

import os
if not os.path.basename(os.getcwd()) == "datenguide-python":
    os.chdir("..")
    
    
from datenguidepy.query_helper import get_regions, get_statistics
from datenguidepy import Query
import pandas as pd
import matplotlib



import json
import six.moves.urllib.request as urlreq
from six import PY3

import dash
import dash_bio as dashbio
import dash_html_components as html
import dash_core_components as dcc


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

pd.set_option('display.max_colwidth', 150)
# get the ID of Berlin by querying all states by name
get_regions().query("name == 'Bayern'")



##########

add_selectbox = st.sidebar.selectbox(
    "Hier kann etwas hin",
    ("Email", "Home phone", "Mobile phone")
)

st.title('CorrelAidX Munich')
st.header('Our Chatbot')

my_placeholder = st.empty()


my_placeholder = st.text_input("Griaß di! Ich bin Bot und beantworte deine Fragen zu Bayern. Was ist deine Lieblingsstadt in Bayern?")


city = nlp(my_placeholder) #nlp makes the text readable for spacy
first = city.ents[0] #ents recognizes names of cities, important persons, countries,...
city = first.text
    
regions = get_regions().query("level == 'nuts2'") #this recognizes if the city is in Bavaria
parents = regions.query('parent == "09"')
ids = parents.index
regions = get_regions().query("level == 'nuts3'")
cities = regions.query('(parent == "091") | (parent == "092") | (parent == "093") | (parent == "095") | (parent == "096") | (parent == "097")')
name = "name.str.contains('"+city+"')"
match = cities.query(name, engine='python')
if match.empty:
    my_placeholder = st.text(city+" ist keine Stadt in Bayern, oder?") #--> repeat question
else:
    my_placeholder = st.text(city+" ist eine schöne Stadt!")
    myid = match.index[0] #at the moment, simply the first one out of the "Landkreis" of the city and the city is chosen - needs to be changed  
    
topic = st.text_input("Gibt es ein Thema, das dich zu " +city+" besonders interessiert? Bitte gib einen Begriff wie 'Abfälle', 'Pflegefälle' oder 'Geld' ein.") 

description = "long_description.str.contains('"+topic+"')" ##first check short_description
table = get_statistics().query(description, engine='python')

term = table['short_description'].iloc[0]

reply = st.text_input("Interessiert dich zu "+city+" das Thema "+"'"+term+"'"+"?")
# First filter tables in which Bavaria plays a role, then ask this
# Right now, only yes as a reply possible

q = Query.region(myid)
field = table.iloc[0]
field = field.name
f1 = q.add_field(field)
#f1.get_info()

results = q.results()

my_placeholder = st.text("Hier hast du einen Plot zum Thema "+"'"+topic+"'"+":")

import plotly.graph_objs as go

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

st.plotly_chart(fig)


