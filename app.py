#!/usr/bin/env python
import ast
import configparser
import os
import subprocess
from flask import Flask, abort, current_app, render_template, request

app = Flask(__name__)
app.config.from_pyfile(os.path.join(os.path.dirname(__file__), "settings.cfg"))


def parse_str_list(str_list):
	if not str_list:
		return None
	elif "," not in str_list:
		# only a single item in the list, so literal_eval will give a str
		return (ast.literal_eval(str_list), )
	else:
		return ast.literal_eval(str_list)


def get_videos():
	config = configparser.ConfigParser()
	config.read("data/hearthstone-science.ini")
	return [
		(name, {
			"url": config[name].get("url", "???"),
			"logs": config[name].get("logs", "").split(" "),
			"tags": config[name].get("tags", "").split(","),
			"build": config[name].get("build", "Missing"),
			"cards": parse_str_list(config[name].get("cards")),
			"issues": config[name].get("issues", "").split(" "),
		}) for name in config.sections()
	]


def validate_github_signature(data, signature):
	import hmac
	from hashlib import sha1
	if not signature.startswith("sha1="):
		return False
	signature = signature.split("=")[1]
	secret = current_app.config["GITHUB_HOOKS_SECRET"].encode("utf-8")
	digest = hmac.new(secret, data, digestmod=sha1).hexdigest()
	return digest == signature


@app.route("/")
def video_index():
	context = {
		"videos": get_videos(),
		"api_key": current_app.config["YOUTUBE_API_KEY"],
	}
	return render_template("index.html", **context)


def _call(args):
	proc = subprocess.Popen(
		args,
		stdin=subprocess.PIPE,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
	)
	stdout, stderr = proc.communicate()
	return "Command: %r\nSTDOUT:\n%s\nSTDERR:\n%s\n" % (args, stdout, stderr)


@app.route("/github-hooks/", methods=["POST"])
def on_hook_trigger():
	signature = request.headers.get("X-Hub-Signature", "")
	import q; q("validating signature", request.data, signature)
	if validate_github_signature(request.data, signature):
		data = request.get_json()
		repo = app.config["GITHUB_HOOKS_GIT_REPO"] % data["repository"]
		ret = _call(["git", "--git-dir=%s" % (repo), "fetch", data["repository"]["clone_url"]])
		ret += _call(["git", "--git-dir=%s" % (repo), "reset", "--hard", "FETCH_HEAD"])
		return ret
	abort(401)


if __name__ == "__main__":
	app.debug = True
	app.run(host="0.0.0.0", port=7070)
