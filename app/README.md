# The datenguide chatbot

The [datenguide project](https://datengui.de/) creates an interface to the 
statistics provided by the local authorities in Germany. However, one still
needs programming knowledge to use the datenguide API and query the
statistics. In order to make the data more accessible to the general public,
we build a chatbot, which utilizes the datenguide API and specifically answers 
your questions and renders visualizations about diverse topics in Bavaria.

This project was created by the Munich local chapter of Correlaid for the 
CorrelaidX challenge.

![Chatbot](https://github.com/CorrelAid/correlaidx-challenge-munich/blob/master/.github/chatbot_pic3.PNG)

## Getting started
### Virtual environment and installation
1. create and activate a Python virtual environment, e.g. with [virtualenv](https://virtualenv.pypa.io/en/latest/) or the built-in [venv](https://docs.python.org/3/library/venv.html) module:

```
# with virtualenv 
virtualenv venv
source venv/bin/activate
```

2. install the dependencies
```
pip -r requirements.txt
```

### Run app locally
1. navigate to the `/app` folder
2. start the app
```
python main.py
```

or with `[gunicorn](https://gunicorn.org/)`
```
gunicorn main:app -c gunicorn_config.py
```
3. Open `localhost:5000` in the browser to interact with the chatbot. Be sure to use either Chrome or Firefox as the browser to have the best
rending effects.

### Geopandas hints
If you are pip installing geopandas, make sure to install the dependencies. 
On Windows, you might try:
```
pip install wheel
pip install pipwin
pipwin install numpy
pipwin install pandas
pipwin install shapely
pipwin install gdal
pipwin install fiona
pipwin install pyproj
pipwin install six
pipwin install rtree
pipwin install geopandas
```

Otherwise,  download GDAL and fiona via https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal and https://www.lfd.uci.edu/~gohlke/pythonlibs/#fiona or use conda.

## Dialog flow

The chatbot first asks the user for her favorite city in Bavaria and then
for a specific topic of interest. It then uses the datenguide API to search
the regional statistics database for data related to the given city and topic.
Finally it renders a plot using the appropriate data. The user can also
download the raw data of the plot in the csv format.

## Tech stack

The chatbot is built as a web application using the Flask framework. The 
SpaCy library is used to process the text input.

## Deployment
The app is deployed on a CorrelAid Ubuntu server. 
For that, `gunicorn` is used.

in `app`:

```
gunicorn main:app -c gunicorn_config_prod.py
```

the app runs behind a Nginx reverse proxy. 