from spacy.matcher import Matcher  # for patterns
from datenguidepy import Query
from datenguidepy.query_helper import get_regions, get_statistics
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from flask import Response
import io
from flask import Flask, render_template, request
from flask import send_file  # to download files
from string import punctuation

import geopandas as gpd


import spacy
import numpy as np

nlp = spacy.load("de_core_news_sm")  # German
matcher = Matcher(nlp.vocab)

# preparing statistics
statistics = get_statistics().short_description.values.tolist()
desc = []
for names in statistics:
    desc.append(nlp(names))


# all regions on nut3 level in Bavaria
bezirke = get_regions().query("parent == '09'")
z = []
ids = []
for i in bezirke.index.values.tolist():
    ids = ids + get_regions().query("parent == '"+str(i)+"'").name.index.tolist()
    z = z + get_regions().query("parent == '"+str(i)+"'").name.values.tolist()


# transform names to nlp format for comparing
n = []
for names in map(lambda x: x.lower(), z):
    n.append(nlp(names))


def recognizeYes(Text):
    text = Text.lower()
    if ("ja" == text or "ja " in text or "ja." in text or "ja," in text or "gerne" in text or "ok" in text or "jo" in text):
        return True
    else:
        return False


def recognizeNo(Text):
    text = Text.lower()
    if ("nein" in text or "nicht" in text or "ne" in text):
        return True
    else:
        return False


def getCity(text):
    global n
    global z
    global myid
    sim = []
    com_doc = nlp(text.lower())
    for doc in n:
        list1 = []
        for teil in com_doc:
            list2 = []
            for token in doc:
                list2.append(token.similarity(teil))
            list1.append(max(np.array(list2)))
        mean = np.sum(np.array(list1))/len(list1)
        sim.append(mean)
    myid = ids[np.array(sim).argmax()]
    return z[np.array(sim).argmax()]


def get_hotwords(text):
    """Extract topic from the user input
    """
    result = []
    pos_tag = ['PROPN', 'ADJ', 'NOUN']
    doc = nlp(text)
    for token in doc:
        if(token.text in nlp.Defaults.stop_words or token.text in punctuation):
            continue
        if(token.pos_ in pos_tag):
            result.append(token.text)

    return result


def get_topic(input):
    global term
    global info
    try:
        sim_stat = []
        separator = ' '
        words = nlp(separator.join(get_hotwords(input)))
        for doc in desc:
            list1 = []
            for teil in words:
                list2 = []
                for token in doc:
                    list2.append(token.similarity(teil))
                list1.append(max(np.array(list2)))
            mean = np.array(list1).mean()
            sim_stat.append(mean)
        table = get_statistics().iloc[np.array(sim_stat).argmax()]
        term = table['short_description']
        info = table['long_description']
        info = info.split("===Aussage===")
        if (len(info) > 1):
            info = info[1]
        else:
            info = info[0]
        info = info.split("Indikatorberechnung")
        info = info[0]
        info = info.split("=")
        info = info[0]
        info = info[:500]
        return term
    except:
        return "False"


# Here comes the regionaldatenbank.de part
if not os.path.basename(os.getcwd()) == "datenguide-python":
    os.chdir("..")

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

last = 0
proposal = ""
ansDict = {1: "Warst Du schon mal in Bayern?",
           2: "Schade, es ist echt schön hier! In München gibt es die meisten Touristen in Bayern. Vielleicht magst Du ja mal vorbeikommen?",
           3: "Was ist denn Deine Lieblingsstadt in Bayern? Oder hast Du keine?",
           4: "Hmm, den Bezirk scheine ich leider nicht zu kennen. Kennst Du vielleicht die Region in der erliegt oder hast Du Dich vielleicht verschrieben?",
           5: "Möchtest Du stattdessen vielleicht erstmal etwas über ganz Bayern erfahren?",
           6: "Ok gerne, hier ein interessanter Plot zu Bayern:",
           7: "Schade, möchtest Du stattdessen einen Plot über ganz Bayern sehen?",
           8: "Das ist eine schöne Region! Gibt es ein Thema, das dich hierzu besonders interessiert?",
           9: "Interessiert Dich das Thema...?",
           10: "Links hast Du einen Plot zum Thema. Beim Download-Button kannst Du Dir die CSV-Datei herunterladen.",
           11: "Hier ein paar Erklärungen zu den Daten:",
           12: "Vielleicht interessiert dich das Thema "+proposal+"?",
           13: "Möchtest Du gerne noch etwas über eine andere Region erfahren?",
           14: "Welche Region interessiert Dich denn besonders?",
           15: "Danke fürs Vorbeischauen. Bis zum nächsten Mal!",
           16: "Gibt es ein Thema, das dich zu Bayern besonders interessiert? Bitte gib einen Begriff wie 'Abfälle', 'Verkehrsunfälle' oder 'Verstorbene' ein",
           17: "Interessiert dich zu Bayern das Thema...",
           18: "Hmmm...Vielleicht interessiert dich zu Bayern das Thema...",
           19: "Ups, dazu konnte ich leider nichts plotten. Welches andere Thema interessiert dich zu Bayern?",
           20: "Ups, dazu konnte ich leider nichts plotten. Welches andere Thema interessiert dich?",
           21: "Möchtest Du gerne noch etwas über ganz Bayern erfahren?",
           22: "Das freut mich zu hören! Wusstest du schon, dass in München die meinsten Touristen in Bayern gibt?"}

plot_con = "False"
city = ""
topic = ""
info = ""
plotChoice = "Flo"


@app.route("/")
def index():
    filePath = "downloads/data.csv"
    if os.path.exists(filePath):
        os.remove(filePath)
    return render_template("index.html")


@app.route("/getPlot")
def plot():
    global plot_con
    return plot_con


def get_chart():
    global topic
    global myid
    global term
    description = "short_description.str.contains('"+topic+"')"
    table = get_statistics().query(description, engine='python')
    q = Query.region(myid)
    field = table.iloc[0]
    field = field.name
    f1 = q.add_field(field)
    results = q.results()
    df = results.set_index('year')
    # Save df as csv
    df.to_csv('downloads/data.csv', sep='\t')

    fig = Figure()
    fig.tight_layout()
    axis = fig.add_subplot(1, 1, 1)
    xs = x = df.index
    ys = y = df[field]
    axis.plot(xs, ys, linestyle='--', marker='o', color='b')
    axis.set_xlabel('Time')
    axis.set_ylabel(term+" in " + city)
    fig.savefig('images/plot.png')
    return fig


@app.route("/resetLast")
def reset():
    global last
    global plot_con
    plot_con = "False"
    last = 0
    return "true"


@app.route('/static/images/plot.png')
def plot_png():
    global plotChoice
    try:
        if (plotChoice == "Michael"):
            fig = get_chart_map()
        else:
            fig = get_chart()
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
        return Response(output.getvalue(), mimetype='image/png')
    except:
        error = "no file"
        return error


@app.route("/getGlobal")
def bot_response():
    global last
    global ansDict
    global plot_con
    global city
    global term
    global topic
    global proposal
    global info
    global plotChoice
    userText = request.args.get('msg')
    if last == 0:
        last = 1
        separator = ' '
        name = separator.join(get_hotwords(userText))
        return "Hallo "+name + "! "+ansDict[1]
    elif last == 1:
        last = 2
        if recognizeYes(userText):
            return ansDict[22]
        else:
            return ansDict[2]
    elif last == 2:
        last = 3
        return ansDict[3]
    elif last == 3:
        if "keine" in userText.lower():
            last = 5
            return ansDict[5]
        else:
            last = 8
            city = getCity(userText)
            return city+" ist ein schöner Ort! Welches Thema interessiert dich hierzu besonders?"
    elif last == 5:
        if recognizeYes(userText):
            last = 16
            return ansDict[16]
        else:
            last = 13
            return ansDict[13]
    elif last == 6:
        plot_con = 'False'
        last = 11
        return "Hier ein paar Erklärungen zu den Daten:"+info
    elif last == 7:
        if recognizeYes(userText):
            last = 16
            return ansDict[16]
        else:
            last = 13
            return ansDict[13]
    elif last == 8 or last == 20:
        topic = get_topic(userText)
        if topic == "False":
            last = 12
            proposal = "Verkehrsunfälle"
            return "Hmm...Vielleicht interessiert dich das Thema "+proposal+"?"
        else:
            last = 9
            return "Interessiert Dich das Thema "+topic+"?"
    elif last == 9:
        if recognizeYes(userText):
            plotChoice = "Flo"
            last = 10
            plot_con = 'True'
            plot_png()
            if (plot_png() == "no file"):
                plot_con = 'False'
                last = 20
                return ansDict[20]
            else:
                return ansDict[10]
        else:
            last = 12
            proposal = "Abfälle"
            return "Hmm...Vielleicht interessiert dich das Thema "+proposal+"?"
    elif last == 10:
        plot_con = 'False'
        last = 11
        return "Hier ein paar Erklärungen zu den Daten:"+info
    elif last == 11:
        last = 13
        return ansDict[13]
    elif last == 12:
        if recognizeNo(userText):
            last = 7
            return ansDict[7]
        else:
            last = 9
            topic = get_topic(proposal)
            return "Interessiert Dich das Thema "+topic+"?"
    elif last == 13:
        if recognizeYes(userText):
            last = 14
            return ansDict[14]
        else:
            last = 21
            return ansDict[21]
    elif last == 14:
        last = 8
        city = getCity(userText)
        return city+" ist ein schöner Ort! Gibt es ein Thema, das dich hierzu besonders interessiert?"
    elif last == 15:
        return None
    elif last == 16 or last == 19:
        last = 17
        topic = get_topic(userText)
        if (topic == 'False'):
            last = 18
            proposal = "Abfälle"
            return "Hmm...Vielleicht interessiert dich zu Bayern das Thema "+proposal+"? Falls ja, gib mir bitte etwas Zeit alles zu berechnen"
        else:
            return "Interessiert dich zu Bayern das Thema "+topic+"? Falls ja, gib mir bitte etwas Zeit alles zu berechnen"
    elif last == 17:
        if recognizeYes(userText):
            plot_con = 'True'
            plotChoice = "Michael"
            plot_png()
            if (plot_png() == "no file"):
                plot_con = 'False'
                last = 19
                return ansDict[19]
            else:
                last = 6
                return ansDict[6]
        else:
            last = 18
            proposal = "Abfälle"
            return "Hmm...Vielleicht interessiert dich zu Bayern das Thema "+proposal+"?"
    elif last == 18:
        if recognizeNo(userText):
            last = 13
            return ansDict[13]
        else:
            last = 17
            topic = get_topic(proposal)
            return "Interessiert Dich das Thema "+topic+"?"
    elif last == 21:
        if recognizeYes(userText):
            last = 16
            return ansDict[16]
        else:
            last = 15
            return ansDict[15]


@app.route('/download')
def download_file():
    try:
        path = "downloads/data.csv"
        return send_file(path, as_attachment=True, cache_timeout=0)
    except FileNotFoundError:
        abort(404)


def get_chart_map():  # this is calling the chart
    global topic
    regions = get_regions().query("level == 'nuts3'")
    cities = regions.query(
        '(parent == "091") | (parent == "092") | (parent == "093") | (parent == "094") | (parent == "095") | (parent == "096") | (parent == "097")')

    # get multiple regions
    q = Query.region(list(cities.index))

    description = "short_description.str.contains('"+topic+"')"
    table = get_statistics().query(description, engine='python')

    field = table.iloc[0]
    field = field.name
    q.add_field(field)
    results_nuts3 = q.results()

    # read in shps
    shp_nuts2 = gpd.read_file("shp/bavaria_nuts2")
    max_year = max(results_nuts3["year"])
    results_nuts3_lastyear = results_nuts3[results_nuts3["year"] == max_year]

    # prep for merging
    results_nuts3_lastyear = results_nuts3_lastyear.drop_duplicates()
    # test if df is empty
    row = results_nuts3_lastyear.iloc[4]
    emptytest = row.iloc[4]
    if(len(emptytest) != 0):
        results_nuts3_lastyear.loc[:, "name2"] = results_nuts3_lastyear["name"].str.replace(
            ", Landkreis", "")
        results_nuts3_lastyear.loc[:, "name2"] = results_nuts3_lastyear["name2"].str.replace(
            ", Landeshauptstadt", "")

    # merge datenguide data
        plot_data = shp_nuts2.merge(results_nuts3_lastyear,
                                    left_on="CC_2",
                                    right_on="id")

    # plot
        fig = Figure()
        axis = fig.add_subplot(1, 1, 1)

        axis = plot_data.plot(column=field, legend=True, ax=axis)
        #fig.suptitle(term + " in " + str(max_year))
        fig.suptitle(topic + " in " + str(max_year))
        axis.set_axis_off()

    # return fig.get_figure()
    fig.savefig('foo4.png')
    return fig


if __name__ == "__main__":
    app.run()