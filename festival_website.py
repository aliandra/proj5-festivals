import flask
import pandas as pd 
from sklearn.metrics.pairwise import cosine_similarity
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pickle
import config
from collections import defaultdict
from sklearn import preprocessing


#---------- MODEL IN MEMORY----------#

ccm = SpotifyClientCredentials(
    client_id=config.client_id,
    client_secret=config.client_secret
)

spotify = spotipy.Spotify(client_credentials_manager=ccm)

# load pickeled genre data
with open('fest_genres_norm.pk1', 'rb') as picklefile:
    fest_genres_norm = pickle.load(picklefile)

def user_genres(artists):
    genres = defaultdict(int)

    for artist in artists:
        try:
            genre_result = spotify.search(q='artist:' + artist, type='artist')['artists']['items'][0]['genres']
            for genre in genre_result:
                new_genre = replace_genre(genre)
                genres[new_genre] += 1
        except IndexError:
            next
    df = pd.DataFrame(genres, index=["User",])
    df_norm = pd.DataFrame(preprocessing.normalize(df, norm='l1'), index=["User",], columns=list(df.columns))
    return df_norm


def replace_genre(genre):
    genre = genre.replace(' ', '_')
    new_genre = genre.replace('-', '_')
    return new_genre
#----------WEB APP----------#

# Initialize the app
app = flask.Flask(__name__)


# Homepage
@app.route("/")
def viz_page():
    with open("festival_website.html", 'r') as viz_file:
        return viz_file.read()


@app.route("/findfest", methods=["POST"])
def findfest():
    data = flask.request.json
    bands_list = data['bands']
    user = user_genres(bands_list)
    user_df = user.append(fest_genres_norm.ix[0, :])
    user_df = user_df.fillna(0)
    distances = pd.DataFrame(
        cosine_similarity(fest_genres_norm, user_df.ix[0, :]),
        index=list(fest_genres_norm.index),
        columns=['distance']
    )
    distances = distances.sort_values("distance")
    results = list(distances.index[-5:])
    return flask.jsonify(results)

if __name__ == '__main__':
   app.run(debug=True)