from flask import *
import praw,prawcore
import cssutils

app = Flask(__name__)
app.config.from_pyfile("settings.cfg")

def get_rules(css):
    out = {}
    for rule in css:
        if "div.thing.id-t3_" in rule.selectorText:
            id = rule.selectorText.split(".id-t3_")[1][:6]
            if not id in out:
                out[id] = {}
            if ":before" in rule.selectorText:
                out[id]["before"] = rule
            else:
                out[id]["element"] = rule
    return out

def update_rules(css, id, title):
    rules = get_rules(css)
    if not id in rules:
        css.add("div.thing.id-t3_{} a.title { font-size: 0 !important }".format(id))
        css.add("div.thing.id-t3_{} a.title:before { font-size: medium !important; content: {} }".format(id, title))
    else:
        rules[id]["before"].style.content = title
    return css

@app.before_request
def before():
    print(session)

@app.route("/")
def index():
    try:
        reddit = praw.Reddit(site_name="reddittitle", refresh_token=session.get("refresh"))
    except prawcore.exceptions.OAuthException as e:
        session["return"] = request.full_path
        return redirect("/login")
    return render_template("index.html", user=reddit.user.me(), subreddits=reddit.user.moderator_subreddits())

@app.route("/r/<subreddit>", methods=["GET", "POST"])
def sr_edit(subreddit):
    try:
        reddit = praw.Reddit(site_name="reddittitle", refresh_token=session.get("refresh"))
    except prawcore.exceptions.OAuthException as e:
        session["return"] = request.full_path
        return redirect("/login")
    sr = {sr.display_name:sr for sr in reddit.user.moderator_subreddits()}
    if not subreddit in sr:
        flash("You are not a moderator on /r/{}".format(subreddit))
        return redirect("/")
    css = cssutils.parseString(sr[subreddit].stylesheet().stylesheet)
    rules = get_rules(css)
    if request.method == "GET":
        if not rules:
            flash("There are no rules on this subreddit yet. Create one below.")
        return render_template("subreddit.html", subreddit=subreddit, rules=rules)
    if request.method == "POST":
        if not request.form.get("id"):
            flash("No post ID provided. It's the six-character string after '/comments/' in the URL.")
            return redirect("/r/{}".format(subreddit))
        if not request.form.get("title"):
            flash("No post title provided.")
            return redirect("/r/{}".format(subreddit))
        id = request.form.get("id")
        title = request.form.get("title")
        if len(id) != 6:
            flash("Invalid post ID provided (must be six characters)")
            return redirect("/r/{}".format(subreddit))
        if title[0] != '"' and title[-1] != '"':
            title = '"{}"'.format(title.replace('"', '\\"'))
        update_rules(css, id, title)
        return "<pre>" + css.cssText + "</pre>"

@app.route("/r/<subreddit>/<id>", methods=["POST"])
def title_edit(subreddit, id):
    try:
        reddit = praw.Reddit(site_name="reddittitle", refresh_token=session.get("refresh"))
    except prawcore.exceptions.OAuthException as e:
        session["return"] = request.full_path
        return redirect("/login")
    sr = {sr.display_name:sr for sr in reddit.user.moderator_subreddits()}
    if not subreddit in sr:
        flash("You are not a moderator on /r/{}".format(subreddit))
        return redirect("/")
    css = cssutils.parseString(sr[subreddit].stylesheet().stylesheet)
    rules = get_rules(css)
    if request.method == "POST":
        title = request.form.get("title")
        if title[0] != '"' and title[-1] != '"':
            title = '"{}"'.format(title.replace('"', '\\"'))
        update_rules(css, id, title)
        return "<pre>" + css.cssText + "</pre>"

@app.route("/login")
def login():
    reddit = praw.Reddit(site_name="reddittitle")
    scopes = ["identity", "modconfig", "mysubreddits", "read"]
    return redirect(reddit.auth.url(scopes, "state", "permanent", False))

@app.route("/postlogin")
def postlogin():
    reddit = praw.Reddit(site_name="reddittitle")
    session["refresh"] = reddit.auth.authorize(request.args.get("code"))
    if "return" in session:
        return redirect(session["return"])
    return redirect("/")

def main():
    app.run(port=5000, debug=True, host="0.0.0.0")

if __name__ == "__main__":
    main()
