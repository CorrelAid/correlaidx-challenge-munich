from datenguidepy import Query
from datenguidepy.query_helper import get_regions, get_statistics
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from flask import Response
import io
from flask import Flask, render_template, request, session
from flask import send_file  # to download files
from string import punctuation
import logging
import geopandas as gpd
from textwrap import wrap
from matplotlib.ticker import MaxNLocator  # for integer values when plotting


import spacy
import numpy as np

nlp = spacy.load("de_core_news_lg")  # German

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
    if ("ja" == text or "ja " in text or "ja." in text or "ja," in text or "gerne" in text or "ok" in text or "jo" in text or "ja!" in text):
        return True
    else:
        return False


def recognizeNo(Text):
    text = Text.lower()
    if ("nein" in text or "nicht" in text or "ne" in text):
        return True
    else:
        return False

# chooses the city/region from the list; names which are in the list will regardless in which order the words are written be matched to the correct names


def getCity(text):
    global n
    global z
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
    session['myid'] = myid
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
        session['info'] = info
        return term
    except:
        return "False"


app = Flask(__name__)
app.secret_key = "super secret key"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


proposal = ""
ansDict = {1: "Warst du schon mal in Bayern?",
           2: "Schade, es ist echt schön hier! In München gibt es die meisten Touristen in Bayern. Vielleicht magst du ja mal vorbeikommen?",
           3: "Was ist denn deine Lieblingsstadt in Bayern? Oder hast du keine?",
           4: "Hmm, den Bezirk scheine ich leider nicht zu kennen. Kennst du vielleicht die Region in der er liegt oder hast du dich vielleicht verschrieben?",
           5: "Möchtest du stattdessen vielleicht erstmal etwas über ganz Bayern erfahren?",
           6: "Ok, hier ein interessanter Plot zu Bayern:",
           7: "Schade, möchtest du stattdessen einen Plot über ganz Bayern sehen?",
           8: "Das ist eine schöne Region! Gibt es ein Thema, das dich hierzu besonders interessiert?",
           9: "Interessiert dich das Thema...?",
           10: "Links hast du einen Plot zum Thema. Beim Download-Button kannst du dir die CSV-Datei herunterladen.",
           11: "Hier ein paar Erklärungen zu den Daten:",
           12: "Vielleicht interessiert dich das Thema "+proposal+"?",
           13: "Möchtest du gerne noch etwas über eine andere Region erfahren?",
           14: "Welche Region interessiert dich denn besonders?",
           15: "Danke fürs Vorbeischauen. Bis zum nächsten Mal!",
           16: "Gibt es ein Thema, das dich zu Bayern besonders interessiert? Bitte gib einen Begriff wie 'Abfälle', 'Verkehrsunfälle' oder 'Verstorbene' ein",
           17: "Interessiert dich zu Bayern das Thema...",
           18: "Hmmm...Vielleicht interessiert dich zu Bayern das Thema...",
           19: "Ups, dazu konnte ich leider nichts plotten. Welches andere Thema interessiert dich zu Bayern?",
           20: "Ups, dazu konnte ich leider nichts plotten. Welches andere Thema interessiert dich?",
           21: "Möchtest du gerne noch etwas über ganz Bayern erfahren?",
           22: "Das freut mich zu hören! Wusstest du schon, dass es in München die meisten Touristen in Bayern gibt?"}

plot_con = "False"
city = ""
topic = ""
info = ""


@app.route("/")
def index():
    filePath = "downloads/data.csv"
    session['last'] = 0
    session['plotChoice'] = "Flo"
    if os.path.exists(filePath):
        os.remove(filePath)
    return render_template("index.html")


@app.route("/getPlot")
def plot():
    plot_con = session.get('plot_con')
    return plot_con


def get_chart():
    topic = session.get('topic')
    myid = session.get('myid')
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
    axis = fig.add_subplot(1, 1, 1)
    xs = x = df.index
    ys = y = df[field]

    axis.plot(xs, ys, linestyle='--', marker='o', color='b')

    axis.set_xlabel('Time')
    axis.set_ylabel("\n".join(wrap(topic+" in " + session.get('city'), 60)))
    axis.xaxis.set_major_locator(MaxNLocator(integer=True))
    fig.tight_layout()

    return fig


@app.route("/resetLast")
def reset():
    session['last'] = 0
    session['plot_con'] = "False"
    return "true"


@app.route('/static/images/plot.png')
def plot_png():
    plotChoice = session.get('plotChoice')
    try:
        if (plotChoice == "Michael"):
            fig = get_chart_map()
        else:
            fig = get_chart()
        app.logger.debug("figure: %s", str(fig))
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
        return Response(output.getvalue(), mimetype='image/png')
    except Exception as e:
        app.logger.error('an error occurred during plotting: ', e)
        error = "no file"
        return error


@app.route("/getGlobal")
def bot_response():
    last = session.get('last')
    global ansDict
    plot_con = session.get('plot_con')
    city = session.get('city')
    topic = session.get('topic')
    global proposal
    info = session.get('info')
    plotChoice = session.get('plotChoice')
    userText = request.args.get('msg')
    chars = '.!' #special char removal
    for c in chars:
        userText = userText.replace(c, '')
    if last == 0:
        last = 1
        separator = ' '
        name = separator.join(get_hotwords(userText))
        session['last'] = last
        if bytearray.fromhex("416c696365").decode('latin-1') in userText:
            session['last'] = 2
            return bytearray.fromhex("426973742064752064617320412e4c2e492e432e452e3f2042696e2065696e2067726fdf65722046616e20766f6e20646972203c33").decode('latin-1')
        return "Hallo "+name + "! "+ansDict[1]
    elif last == 1:
        last = 2
        session['last'] = last
        if recognizeYes(userText):
            return ansDict[22]
        else:
            return ansDict[2]
    elif last == 2:
        last = 3
        session['last'] = last
        return ansDict[3]
    elif last == 3:
        if "keine" in userText.lower():
            last = 5
            session['last'] = last
            return ansDict[5]
        else:
            last = 8
            session['last'] = last
            city = getCity(userText)
            session['city'] = city
            return city+" ist ein schöner Ort! Welches Thema interessiert dich hierzu besonders?"
    elif last == 5:
        if recognizeYes(userText):
            last = 16
            session['last'] = last
            return ansDict[16]
        else:
            last = 13
            session['last'] = last
            return ansDict[13]
    elif last == 6:
        session['plot_con'] = 'False'
        last = 11
        session['last'] = last
        return "Hier ein paar Erklärungen zu den Daten:"+info
    elif last == 7:
        if recognizeYes(userText):
            last = 16
            session['last'] = last
            return ansDict[16]
        else:
            last = 13
            session['last'] = last
            return ansDict[13]
    elif last == 8 or last == 20:
        topic = get_topic(userText)
        session['topic'] = topic
        if topic == "False":
            last = 12
            session['last'] = last
            proposal = "Verkehrsunfälle"
            return "Hmm...Vielleicht interessiert dich das Thema "+proposal+"?"
        else:
            last = 9
            session['last'] = last
            return "Interessiert Dich das Thema "+topic+"?"
    elif last == 9:
        if recognizeYes(userText):
            plotChoice = "Flo"
            session['plotChoice'] = plotChoice
            last = 10
            session['last'] = last
            session['plot_con'] = 'True'
            plot_png()
            if (plot_png() == "no file"):
                session['plot_con'] = 'False'
                last = 20
                session['last'] = last
                return ansDict[20]
            else:
                return ansDict[10]
        else:
            last = 12
            session['last'] = last
            proposal = "Abfälle"
            return "Hmm...Vielleicht interessiert dich das Thema "+proposal+"?"
    elif last == 10:
        session['plot_con'] = 'False'
        last = 11
        session['last'] = last
        return "Hier ein paar Erklärungen zu den Daten:"+info
    elif last == 11:
        last = 13
        session['last'] = last
        return ansDict[13]
    elif last == 12:
        if recognizeNo(userText):
            last = 7
            session['last'] = last
            return ansDict[7]
        else:
            last = 9
            session['last'] = last
            topic = get_topic(proposal)
            session['topic'] = topic
            return "Interessiert dich das Thema "+topic+"?"
    elif last == 13:
        if recognizeYes(userText):
            last = 14
            session['last'] = last
            return ansDict[14]
        else:
            last = 21
            session['last'] = last
            return ansDict[21]
    elif last == 14:
        last = 8
        session['last'] = last
        city = getCity(userText)
        session['city'] = city
        return city+" ist ein schöner Ort! Gibt es ein Thema, das dich hierzu besonders interessiert?"
    elif last == 15:
        return None
    elif last == 16 or last == 19:
        last = 17
        session['last'] = last
        topic = get_topic(userText)
        session['topic'] = topic
        if (topic == 'False'):
            last = 18
            session['last'] = last
            proposal = "Abfälle"
            return "Hmm...Vielleicht interessiert dich zu Bayern das Thema "+proposal+"? Falls ja, gib mir bitte etwas Zeit alles zu berechnen"
        else:
            return "Interessiert dich zu Bayern das Thema "+topic+"? Falls ja, gib mir bitte etwas Zeit alles zu berechnen"
    elif last == 17:
        if recognizeYes(userText):
            session['plot_con'] = 'True'
            plotChoice = "Michael"
            plot_png()
            session['plotChoice'] = plotChoice
            if (plot_png() == "no file"):
                session['plot_con'] = 'False'
                last = 19
                session['last'] = last
                return ansDict[19]
            else:
                last = 6
                session['last'] = last
                return ansDict[6]
        else:
            last = 18
            session['last'] = last
            proposal = "Abfälle"
            return "Hmm...Vielleicht interessiert dich zu Bayern das Thema "+proposal+"?"
    elif last == 18:
        if recognizeNo(userText):
            last = 13
            session['last'] = last
            return ansDict[13]
        else:
            last = 17
            session['last'] = last
            topic = get_topic(proposal)
            session['topic'] = topic
            return "Interessiert dich das Thema "+topic+"?"
    elif last == 21:
        if recognizeYes(userText):
            last = 16
            session['last'] = last
            return ansDict[16]
        else:
            last = 15
            session['last'] = last
            return ansDict[15]


@app.route('/download')
def download_file():
    try:
        path = "downloads/data.csv"
        return send_file(path, as_attachment=True, cache_timeout=0)
    except FileNotFoundError:
        abort(404)


def get_chart_map():  # this is calling the chart
    try:
        topic = session.get('topic')
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
            fig.suptitle(topic + " in " + str(max_year))
            axis.set_axis_off()

            # return fig.get_figure()
            return fig
    except Exception as e:
        app.logger.error(
            'an error occurred during the creation of the map:', e)


@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'max-age=300'
    return response


if __name__ == "__main__":
    app.run()

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
