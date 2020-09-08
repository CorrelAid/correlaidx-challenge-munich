# The datenguide chatbot

The [datenguide project](https://datengui.de/) creates an interface to the 
statistics provided by the local authorities in Germany. However, one still
needs programming knowledge to use the datenguide API and query the
statistics. In order to make the data more accessible to the general public,
we build a chatbot, which utilizes the datenguide API and specifically answers 
your questions and renders visualizations about diverse topics in Bavaria.

This project was created by the Munich local chapter of Correlaid for the 
CorrelaidX challenge.

## Getting started

- Create a Python virtual environment, and install all dependencies as 
specified in `requirements.txt`.
- Navigate to the `/App` folder and run `python app.py`.
- Open `localhost:5000` in the browser to interact with the chatbot.

## Dialog flow

The chatbot first asks the user for her favorite city in Bavaria and then
for a specific topic of interest. It then uses the datenguide API to search
the regional statistics database for data related to the given city and topic.
Finally it renders a plot using the appropriate data. The user can also
download the raw data of the plot in the csv format.

## Tech stack

The chatbot is built as a web application using the Flask framework. The 
SpaCy library is used to process the text input.