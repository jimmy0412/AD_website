from flask import Flask, request, make_response, redirect, session, render_template, send_file, flash 
from flask_sqlalchemy import SQLAlchemy
import os
import json
app = Flask(__name__)
app.secret_key = os.urandom(32)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///user.db"
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    username = db.Column(db.String(30),unique=True,nullable=False)
    password = db.Column(db.String(30),nullable=False)

    
    def __init__(self,username,password):
        self.username = username
        self.password = password


@app.route('/')
def hello():
	return render_template('index.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/create_user')
def create_user():
	return render_template('create_user.html')

@app.route('/user')
def user():
	return render_template('user.html')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000)