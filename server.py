"""Python Flask WebApp Auth0 integration example with SQLAlchemy
"""

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from datetime import datetime

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Product, Order, OrderItem

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = env.get("APP_SECRET_KEY")

# Database setup
DATABASE_URL = env.get("DATABASE_URL", "sqlite:///./dev.db")
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth = OAuth(app)

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


# Database endpoints with SQLAlchemy
@app.route("/users")
def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        users_dict = []
        for user in users:
            users_dict.append({
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "createdAt": user.created_at.isoformat() if user.created_at else None,
                "updatedAt": user.updated_at.isoformat() if user.updated_at else None
            })
        return jsonify(users_dict)
    finally:
        db.close()


@app.route("/users/seed")
def seed_user():
    db = SessionLocal()
    try:
        import uuid
        new_user = User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            name="Test User"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return jsonify({
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "createdAt": new_user.created_at.isoformat() if new_user.created_at else None
        })
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# Product endpoints
@app.route("/products")
def list_products():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        products_dict = []
        for product in products:
            products_dict.append({
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock": product.stock,
                "category": product.category,
                "image_url": product.image_url,
                "is_active": product.is_active,
                "created_at": product.created_at.isoformat() if product.created_at else None
            })
        return jsonify(products_dict)
    finally:
        db.close()


@app.route("/products/seed")
def seed_product():
    db = SessionLocal()
    try:
        import uuid
        new_product = Product(
            id=str(uuid.uuid4()),
            name="Huevos Frescos",
            description="Huevos frescos de gallinas criadas en libertad",
            price=15.50,
            stock=100,
            category="Huevos",
            is_active=True
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        
        return jsonify({
            "id": new_product.id,
            "name": new_product.name,
            "description": new_product.description,
            "price": new_product.price,
            "stock": new_product.stock,
            "category": new_product.category,
            "created_at": new_product.created_at.isoformat() if new_product.created_at else None
        })
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 3000))
