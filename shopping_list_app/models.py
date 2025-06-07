from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()

# Database Models
class User(UserMixin, db.Model):
    __tablename__ = 'user'  # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)  # Store hashed passwords
    lists = db.relationship('ShoppingList', backref='owner', lazy=True, foreign_keys='ShoppingList.owner_id')
    # Relationship to lists shared with this user is through ListShare
    # items_added relationship can be useful for tracking who added what
    items_added = db.relationship('ListItem', backref='adder', lazy=True, foreign_keys='ListItem.added_by_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ShoppingList(db.Model):
    __tablename__ = 'shopping_list'  # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('ListItem', backref='list', lazy=True, cascade="all, delete-orphan")
    shares = db.relationship('ListShare', backref='list', lazy=True, cascade="all, delete-orphan")


class ListItem(db.Model):
    __tablename__ = 'list_item'  # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('shopping_list.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    is_purchased = db.Column(db.Boolean, default=False, nullable=False)
    added_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)


class ListShare(db.Model):
    __tablename__ = 'list_share'  # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('shopping_list.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Relationship to the shared user
    user = db.relationship('User', backref='shared_lists', lazy=True)
    # Ensures a user can only be shared a list once
    __table_args__ = (db.UniqueConstraint('list_id', 'user_id', name='_list_user_uc'),)
