import pandas as pd
import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.client import SpotifyException

# Load the model
recommender = joblib.load('recommender.pkl')
preprocessor = joblib.load('preprocessor.pkl')

# Load the data
data = pd.read_csv('data.csv')
data.set_index('id', inplace=True)

# Define the features to be used for the recommendation
features = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'tempo', 'valence']


client_id = '50beacb0249f4571ab26da522c0fba5b'
client_secret = '9db120d4abec4c1fa0fb3c5ffe53ed92'
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

def get_track_id(track_name, artist_name):
    try:
        results = sp.search(q=f'artist:{artist_name} track:{track_name}')
        print(results)
        return results['tracks']['items'][0]['id']
    except SpotifyException:
        return None
    
def get_track_features(track_id):
    try:
        features = sp.audio_features(track_id)
        return features[0]
    except SpotifyException:
        return None
    
    
def recommend_songs_by_id(song_id, num_recommendations=5):
    song = data.loc[song_id, features].values.reshape(1, -1)
    
    song_transformed = preprocessor.transform(song)
    song_transformed = pd.DataFrame(song_transformed, columns=[f'PC{i+1}' for i in range(song_transformed.shape[1])])
    song_transformed['year'] = data.loc[song_id, 'year']
    
    distances, indices = recommender.kneighbors(song_transformed, n_neighbors=num_recommendations+1)
    recommended_songs = data.iloc[indices[0]].index
    return recommended_songs[1:num_recommendations + 1]


def recommend_songs_by_artist(song_id, num_recommendations=5):
    artist_name = data.loc[song_id, 'artists_name']
    songs_by_artist = data[(data['artists_name'] == artist_name) & (data.index != song_id)].index
    
    cos_sim = []
    for song in songs_by_artist:
        song_features = data.loc[song, features].values.reshape(1, -1)
        song_features_transformed = preprocessor.transform(song_features)
        cos_sim.append(cosine_similarity(song_features_transformed, preprocessor.transform(data.loc[song_id, features].values.reshape(1, -1))))
        
    cos_sim = np.array(cos_sim).reshape(-1)
    indices = np.argsort(cos_sim)[::-1]
    recommended_songs = songs_by_artist[indices]
    return recommended_songs[:num_recommendations]

def recommend_songs(song_id, num_recommendations_by_id=3, num_recommendations_by_artist=2):
    rec_by_id = recommend_songs_by_id(song_id, num_recommendations_by_id)
    rec_by_artist = recommend_songs_by_artist(song_id, num_recommendations_by_artist)
    combined_recs = np.concatenate((rec_by_id, rec_by_artist))
    return data.loc[combined_recs[:num_recommendations_by_artist+num_recommendations_by_id], ['name', 'artists_name', 'year', 'popularity']]


def get_recommendations(track_name, artist_name):
    track_id = get_track_id(track_name, artist_name)
    if track_id is None:
        return None
    if data[data.index == track_id].empty:
        song_features = get_track_features(track_id)
        if song_features is None:
            return None
        
        print(song_features)
        song_features = pd.DataFrame(song_features, index=[track_id])
        song_features['artists_name'] = artist_name
        song_features['name'] = track_name
        
        data = pd.concat([data, song_features])
        song_id = track_id
    else:
        song_id = track_id
        
    recommendations = recommend_songs(song_id)
    return recommendations

def main():
    st.title('Spotify Song Recommender')
    track_name = st.text_input('Enter the name of the track')
    artist_name = st.text_input('Enter the name of the artist')
    if st.button('Get Recommendations'):
        recommendations = get_recommendations(track_name, artist_name)
        if recommendations is None:
            st.write('No recommendations found')
        else:
            st.write(recommendations)
            
if __name__ == '__main__':
    main()
    
        
        
        
    

