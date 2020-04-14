
import requests
import json
import os

import googleapiclient.discovery
import googleapiclient.errors
import google_auth_oauthlib.flow
import youtube_dl
from exceptions import ResponseException



spotify_user_id="rjvgdm0w2ku1x7revq2ku7gvl"
spotify_token="BQAO28ioGSHxooLBh5OCA5UcwYaP-vqrDW5aic8QwdKp09DXm9rodW5zywVj_u8QzJ2ZLx0OePo7RHFHdkHXxL6X4oHMZycaeEA7qE8HtHY_4nfeErJAd_p"


class Automation1:
    def __init__(self):
        self.youtube_client = self.getYoutubeClient()
        self.all_song_info = {}

     
    

    def getYoutubeClient(self):
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secrets.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client



    def getLikedVids(self):
        request = self.youtube_client.videos().list(
        part="snippet,contentDetails,statistics",
        myRating="like")
        response = request.execute()

        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(
                item["id"])

            # use youtube_dl to collect the song name & artist name
            video = youtube_dl.YoutubeDL({}).extract_info(
                youtube_url, download=False)
            song_name = video["track"]
            artist = video["artist"]

            if song_name is not None and artist is not None:
                # save all important info and skip any missing song and artist
                self.all_song_info[video_title] = {
                    "youtube_url": youtube_url,
                    "song_name": song_name,
                    "artist": artist,

                    # add the uri, easy to get song to put into playlist
                    "spotify_uri": self.get_spotify_uri(song_name, artist)

                }

           

    def createPlaylist(self):
        requsts_body=json.dumps({
        "name": "Liked Youtube Songs ",
        "description": "All the liked songs from youtube",
        "public": False
        })
        query=	"https://api.spotify.com/v1/users/{}/playlists".format(spotify_user_id)
        response=json.dumps({
            requests.post(query,data=requsts_body,header={"Content-Type":"appication/json",
            "Authorization":"Bearer{}".format(spotify_token)})
        })
        playlistID=response["id"]
        return playlistID



    def getSportifyURI(self,song_name, artist):
        """Search For the Song"""
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()
        songs = response_json["tracks"]["items"]

        # only use the first song
        uri = songs[0]["uri"]

        return uri


    def addSongToPlaylist(self):
        """Add all liked songs into a new Spotify playlist"""
        # populate dictionary with our liked songs
        self.get_liked_videos()

        # collect all of uri
        uris = [info["spotify_uri"]
                for song, info in self.all_song_info.items()]

        # create a new playlist
        playlist_id = self.create_playlist()

        # add all songs into new playlist
        request_data = json.dumps(uris)

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(
            playlist_id)

        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )

        # check for valid response status
        if response.status_code != 200:
            raise ResponseException(response.status_code)

        response_json = response.json()
        return response_json

