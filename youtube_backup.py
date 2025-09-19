#!/usr/bin/env python3
import argparse
import datetime
import json
import math
import os
import pickle
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

expanduser = os.path.expanduser

class colours:
	green = "\x1b[38;2;0;255;0m"
	pink = "\x1b[38;2;255;0;255m"
	red = "\x1b[38;2;255;0;0m"
	end = "\x1b[0m"

def verbose(message):
	if args.verbose:
		print(message)

sanatize = lambda item : item.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")

def authenticate(credentials_path: str):
	creds = None
	# `token.pickle` stores the user"s access and refresh tokens
	if os.path.exists(os.path.join(credentials_path, "token.pickle")):
		with open(os.path.join(credentials_path, "token.pickle"), "rb") as token:
			creds = pickle.load(token)

	if not creds or not creds.valid: # If there are no (valid) credentials available, let the user log in
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
				os.path.join(credentials_path, "credentials.json"),
				("https://www.googleapis.com/auth/youtube.readonly")
			)
			creds = flow.run_local_server(port = 0)

		with open(os.path.join(credentials_path, "token.pickle"), "wb") as token: # Save the credentials for the next run
			pickle.dump(creds, token)
	return creds

def get_playlists() -> (str("title"),  str("id")):
	page_token = None
	playlists = []
	params = {
		"part": "snippet",
		"mine": "true",
		"maxResults": 50,
		"key": token,
	}

	while True:
		r = session.get(
			"https://youtube.googleapis.com/youtube/v3/playlists",
			params = params
		)
		j = r.json()

		playlists += j["items"]

		if "nextPageToken" not in j.keys():
			break

		params["pageToken"] = j["nextPageToken"]

	playlists = [[playlist["snippet"]["title"], playlist["id"]] for playlist in playlists]
	playlists += [["Watch Later", "WL"]] + [["Sounds from Shorts", "SS"]] + [["Liked videos", "LL"]]

	return playlists

def get_playlist(playlist: str):
	page_token = None
	playlists = []
	params = {
		"part": "snippet",
		"maxResults": 50,
		"playlistId": playlist,
	}
	count = 0
	total = 0

	while True:
		verbose(f"{colours.pink}[~] Downloading: `{playlist}` ({count}/{math.ceil(total / 50)}){colours.end}")

		r = session.get(
			"https://youtube.googleapis.com/youtube/v3/playlistItems",
			params = params,
		)

		for v in (j := r.json())["items"]:
			playlists.append(p := {
				"title": v["snippet"]["title"],
				"description": v["snippet"]["description"],
				"date": v["snippet"]["publishedAt"],
				"id": v["snippet"]["resourceId"]["videoId"],
				"channelId": v["snippet"].get("videoOwnerChannelTitle"),
				"channelName": v["snippet"].get("videoOwnerChannelId"),
			})

		total = j["pageInfo"]["totalResults"]
		count += 1

		if args.verbose:
			clear(1)

		if "nextPageToken" not in j.keys():
			break

		params["pageToken"] = j["nextPageToken"]

	return playlists

def first_run(config_path: str):
	config = {"list": []}
	item_list = []
	browser_found = False

	for o in [
		["list_mode", "[First run] Select list mode to use [blacklist / whitelist]: ", "blacklist", "whitelist"],
		["format", "[First run] Select format to use [tsv / json]: ", "tsv", "json"],
		["date_mode", "[First run] Do you want to save each backup in a date labelled directory? [yes / no]: ", "yes", "no"],
		# ["subscriptions", "[First run] Do you want to save subscriptions? [yes / no]: ", "yes", "no"],
	]:
		if (mode := input(o[1])) not in [o[2], o[3]]:
			print(f"{colours.red}[!] Invalid option!{colours.end}")
			exit()

		config[o[0]] = 0 if mode == o[2] else 1

	for index, playlist in enumerate(playlists := get_playlists()):
		print(f"{index}) title: `{playlist[0]}` id: `{playlist[1]}`")

	playlists = [playlist[1] for playlist in playlists]

	while True:
		user_input = input(f"Enter number ID to {'blacklist' if config['list_mode'] == 0 else 'whitelist'} or leave blank to continue: ")

		if user_input == "":
			break

		config["list"].append(playlists[int(user_input)])

	with open(config_path, "w") as fp:
		json.dump(config, fp, indent = "\t")

	return config

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = "Back up youtube playlists")
	parser.add_argument("--config", dest = "config", action = "store", default = "config.json", type = str, help = "Configuration file")
	parser.add_argument("--credentials", dest = "credentials", action = "store", default = "", type = str, help = "Directory where credential files are stored")
	parser.add_argument("--backup", dest = "backup", action = "store", default = "Playlists", type = str, help = "Where to store exported data")
	parser.add_argument("-v", "--verbose", dest = "verbose", action = "store_true", help = "Print extra info")
	args = parser.parse_args()

	creds = authenticate(args.credentials)
	session = requests.Session()
	session.headers.update({"Authorization": f"Bearer {(token := creds.token)}"})

	clear = lambda amount : print("\x1b[1A\x1b[2K" * amount, end = "")

	if os.path.exists(args.config):
		with open(args.config) as fp:
			config = json.load(fp)

		dv = [None, ""]

		for setting in ["list_mode", "date_mode", "format", "list"]: #  "subscriptions"
			if config.get(setting) in dv:
				verbose(f"{colours.pink}[~] Config is empty. prompting user creation.{colours.end}")
				config = first_run(args.config)
				break

	else:
		verbose(f"{colours.pink}[~] Config does not exist. prompting user creation.{colours.end}")
		config = first_run(args.config)

	if config["list_mode"] == 0: # blacklist mode download everything but those in `list`
		playlists = [playlist for playlist in get_playlists() if playlist not in config.get("list")]
	else: # whitelist mode download nothing but those in `list`
		playlists = [playlist for playlist in get_playlists() if playlist in config.get("list")]

	if len(playlists) < 1:
		print(f"{colours.red}[!] No playlists available!. try going through the setup again `rm config.json`{colours.end}")
		exit()

	verbose(f"{colours.pink}[~] Backing up {len(playlists)} playlists and {'excluding' if config.get('list_mode') == 0 else 'including'} {len(config.get("list"))} {'blacklist' if config.get('list_mode') == 0 else 'whitelist'}ed playlists{colours.end}")

	count = 0
	directory = os.path.join(args.backup, datetime.datetime.now().strftime("%d.%m.%Y")) if config.get("date_mode") == 0 else args.backup

	if not os.path.exists(directory):
		verbose(f"{colours.pink}[~] Creating directory: `{directory}` because it does not exist.{colours.end}")
		os.makedirs(directory)

	for title, identifier in playlists:
		path = os.path.join(directory, f"{title}_{identifier}.{'tsv' if (mode := config.get('format')) == 0 else 'json'}")
		verbose(f"{colours.pink}[~] Backing up playlist: `{title}` ID: `{identifier}` to `{path}`{colours.end}")

		with open(path, "w") as fp:
			playlist = get_playlist(identifier)

			if mode == 0: # tsv
				fp.write("\t".join(("title", "description", "date", "id", "channelId", "channelName")) + "\n")

				for video in playlist:
					fp.write("\t".join(sanatize(str(i)) for i in video.values())  + "\n")

			elif mode == 1: # json
				json.dump(playlist, fp, indent = "\t", ensure_ascii = False)

			count += len(playlist)

	verbose(f"{colours.green}[+] Finished backing up {count} videos across {len(playlists)} playlists{colours.end}")
