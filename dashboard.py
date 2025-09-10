import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from flask_login import LoginManager
from pymongo import MongoClient

# ---------------------------------------------------------
# Flask App Setup
# ---------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("TOKEN", "dev_fallback_token")  # Use TOKEN as secret key

# ---------------------------------------------------------
# MongoDB + Session Config
# ---------------------------------------------------------
app.config["SESSION_TYPE"] = "mongodb"

mongo_uri = os.getenv("MONGODB_URI")
if not mongo_uri:
    raise RuntimeError("MONGODB_URI environment variable not set!")

# Explicit MongoDB client from Atlas URI
client = MongoClient(mongo_uri)
app.config["SESSION_MONGODB"] = client
app.config["SESSION_MONGODB_DB"] = os.getenv("SESSION_MONGODB_DB", "cyni_sessions")
app.config["SESSION_MONGODB_COLLECT"] = os.getenv("SESSION_MONGODB_COLLECT", "sessions")

# Initialize Session
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
# Routes
# ---------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Example login logic (replace with real user auth later)
        if username == "admin" and password == "password":
            session["user"] = username
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=session["user"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
