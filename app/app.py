from flask import Flask, request, make_response, redirect, session, render_template, send_file, flash 
app = Flask(__name__)

@app.route('/')
def hello():
	return "Hello World!"

@app.route('/about')
def about():
	return render_template('about.html')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000)