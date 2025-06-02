from flask import Flask
from config import Config
from .models import db
from flask_login import LoginManager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login' # Assuming you will have a login route in main blueprint

    @login_manager.user_loader
    def load_user(user_id):
        # Since the user_id is just the primary key of our user table, use it in the query for the user
        from .models import User
        return User.query.get(int(user_id))

    # Further initialization (database, blueprints) will go here later

    from app.routes import bp as main_bp # Import routes
    app.register_blueprint(main_bp)

    return app
