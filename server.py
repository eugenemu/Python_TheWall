from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
import re
EMAIL_REGEX = re.compile(r'^[a-za-z0-9\.\+_-]+@[a-za-z0-9\._-]+\.[a-za-z]*$')

app = Flask(__name__)
app.secret_key = "secret"
mysql = MySQLConnector("walldb")


@app.route('/')
def index():

	return render_template("index.html")

@app.route('/register', methods=["POST"])
def register():

	count = 0
	if len(request.form['first_name']) < 2 or len(request.form['last_name']) < 2:
		flash("Name must have at least 2 characters")
		count += 1

	if not isinstance(request.form['first_name'], str) or isinstance(request.form['last_name'], str):
		flash("Name must only have letters")
		count += 1

	if not EMAIL_REGEX.match(request.form['email']):
		flash("Invalid Email address")
		count += 1

	if mysql.fetch("SELECT email from users where email = '{}'".format(request.form['email'])):
		flash("Email already in use")
		count += 1

	if len(request.form['password']) < 8:
		flash("Password must be at least 8 characters")
		count += 1

	if request.form['password'] != request.form['confirm']:
		flash("Your password and confirmation should match")

	if count == 0:
		flash("Thanks for submitting your information!")
		query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES ('{}','{}','{}', '{}', NOW(), NOW())".format(request.form['first_name'], request.form['last_name'], request.form['email'], request.form['password'])
		mysql.run_mysql_query(query)

	return render_template('index.html', flash='left')


@app.route('/login', methods=["POST"])
def login():
	email = request.form['email']
	password = request.form['password']
	user_info = mysql.fetch("SELECT * from users where email = '{}'".format(email))

	if user_info:
		if user_info[0]['password'] == password:
			session['name'] = user_info[0]['first_name']
			name = session['name']
			session['user_id'] = user_info[0]['id']
			return redirect("/wall")	
		else: 
			flash("Incorrect Password")
			return render_template('index.html', flash='right')
	else:
		flash("This email is invalid")
		return render_template('index.html', flash='right')


@app.route('/logoff')
def logoff():
	session.clear()
	return redirect('/')


@app.route('/wall')
def homepage():
	messages = mysql.fetch("SELECT messages.id, first_name, message, DATE_FORMAT(messages.created_at, '%b %D %Y %I:%m %p') as timestamp FROM messages JOIN users on messages.user_id = users.id ORDER BY messages.created_at DESC")
	comments = mysql.fetch("SELECT message_id, first_name, comment, DATE_FORMAT(comments.created_at, '%b %D %Y %I:%m %p') as timestamp FROM comments JOIN messages on comments.message_id = messages.id JOIN users on comments.user_id = users.id")
	
	return render_template('wall.html', messages=messages, comments=comments)


@app.route('/message', methods=["POST"])
def message():
	message = str(request.form['message']).replace("'", "\\'")
	query = "INSERT INTO messages (user_id, message, created_at, updated_at) VALUES ('{}', '{}', NOW(), NOW())".format(session['user_id'], message)
	mysql.run_mysql_query(query)

	return redirect('/wall')

@app.route('/comment', methods=["POST"])
def comment():
	comment = str(request.form['comment']).replace("'", "\\'")
	query = "INSERT INTO comments (user_id, message_id, comment, created_at, updated_at) VALUES ('{}', '{}', '{}', NOW(), NOW())".format(session['user_id'], request.form['message_id'], comment)
	mysql.run_mysql_query(query)

	return redirect('/wall')

app.run(debug=True)