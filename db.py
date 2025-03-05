from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def db_init(source):
    db.init_app(source)

    with source.app_context():
        db.create_all()