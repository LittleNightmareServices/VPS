from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=True)
    servers = db.relationship('Server', backref='owner', lazy='dynamic')

    # Relationship to Plan (optional, if you want to easily access user.plan)
    plan = db.relationship('Plan', backref='users', uselist=False, foreign_keys=[plan_id])


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    price_monthly = db.Column(db.Float, nullable=False)
    price_yearly = db.Column(db.Float, nullable=True) # Allow null if not applicable
    ram_gb = db.Column(db.Integer, nullable=False)
    disk_gb = db.Column(db.Integer, nullable=False)
    time_limit_hours = db.Column(db.Integer, nullable=True) # Null for no limit
    details = db.Column(db.Text, nullable=True) # For longer descriptions or feature lists

    servers = db.relationship('Server', backref='plan_details', lazy='dynamic') # This links Servers to a Plan

    def __repr__(self):
        return f'<Plan {self.name}>'

class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    ip_address = db.Column(db.String(45), unique=True, nullable=True) # IPv4 or IPv6
    status = db.Column(db.String(64), default='pending') # e.g., pending, active, stopped, archived
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=False)

    def __repr__(self):
        return f'<Server {self.name}>'
