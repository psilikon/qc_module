from flask import render_template, request, jsonify, redirect, url_for, session, request, logging, flash
from app import app
import MySQLdb 
import json
from datetime import datetime
from functools import wraps

app.secret_key = app.config['SECRET_KEY']

dbuser = app.config['DBUSER']
dbpasswd = app.config['DBPASSWORD']
dbdb = app.config['DB']
dbhost = app.config['DBHOST']
dbport = int(app.config['DBPORT'])

db = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpasswd, db=dbdb, port=dbport)

#list logged in dev
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Please login', 'danger')
			return redirect(url_for('login'))
	return wrap

#Logout
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))

#Login
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		# Get Form Fields
		username = request.form['username']
		password_candidate = request.form['password']

		# Create cursor
		c = db.cursor()

		# Get user by username
		result = c.execute("SELECT pass, user_level FROM vicidial_users WHERE user = %s AND user_level >= '7' ", [username])

		if result > 0:
			# Get stored hash
			data = c.fetchone()
			password = data[0]

			# Compare Passwords
			if password_candidate == password:
				# Passed
				session['logged_in'] = True
				session['username'] = username

				flash('You are now logged in', 'success')
				return redirect(url_for('index'))
			else:
				error = 'Invalid login'
				return render_template('login.html', error=error)
			# Close connection
			c.close()
		else:
			error = 'Username not found'
			return render_template('login.html', error=error)

	return render_template('login.html')

@app.route('/')
@app.route('/index')
@is_logged_in
def index():
    return render_template('main_form.html', username=session['username'])

@app.route('/lookup', methods=['POST'])
@is_logged_in
def lookup():
	now = datetime.now()
	dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
	print(dt_string)

	recording_id =  request.form.get('recording_id')
	
	json_cont = []
	
	c = db.cursor()
	
	sql = "SELECT vicidial_id, user, lead_id, location, start_time FROM recording_log WHERE recording_id = '"+recording_id+"' "
	c.execute(sql)
	rec_res = c.fetchone()
	location_parts = rec_res[3].split("/")
	lead_id = str(rec_res[2])
	sql = "SELECT alt_server_ip FROM servers WHERE server_ip = '"+location_parts[2]+"' "
	c.execute(sql)
	serv_res = c.fetchone()
	alt_server_ip = str(serv_res[0])

	location_parts[2] = alt_server_ip
	alt_location = "/".join(location_parts)

	sql = "SELECT first_name, last_name, phone_number FROM vicidial_list WHERE lead_id = '"+lead_id+"' "
	c.execute(sql)
	lead_res = c.fetchone()

	fields = {'vicidial_id': rec_res[0], 'user': rec_res[1], 'lead_id': lead_id, 'location': alt_location, 'start_time': str(rec_res[4]), 'first_name': lead_res[0], 'last_name': lead_res[1], 'phone_number': lead_res[2], 'eval_time': dt_string}
	
	#return render_template('main_form.html')"""
	json_cont.append(fields)
	return jsonify(json_cont)
