import argparse
import json
import sys
import spotipy
import spotipy.util as util

CLIENT_ID = None
CLIENT_SECRET = None
REDIRECT_URI = None

DEFAULT_SCOPE = 'playlist-read-private user-library-read'
DEFAULT_TRACKS_LIMIT = 20


# Requires a session 'sp' and username
def generate_music_library_tracks(sp, username):
    saved_tracks_result = sp.current_user_saved_tracks(DEFAULT_TRACKS_LIMIT)

    while saved_tracks_result['items']:
        saved_tracks = saved_tracks_result['items']
        for track in saved_tracks:
            yield track

        saved_tracks_result = sp.next(saved_tracks_result)
        if not saved_tracks_result:
            break


def generate_playlist_tracks(sp, username, playlist_id):
    playlist_tracks_result = sp.user_playlist_tracks(
        username, playlist_id, limit=DEFAULT_TRACKS_LIMIT)

    while playlist_tracks_result['items']:
        playlist_tracks = playlist_tracks_result['items']
        for track in playlist_tracks:
            yield track

        playlist_tracks_result = sp.next(playlist_tracks_result)
        if not playlist_tracks_result:
            break


def get_user_token(username):
    return spotipy.util.prompt_for_user_token(
        username, DEFAULT_SCOPE, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)


def get_playlist_id(sp, username, playlist_name):
    playlists = sp.user_playlists(username)
    for playlist in playlists['items']:
        if playlist['owner']['id'] != username:
            continue
        if playlist['name'] != playlist_name:
            continue

        return playlist['id']
    return None


def init_session(username):
    token = get_user_token(username)

    if not token:
        print "Can't get token for", username
        return None

    return spotipy.Spotify(auth=token)


def make_track_summary(track_result):
    track = track_result['track']
    summary = {
        'album': track['album']['name'],
        'album_type': track['album']['type'],
        'name': track['name'],
        'artists': [artist['name'] for artist in track['artists']]
    }

    # Maybe these ID's will be useful someday
    if 'isrc' in track['external_ids']:
        summary['isrc'] = track['external_ids']['isrc']

    return summary


def serialize_track(track):
    return json.dumps(track)

# Run as main
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('output_file')
    parser.add_argument('--use_music_library', action='store_true')
    parser.add_argument('--playlist')

    args = parser.parse_args()

    sp = init_session(args.username)

    if args.use_music_library:
        tracks_source = generate_music_library_tracks(sp, args.username)
    elif args.playlist:
        playlist_id = get_playlist_id(sp, args.username, args.playlist)
        if not playlist_id:
            print 'Cannot find playlist: %s' % args.playlist
            sys.exit()

        tracks_source = generate_playlist_tracks(
            sp, args.username, playlist_id)
    else:
        print 'Must specify playlist or --use_music_library'
        sys.exit()

    output_file = open(args.output_file, 'w')
    for track in tracks_source:
        track_summary = make_track_summary(track)
        output_file.write(serialize_track(track_summary) + '\n')