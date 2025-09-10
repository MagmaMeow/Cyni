import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from requests_oauthlib import OAuth2Session
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------
# Flask App Setup
# ---------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("TOKEN", "dev_fallback_token")

# ---------------------------------------------------------
# MongoDB + Session Config
# ---------------------------------------------------------
mongo_uri = os.getenv("MONGODB_URI")
if not mongo_uri:
    raise RuntimeError("MONGODB_URI environment variable not set!")

client = MongoClient(mongo_uri)

app.config["SESSION_TYPE"] = "mongodb"
app.config["SESSION_MONGODB"] = client
app.config["SESSION_MONGODB_DB"] = os.getenv("SESSION_MONGODB_DB", "cyni_sessions")
app.config["SESSION_MONGODB_COLLECT"] = os.getenv("SESSION_MONGODB_COLLECT", "sessions")
Session(app)

# ---------------------------------------------------------
# Flask-Login Setup
# ---------------------------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Discord OAuth2 Config
# ---------------------------------------------------------
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")  # Render URL + /callback
OAUTH_SCOPE = ["identify", "guilds"]
DISCORD_API_BASE_URL = "https://discord.com/api"

# ---------------------------------------------------------
# User Class
# ---------------------------------------------------------
class User(UserMixin):
    def __init__(self, id, username, discriminator, avatar):
        self.id = id
        self.username = username
        self.discriminator = discriminator
        self.avatar = avatar

@login_manager.user_loader
def load_user(user_id):
    if "user" in session:
        u = session["user"]
        if u["id"] == int(user_id):
            return User(u["id"], u["username"], u["discriminator"], u.get("avatar"))
    return None

def make_discord_session(state=None, token=None):
    return OAuth2Session(
        CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=OAUTH_SCOPE,
        state=state,
        token=token
    )

# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/login")
def login():
    discord = make_discord_session()
    auth_url, state = discord.authorization_url(f"{DISCORD_API_BASE_URL}/oauth2/authorize")
    session['oauth2_state'] = state
    return redirect(auth_url)

@app.route("/callback")
def callback():
    discord = make_discord_session(state=session.get('oauth2_state'))
    token = discord.fetch_token(
        f"{DISCORD_API_BASE_URL}/oauth2/token",
        client_secret=CLIENT_SECRET,
        authorization_response=request.url
    )
    session['oauth2_token'] = token

    discord = make_discord_session(token=token)
    user_data = discord.get(f"{DISCORD_API_BASE_URL}/users/@me").json()

    user = User(
        id=int(user_data["id"]),
        username=user_data["username"],
        discriminator=user_data["discriminator"],
        avatar=user_data.get("avatar")
    )
    login_user(user)
    session["user"] = user_data
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("index"))

# ---------------------------------------------------------
# Run Flask App
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
