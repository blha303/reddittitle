from flask import *
import praw,prawcore

app = Flask(__name__)
app.config.from_pyfile("settings.cfg")
reddit = praw.Reddit(site_name="reddittitle")

@app.route("/")
def index():
    if not "code" in session:
        return redirect("/login")
    try:
        r = praw.Reddit(user_agent="Praw user instance", site_name="reddittitle")
        r.auth.authorize(session["code"])
        return ", ".join(sr.display_name for sr in r.user.moderator_subreddits())
    except prawcore.exceptions.OAuthException:
        return redirect("/login")

@app.route("/login")
def login():
    return redirect(reddit.auth.url(["identity", "modconfig", "mysubreddits"], "state", "temporary", False))

@app.route("/postlogin")
def postlogin():
    session["code"] = request.args.get("code")
    return redirect("/")

def main():
    app.run(port=5000, debug=True, host="0.0.0.0")

if __name__ == "__main__":
    main()
