import flask
import pandas as pd 
from sklearn.metrics.pairwise import cosine_similarity

#---------- MODEL IN MEMORY----------#




#----------WEB APP----------#

# Initialize the app
app = flask.Flask(__name__)

# Homepage
@app.route("/")
def viz_page():
	with open("festival_website.html", 'r') as viz_file:
		return viz_file.read()

if __name__ == '__main__':
   app.run(debug=True)