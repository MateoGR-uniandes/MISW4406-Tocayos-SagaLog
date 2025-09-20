import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

# db = SQLAlchemy()

# def init_db(app: Flask):
#     database_url = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@localhost:5432/saga_db')
#     app.config['SQLALCHEMY_DATABASE_URI'] = database_url
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#     db.init_app(app)
#     with app.app_context():
#         db.create_all()

db = SQLAlchemy()

def init_db(app: Flask):
    db.init_app(app)

