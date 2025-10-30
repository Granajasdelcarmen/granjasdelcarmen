"""Python Flask WebApp Auth0 integration example with SQLAlchemy
"""

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from datetime import datetime 

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, jsonify, request
from flask_restx import Resource, fields
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Rabbit
from api_docs import api_bp, api, auth_ns, users_ns, rabbits_ns, inventory_ns

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = env.get("APP_SECRET_KEY")

# Register API documentation blueprint
app.register_blueprint(api_bp)

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


# JSON endpoints for frontend (React) - Now with API documentation
@auth_ns.route("/login-url")
class AuthLoginUrl(Resource):
    @auth_ns.doc('get_login_url')
    @auth_ns.marshal_with(api.model('LoginUrl', {
        'loginUrl': fields.String(description='Auth0 login URL')
    }))
    def get(self):
        """Get Auth0 login URL for frontend redirection"""
        # Build the redirect URL so the FE can redirect the browser
        redirect_uri = url_for("callback", _external=True)
        client = oauth.create_client("auth0")
        uri = client.create_authorization_url(redirect_uri=redirect_uri)[0]
        return {"loginUrl": uri}


@auth_ns.route("/logout-url")
class AuthLogoutUrl(Resource):
    @auth_ns.doc('get_logout_url')
    @auth_ns.marshal_with(api.model('LogoutUrl', {
        'logoutUrl': fields.String(description='Auth0 logout URL')
    }))
    def get(self):
        """Get Auth0 logout URL for frontend redirection"""
        return {
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
        }


@auth_ns.route("/me")
class AuthMe(Resource):
    @auth_ns.doc('get_current_user')
    @auth_ns.marshal_with(api.model('AuthUser', {
        'sub': fields.String(description='User ID from Auth0'),
        'email': fields.String(description='User email'),
        'name': fields.String(description='User full name'),
        'picture': fields.String(description='User profile picture URL'),
        'email_verified': fields.Boolean(description='Email verification status')
    }))
    def get(self):
        """Get current authenticated user information"""
        return session.get("user")


# Database endpoints with SQLAlchemy - Now with API documentation
@users_ns.route("/")
class UserList(Resource):
    @users_ns.doc('list_users')
    @users_ns.marshal_list_with(api.model('User', {
        'id': fields.String(description='Unique user identifier'),
        'email': fields.String(description='User email address'),
        'name': fields.String(description='User full name'),
        'phone': fields.String(description='User phone number'),
        'address': fields.String(description='User address'),
        'role': fields.String(description='User role'),
        'is_active': fields.Boolean(description='User active status'),
        'created_at': fields.DateTime(description='User creation timestamp'),
        'updated_at': fields.DateTime(description='User last update timestamp')
    }))
    def get(self):
        """Get list of all users"""
        print("list_users")
        db = SessionLocal()
        try:
            users = db.query(User).all()
            users_dict = []
            for user in users:
                users_dict.append({
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "phone": user.phone,
                    "address": user.address,
                    "role": user.role.value if user.role else None,
                    "is_active": user.is_active,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at
                })
            return users_dict
        finally:
            db.close()


@users_ns.route("/seed")
class UserSeed(Resource):
    @users_ns.doc('seed_user')
    @users_ns.marshal_with(api.model('User', {
        'id': fields.String(description='Unique user identifier'),
        'email': fields.String(description='User email address'),
        'name': fields.String(description='User full name'),
        'phone': fields.String(description='User phone number'),
        'address': fields.String(description='User address'),
        'role': fields.String(description='User role'),
        'is_active': fields.Boolean(description='User active status'),
        'created_at': fields.DateTime(description='User creation timestamp'),
        'updated_at': fields.DateTime(description='User last update timestamp')
    }))
    def get(self):
        """Create a test user for development purposes"""
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
            
            return {
                "id": new_user.id,
                "email": new_user.email,
                "name": new_user.name,
                "phone": new_user.phone,
                "address": new_user.address,
                "role": new_user.role.value if new_user.role else None,
                "is_active": new_user.is_active,
                "created_at": new_user.created_at,
                "updated_at": new_user.updated_at
            }
        except Exception as e:
            db.rollback()
            return {"error": str(e)}, 500
        finally:
            db.close()

@rabbits_ns.route("/")
class RabbitList(Resource):
    @rabbits_ns.doc('list_rabbits')
    @rabbits_ns.marshal_list_with(api.model('Rabbit', {
        'id': fields.String(description='Unique rabbit identifier'),
        'name': fields.String(description='Rabbit name'),
        'image': fields.String(description='Rabbit image URL'),
        'birth_date': fields.DateTime(description='Rabbit birth date'),
        'gender': fields.String(description='Rabbit gender'),
        'discarded': fields.Boolean(description='Whether rabbit is discarded'),
        'discarded_reason': fields.String(description='Reason for discarding'),
        'created_at': fields.DateTime(description='Rabbit creation timestamp'),
        'updated_at': fields.DateTime(description='Rabbit last update timestamp')
    }))
    def get(self):
        """Get list of all rabbits"""
        db = SessionLocal()
        try:
            rabbits = db.query(Rabbit).all()
            rabbits_dict = []
            for rabbit in rabbits:
                rabbits_dict.append({
                    "id": rabbit.id,
                    "name": rabbit.name,
                    "image": rabbit.image,
                    "birth_date": rabbit.birth_date,
                    "gender": rabbit.gender.value if rabbit.gender else None,
                    "discarded": rabbit.discarded,
                    "discarded_reason": rabbit.discarded_reason,
                    "created_at": rabbit.created_at,
                    "updated_at": rabbit.updated_at
                })
            return rabbits_dict
        finally:
            db.close()

@rabbits_ns.route("/add")
class RabbitAdd(Resource):
    @rabbits_ns.doc('add_rabbit')
    @rabbits_ns.expect(api.model('RabbitCreate', {
        'name': fields.String(required=True, description='Rabbit name'),
        'image': fields.String(description='Rabbit image URL'),
        'birth_date': fields.String(description='Rabbit birth date (YYYY-MM-DD format)'),
        'gender': fields.String(enum=['MALE', 'FEMALE'], description='Rabbit gender'),
        'user_id': fields.String(description='Owner user ID')
    }))
    @rabbits_ns.marshal_with(api.model('Rabbit', {
        'id': fields.String(description='Unique rabbit identifier'),
        'name': fields.String(description='Rabbit name'),
        'image': fields.String(description='Rabbit image URL'),
        'birth_date': fields.DateTime(description='Rabbit birth date'),
        'gender': fields.String(description='Rabbit gender'),
        'discarded': fields.Boolean(description='Whether rabbit is discarded'),
        'discarded_reason': fields.String(description='Reason for discarding'),
        'created_at': fields.DateTime(description='Rabbit creation timestamp'),
        'updated_at': fields.DateTime(description='Rabbit last update timestamp')
    }), code=201)
    @rabbits_ns.marshal_with(api.model('Error', {
        'error': fields.String(description='Error message')
    }), code=400)
    @rabbits_ns.marshal_with(api.model('Error', {
        'error': fields.String(description='Error message')
    }), code=500)
    def post(self):
        """Add a new rabbit"""
        db = SessionLocal()
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data:
                return {"error": "No data provided"}, 400
            
            if not data.get("name"):
                return {"error": "Name is required"}, 400
            
            # Validate gender if provided
            if data.get("gender") and data["gender"] not in ["MALE", "FEMALE"]:
                return {"error": "Gender must be MALE or FEMALE"}, 400
            
            import uuid
            
            # Parse birth_date if provided
            birth_date = None
            if data.get("birth_date"):
                try:
                    birth_date = datetime.strptime(data["birth_date"], "%Y-%m-%d")
                except ValueError:
                    return {"error": "Invalid birth_date format. Use YYYY-MM-DD"}, 400
            
            new_rabbit = Rabbit(
                id=str(uuid.uuid4()),
                name=data["name"],
                image=data.get("image"),
                birth_date=birth_date,
                gender=data.get("gender"),
                user_id=data.get("user_id")
            )
            
            db.add(new_rabbit)
            db.commit()
            db.refresh(new_rabbit)
            
            return {
                "id": new_rabbit.id,
                "name": new_rabbit.name,
                "image": new_rabbit.image,
                "birth_date": new_rabbit.birth_date,
                "gender": new_rabbit.gender.value if new_rabbit.gender else None,
                "discarded": new_rabbit.discarded,
                "discarded_reason": new_rabbit.discarded_reason,
                "created_at": new_rabbit.created_at,
                "updated_at": new_rabbit.updated_at
            }, 201
            
        except Exception as e:
            db.rollback()
            return {"error": str(e)}, 500
        finally:
            db.close()

@rabbits_ns.route("/<string:id>")
class RabbitDetail(Resource):
    @rabbits_ns.doc('update_rabbit')
    @rabbits_ns.expect(api.model('RabbitUpdate', {
        'name': fields.String(description='Rabbit name'),
        'image': fields.String(description='Rabbit image URL'),
        'birth_date': fields.String(description='Rabbit birth date (YYYY-MM-DD format)'),
        'gender': fields.String(enum=['MALE', 'FEMALE'], description='Rabbit gender'),
        'user_id': fields.String(description='Owner user ID')
    }))
    @rabbits_ns.marshal_with(api.model('Rabbit', {
        'id': fields.String(description='Unique rabbit identifier'),
        'name': fields.String(description='Rabbit name'),
        'image': fields.String(description='Rabbit image URL'),
        'birth_date': fields.DateTime(description='Rabbit birth date'),
        'gender': fields.String(description='Rabbit gender'),
        'discarded': fields.Boolean(description='Whether rabbit is discarded'),
        'discarded_reason': fields.String(description='Reason for discarding'),
        'created_at': fields.DateTime(description='Rabbit creation timestamp'),
        'updated_at': fields.DateTime(description='Rabbit last update timestamp')
    }))
    @rabbits_ns.marshal_with(api.model('Error', {
        'error': fields.String(description='Error message')
    }), code=400)
    @rabbits_ns.marshal_with(api.model('Error', {
        'error': fields.String(description='Error message')
    }), code=404)
    @rabbits_ns.marshal_with(api.model('Error', {
        'error': fields.String(description='Error message')
    }), code=500)
    def put(self, id):
        """Update a rabbit by ID"""
        db = SessionLocal()
        try:
            data = request.get_json()
            rabbit = db.query(Rabbit).filter(Rabbit.id == id).first()
            
            if not rabbit:
                return {"error": "Rabbit not found"}, 404
            
            # Update fields if provided
            if "name" in data:
                rabbit.name = data["name"]
            if "image" in data:
                rabbit.image = data["image"]
            if "birth_date" in data:
                if data["birth_date"]:
                    try:
                        rabbit.birth_date = datetime.strptime(data["birth_date"], "%Y-%m-%d")
                    except ValueError:
                        return {"error": "Invalid birth_date format. Use YYYY-MM-DD"}, 400
                else:
                    rabbit.birth_date = None
            if "gender" in data:
                if data["gender"] and data["gender"] not in ["MALE", "FEMALE"]:
                    return {"error": "Gender must be MALE or FEMALE"}, 400
                rabbit.gender = data["gender"]
            if "user_id" in data:
                rabbit.user_id = data["user_id"]
            
            rabbit.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(rabbit)
            
            return {
                "id": rabbit.id,
                "name": rabbit.name,
                "image": rabbit.image,
                "birth_date": rabbit.birth_date,
                "gender": rabbit.gender.value if rabbit.gender else None,
                "discarded": rabbit.discarded,
                "discarded_reason": rabbit.discarded_reason,
                "created_at": rabbit.created_at,
                "updated_at": rabbit.updated_at
            }
            
        except Exception as e:
            db.rollback()
            return {"error": str(e)}, 500
        finally:
            db.close()

    @rabbits_ns.doc('delete_rabbit')
    @rabbits_ns.marshal_with(api.model('Success', {
        'message': fields.String(description='Success message')
    }))
    @rabbits_ns.marshal_with(api.model('Error', {
        'error': fields.String(description='Error message')
    }), code=404)
    @rabbits_ns.marshal_with(api.model('Error', {
        'error': fields.String(description='Error message')
    }), code=500)
    def delete(self, id):
        """Delete a rabbit by ID"""
        db = SessionLocal()
        try:
            rabbit = db.query(Rabbit).filter(Rabbit.id == id).first()
            
            if not rabbit:
                return {"error": "Rabbit not found"}, 404
            
            db.delete(rabbit)
            db.commit()
            
            return {"message": "Rabbit deleted successfully"}
            
        except Exception as e:
            db.rollback()
            return {"error": str(e)}, 500
        finally:
            db.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 3000))
