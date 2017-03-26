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

with open('replace_dict.pk1', 'rb') as picklefile:
    replace_dict = pickle.load(picklefile)

with open('all_genres.pk1', 'rb') as picklefile:
    all_genres = pickle.load(picklefile)

with open('festivals.pk1', 'rb') as picklefile:
    festivals = pickle.load(picklefile)


def user_genres(artists):
    genres_dict = defaultdict(int)
    for artist in artists:
        try:
            genre_result = spotify.search(q='artist:' + artist, type='artist')['artists']['items'][0]['genres']
            genre_list = []
            for genre in genre_result:
                new_genre = replace_genre(genre)
                if new_genre not in genre_list:
                    genre_list.append(new_genre)
            genre_list = top_three(genre_list)
            for genre in genre_list:
                genres_dict[genre] += 1
        except IndexError:
            next
    df = pd.DataFrame(genres_dict, index=["User",])
    df_norm = pd.DataFrame(preprocessing.normalize(df, norm='l1'), index=["User",], columns=list(df.columns))
    return df_norm


def replace_genre(genre):
    genre = genre.replace(' ', '_')
    new_genre = genre.replace('-', '_')
    new_genre = replace_dict[genre]
    return new_genre


def add_weights(x, user_artists):
    fest_name = x[1]
    lineup = list(festivals[festivals.name == fest_name]['lineup'])[0]
    count = 0
    for artist in user_artists:
        if artist in lineup:
            count += 1
    new_dist = x[0] + (count * 0.15)
    return new_dist


def top_three(genre_list):
    if len(genre_list) < 4:
        return genre_list
    else:
        most_pop = []     
        for genre in genre_list:
            most_pop.append((all_genres[genre], genre))
        most_pop.sort(reverse=True)
        selection = []
        for i in range(0, 3):
            top_genre = most_pop[i][1]
            selection.append(top_genre)
        return selection

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
    user_artists = data['bands']
    user = user_genres(user_artists)
    user_df = fest_genres_norm.append(user)
    user_df = user_df.fillna(0)
    user_case = user_df.ix[-1,:]
    distances = pd.DataFrame(
        cosine_similarity(fest_genres_norm, user_case.reshape(1, -1)),
        index=list(fest_genres_norm.index),
        columns=['distance']
    )
    distances['name'] = distances.index
    distances['weighted_dist'] = distances.apply(lambda x: add_weights(x, user_artists), axis=1)
    distances = distances.sort_values("weighted_dist", ascending=False)
    distances.reset_index(drop=True)
    distances = pd.merge(distances, festivals, on='name')
    distances.drop(
        [
            'distance', 
            'description', 
            'url', 
            'num_bands', 
            'num_unknowns', 
            'unknown_percent', 
            'genres',
            'unknown'
        ], 
        axis=1, 
        inplace=True
    )
    results_dict = distances.to_dict(orient='index')
    results = []
    for key, value in results_dict.items():
        results.append(value)
    return flask.jsonify(results)

if __name__ == '__main__':
   app.run(debug=True)