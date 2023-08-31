#!/usr/bin/env python3
#
# Reads an input CSV of [Album,Artist,Year] and monitors it within Lidarr.
#

import csv
import json
import os
import sys
import time
import urllib.request, urllib.parse

# From the Settings | General tab of Lidarr
X_API_KEY=os.environ.get('X_API_KEY')

def lookup_artist(artist):
    headers = { 'X-Api-Key': X_API_KEY }
    url = "http://localhost:8686/lidarr/api/v1/artist/lookup?term={0}".format(urllib.parse.quote(artist))
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        content = response.read()
    text = content.decode("utf-8", "ignore")
    return json.loads(text)

def monitor_artist(artist):
    headers = { 'X-Api-Key': X_API_KEY, 'Content-Type': 'application/json' }
    url = "http://localhost:8686/lidarr/api/v1/artist"
    data = artist
    data_bytes = bytes(json.dumps(data), encoding='utf8')
    handler = urllib.request.HTTPHandler(debuglevel=10)
    opener = urllib.request.build_opener(handler)
    req = urllib.request.Request(url, method='PUT', headers=headers, data=data_bytes)
    with opener.open(req) as response:
        content = response.read()
    text = content.decode("utf-8", "ignore")
    print(text)

def lookup_albums(title):
    headers = { 'X-Api-Key': X_API_KEY }
    url = "http://localhost:8686/lidarr/api/v1/album/lookup?term={0}".format(urllib.parse.quote(title))
    handler = urllib.request.HTTPHandler(debuglevel=0)
    opener = urllib.request.build_opener(handler)
    req = urllib.request.Request(url, headers=headers)
    with opener.open(req) as response:
        content = response.read()
    text = content.decode("utf-8", "ignore")
    return json.loads(text)

def list_albums(artist_id):
    #print(artist_id)
    headers = { 'X-Api-Key': X_API_KEY }
    url = "http://localhost:8686/lidarr/api/v1/album/?artistId={0}".format(urllib.parse.quote(artist_id))
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        content = response.read()
    text = content.decode("utf-8", "ignore")
    return json.loads(text)

def add_album(album_id):
    headers = { 'X-Api-Key': X_API_KEY, 'Content-Type': 'application/json' }
    url = "http://localhost:8686/lidarr/api/v1/album/monitor"
    data = {'albumIds': [ album_id ], 'monitored': True}
    data_bytes = bytes(json.dumps(data), encoding='utf8')
    req = urllib.request.Request(url, method='PUT', headers=headers, data=data_bytes)
    with urllib.request.urlopen(req) as response:
        content = response.read()
    text = content.decode("utf-8", "ignore")
    #print(text)

def monitor_album(album_id):
    headers = { 'X-Api-Key': X_API_KEY, 'Content-Type': 'application/json' }
    url = "http://localhost:8686/lidarr/api/v1/album/monitor"
    data = {'albumIds': [ album_id ], 'monitored': True}
    data_bytes = bytes(json.dumps(data), encoding='utf8')
    req = urllib.request.Request(url, method='PUT', headers=headers, data=data_bytes)
    with urllib.request.urlopen(req) as response:
        content = response.read()
    text = content.decode("utf-8", "ignore")
    #print(text)

def monitor_foreign_album(artist_foreign_id, artist_name, album_foreign_id):
    headers = { 'X-Api-Key': X_API_KEY, 'Content-Type': 'application/json' }
    url = "http://localhost:8686/lidarr/api/v1/artist"
    data = {
        "addOptions": {
            "AlbumsToMonitor": [
                album_foreign_id
            ],
            "monitor": "Existing",
            "searchForMissingAlbums": True,
            "monitored": True
        },
        "albumFolder": True,
        "foreignArtistId": artist_foreign_id,
        "artistName": artist_name,
        "metadataProfileId": 1,
        "monitorNewItems": "none",
        "monitored": True,
        "qualityProfileId": 1,
        "rootFolderPath": "/data/media/music",
    }
    data_bytes = bytes(json.dumps(data), encoding='utf8')
    handler = urllib.request.HTTPHandler(debuglevel=0)
    opener = urllib.request.build_opener(handler)
    req = urllib.request.Request(url, method='POST', headers=headers, data=data_bytes)
    with opener.open(req) as response:
        content = response.read()
    text = content.decode("utf-8", "ignore")
    #print(text)

def read_album_list(filename):
    albums = []
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                #print(f'{", ".join(row)}')
                pass
            else:
                albums.append({
                    'year': row[2], 
                    'artist': row[1],
                    'title': row[0]
                })
            line_count += 1
    #print('Loaded {0} albums.'.format(len(albums)))
    return albums

def album_match(album, artist_albums):
    list_title_cleaned = ''.join(e for e in album['title'].lower() if e.isalnum())
    list_artist_cleaned = ''.join(e for e in album['artist'].lower() if e.isalnum())
    # First check for an equals match on the cleaned title 
    for artist_album in artist_albums:
        if artist_album['albumType'] != 'Album':
            continue
        album_title_cleaned = ''.join(e for e in artist_album['title'].lower() if e.isalnum())
        artist_title_cleaned = ''.join(e for e in artist_album['artist']['artistName'].lower() if e.isalnum()) 
        if list_title_cleaned == album_title_cleaned and list_artist_cleaned == artist_title_cleaned:
            return artist_album
    # Now check for any looser match of one title within the other
    for artist_album in artist_albums:
        if artist_album['albumType'] != 'Album':
            continue
        album_title_cleaned = ''.join(e for e in artist_album['title'].lower() if e.isalnum()) 
        artist_title_cleaned = ''.join(e for e in artist_album['artist']['artistName'].lower() if e.isalnum()) 
        if list_title_cleaned in album_title_cleaned and list_artist_cleaned == artist_title_cleaned:
            return artist_album
        if album_title_cleaned  in list_title_cleaned and list_artist_cleaned == artist_title_cleaned:
            return artist_album
    return None

if __name__ == "__main__":
    albums = read_album_list(sys.argv[1])
    for album in albums:
        artists = lookup_artist(album['artist'])
        if len(artists) == 0:
            print("***************** NO ARTIST MATCH: {0}".format(album['artist']))
            continue
        artist = artists[0]
        #print("ARTIST: {0}".format(artist['artistName']))
        if 'id' in artist:  # Artist already in Lidarr, check for the album
            print("FOUND ARTIST: {0}".format(album))
            artist_albums = list_albums(str(artist['id']))
            matched_album = album_match(album, artist_albums)
            if matched_album:
                if not matched_album['monitored']:
                    print("MONITORING: {0}".format(matched_album['title']))
                    monitor_album(str(matched_album['id']))
            else:
                print("***************** NO ALBUM MATCH: {0}".format(album))
        else: # Artist not in Lidarr, so must add via album search
            print("ADDING ARTIST: {0}".format(album))
            artist_albums = lookup_albums(album['title'])
            matched_album = album_match(album, artist_albums)
            if matched_album:
                if not matched_album['monitored']:
                    print("MONITORING: {0}".format(matched_album['title']))
                    monitor_foreign_album(str(matched_album['artist']['foreignArtistId']), str(matched_album['artist']['artistName']), str(matched_album['foreignAlbumId']))
            else:
                print("***************** NO FOREIGN ALBUM MATCH: {0}".format(album))
        time.sleep(15)
