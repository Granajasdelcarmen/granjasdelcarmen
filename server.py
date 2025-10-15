"""Python Flask WebApp Auth0 integration example
"""

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
import asyncio
from prisma import Prisma
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, jsonify, request
from flask_cors import CORS

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = env.get("APP_SECRET_KEY")


oauth = OAuth(app)

# Prisma Client (Python)
db = Prisma()


def run_async(coroutine):
    """Run an async coroutine in a synchronous context."""
    return asyncio.run(coroutine)


@app.before_first_request
def connect_prisma():
    # Establish Prisma connection once at startup
    run_async(db.connect())


@app.teardown_appcontext
def disconnect_prisma(exception):
    # Gracefully close Prisma connection when the app context tears down
    try:
        run_async(db.disconnect())
    except Exception:
        pass

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


# Controllers API
@app.route("/")
def home():
    return render_template(
        "home.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


# JSON endpoints for frontend (React)
@app.route("/auth/login-url", methods=["GET"])
def auth_login_url():
    # Build the redirect URL so the FE can redirect the browser
    redirect_uri = url_for("callback", _external=True)
    client = oauth.create_client("auth0")
    uri = client.create_authorization_url(redirect_uri=redirect_uri)[0]
    return jsonify({"loginUrl": uri})


@app.route("/auth/logout-url", methods=["GET"])
def auth_logout_url():
    return jsonify({
        "logoutUrl": (
            "https://"
            + env.get("AUTH0_DOMAIN")
            + "/v2/logout?"
            + urlencode(
                {
                    "returnTo": url_for("home", _external=True),
                    "client_id": env.get("AUTH0_CLIENT_ID"),
                },
                quote_via=quote_plus,
            )
        )
    })


@app.route("/auth/me", methods=["GET"])
def auth_me():
    return jsonify(session.get("user"))

# Prisma demo endpoints
@app.route("/users")
def list_users():
    users = run_async(db.user.find_many())
    # Convert Pydantic models to dicts for JSON serialization
    users_dict = [u.dict() for u in users]
    return app.response_class(
        response=json.dumps(users_dict, default=str),
        mimetype="application/json",
    )


@app.route("/users/seed")
def seed_user():
    new_user = run_async(
        db.user.create(
            data={
                "email": "test@example.com",
                "name": "Test User",
            }
        )
    )
    return app.response_class(
        response=json.dumps(new_user.dict(), default=str),
        mimetype="application/json",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 3000))
