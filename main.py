#!/usr/bin/env python

import configparser, json, ast
from flask import Flask, render_template

import settings

app = Flask(__name__)

def parse_str_list(str_list):
	if not str_list:
		return None
	elif "," not in str_list:
		# only a single item in the list, so literal_eval will give a str
		return (ast.literal_eval(str_list), )
	else:
		return ast.literal_eval(str_list)

config = configparser.ConfigParser()
config.read("data/hearthstone-science.ini")
videos = [
	(name, {
		"url"   : config[name].get("url", "???"),
		"build" : config[name].get("build", "Missing"),
		"logs"  : parse_str_list(config[name].get("logs")),
		"cards" : parse_str_list(config[name].get("cards")),
		"tags"  : parse_str_list(config[name].get("tags")),
	}) for name in config.sections()
]


@app.route("/")
def video_index():
	return render_template("index.html", videos=videos, youtube_api_key=settings.youtube_api_key)


if __name__ == "__main__":
	app.debug = False
	app.run()
