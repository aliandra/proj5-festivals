import flask
import pandas as pd 
from sklearn.metrics.pairwise import cosine_similarity
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pickle
import config
from collections import defaultdict
from sklearn import preprocessing
from sklearn.metrics.pairwise import euclidean_distances


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

with open('artist_average.pk1', 'rb') as picklefile:
    artist_average = pickle.load(picklefile)

with open ('artist_info.pk1', 'rb') as picklefile:
    artist_info = pickle.load(picklefile)


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


def track_averages(artist):
    averages = defaultdict(int)
    if artist in artist_average:
        return artist_average[artist]
    else:
        count = 0
        danceability = 0
        energy = 0
        key = 0
        loudness = 0
        speechiness = 0
        acousticness = 0
        instrumentalness = 0
        liveness = 0
        valence = 0
        tempo = 0
        try:
            artist_id = spotify.search(q='artist:' + artist, type='artist')['artists']['items'][0]['uri']
            top_tracks = spotify.artist_top_tracks(artist_id)
            track_features = []
            for i in range(0, len(top_tracks['tracks'])):
                song_id = str(top_tracks['tracks'][i]['uri'])
                features = spotify.audio_features(song_id)
                track_features.append(features)
            for track in track_features:
                count += 1.0
                danceability += track[0]['danceability']
                energy += track[0]['energy']
                key += track[0]['key']
                loudness += track[0]['loudness']
                speechiness += track[0]['speechiness']
                acousticness += track[0]['acousticness']
                instrumentalness += track[0]['instrumentalness']
                liveness += track[0]['liveness']
                valence += track[0]['valence']
                tempo += track[0]['tempo']
        except TypeError:
            next
        except IndexError:
            next
        if count == 0:
            count = 1
        averages['danceability'] = danceability / count
        averages['energy'] = energy / count
        averages['key'] = key / count
        averages['loudness'] = loudness / count
        averages['speechiness'] = speechiness / count
        averages['acousticness'] = acousticness / count
        averages['instrumentalness'] = instrumentalness / count
        averages['liveness'] = liveness / count
        averages['valence'] = valence / count
        averages['tempo'] = tempo / count
        try:
            averages['genres'] = spotify.search(q='artist:' + artist, type='artist')['artists']['items'][0]['genres']
        except IndexError:
            averages['genres'] = []
        return averages



def artist_genre_replace(g_list):
    genre_string = ''
    if g_list:
        for i in range(0, len(g_list)):
            g_list[i] = replace_genre(g_list[i])
        new_genres = list(set(g_list))
        genre_string = ",".join(new_genres)
    return genre_string


def get_image(x):
    try:
        return artist_info[x]['images'][0]['url']
    except IndexError:
        return 'http://www2.pictures.zimbio.com/mp/RyOQVmpiyZB+O937YJarJVm+594x400.jpg'
    except KeyError:
        return 'http://www2.pictures.zimbio.com/mp/RyOQVmpiyZB+O937YJarJVm+594x400.jpg'


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
    print data
    user_artists = data['bands']
    for i in range(0, len(user_artists)):
        user_artists[i] = user_artists[i].strip()
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


@app.route("/findbands", methods=["POST"])
def findbands():
    data = flask.request.json
    user_artists = data['bands']
    for i in range(0, len(user_artists)):
        user_artists[i] = user_artists[i].strip()
    fest = data['fest']
    user_artist_average = defaultdict(dict)
    for i, artist in enumerate(user_artists):
        user_artist_average['user' + str(i)] = track_averages(artist)
    user_df = pd.DataFrame(user_artist_average).T
    artists = pd.DataFrame(artist_average).T
    artists = artists.append(user_df)
    artists['genres'] = artists['genres'].apply(artist_genre_replace)
    df_genre = artists['genres'].str.get_dummies(sep=',')
    artist_recommend = pd.concat([artists, df_genre], axis=1)
    artist_recommend.drop('genres', axis=1, inplace=True)
    artist_recommend.fillna(0)
    user_fest = fest
    lineup = festivals[festivals.id == user_fest]['lineup']
    recommend_df = artist_recommend.loc[list(lineup)[0]]
    recommend_df = recommend_df.fillna(0)
    user_df = artist_recommend.loc[list(user_df.index)]
    user_df = user_df.fillna(0)
    artist_distances = pd.DataFrame(
        list(recommend_df.index), 
        index=list(recommend_df.index), 
        columns=['names']
    )
    for i in range(0, len(user_df)):
        user_case = user_df.ix[i,:]
        distances = pd.DataFrame(
            euclidean_distances(recommend_df, user_case.reshape(1, -1)),
            index = list(recommend_df.index),
            columns=['distance' + str(i)]
        )
        artist_distances = pd.concat([artist_distances, distances], axis=1)
    artist_distances['min'] = artist_distances[list(artist_distances.columns[1:])].min(axis=1)
    artist_distances = artist_distances.sort_values("min")
    df = artist_distances[['names', 'min']]
    df['pic'] = df['names'].apply(get_image)
    results_dict = df.to_dict(orient='index')
    results = []
    for key, value in results_dict.items():
        results.append(value)
    return flask.jsonify(results)



if __name__ == '__main__':
   app.run(debug=True)