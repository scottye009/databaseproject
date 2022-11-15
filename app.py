from flask import Flask, render_template, request, session, url_for, redirect, flash
import mysql.connector
#from forms import RegistrationForm, LoginForm
import re
from datetime import timedelta, date, time, datetime
import json
import urllib.request
from urllib.error import HTTPError
from random import randint
from dateutil.relativedelta import relativedelta


#Initialize the app from Flask
app = Flask(__name__)


# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'abcdefg'

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)

#Configure MySQL
conn = mysql.connector.connect(host='localhost',
                       user='root',
                       password='',
                       database='air',
					   buffered=True)


#Define a route to hello function
@app.route('/', methods =['POST', 'GET'])
def home():
	cursor = conn.cursor()
	cursor.execute('SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time FROM flight WHERE status = "DELAYED"')
	data1 = cursor.fetchall()
	msg=''
	data = {}

	if request.method == 'POST':
		pre = request.form['city']
		city = ''
		for a in pre:
			if a == ' ':
				city += '+'
			else:
				city += a

	else:
		city = 'shanghai'


	api = '9df3952de1ad2436f5019fc66a587692'

	# source contain json data from api
	try:
		source = urllib.request.urlopen('http://api.openweathermap.org/data/2.5/weather?q=' + city + '&appid=' + api).read()

		list_of_data = json.loads(source)
		icon = {
			"01d": "fas fa-sun",
			"01n": "fas fa-sun",
			"02n": "fas fa-cloud-moon",
			"02d": "fas fa-cloud-sun",
			"03d": "fas fa-cloud-meatball",
			"03n": "fas fa-cloud-meatball",
			"04d": "fas fa-cloud-meatball",
			"04n": "fas fa-cloud-meatball",
			"09d": "fas fa-cloud-showers-heavy",
			"09n": "fas fa-cloud-showers-heavy",
			"10d": "fas fa-cloud-sun-rain",
			"10n": "fas fa-cloud-sun-rain",
			"11d": "fas fa-poo-storm",
			"11n": "fas fa-poo-storm",
			"13d": "fas fa-snowflake",
			"13n": "fas fa-snowflake",
			"50d": "fas fa-smog",
			"50n": "fas fa-smog"
		}

		data = {
			"cityname": str(list_of_data["name"].capitalize()),
			"country_code": str(list_of_data['sys']['country']),
			"coordinate": str(list_of_data['coord']['lon']) + ' ' 
						+ str(list_of_data['coord']['lat']),
			"weather": str(list_of_data['weather'][0]['description'].capitalize()),
			"temp": str(round(list_of_data['main']['temp']-273, 1)) + '°C',
			"wind": str(list_of_data['wind']['speed']),
			"pressure": str(list_of_data['main']['pressure']),
			"humidity": str(list_of_data['main']['humidity'])+'%',
			"icon": str(icon[list_of_data['weather'][0]['icon']])
		}
		#print(data)
	except HTTPError:
		msg="The city you entered is currently not available."

	
	return render_template('index.html', data = data, data1 = data1, msg=msg)
		


@app.route('/search', methods=['GET', 'POST'])
def search():
	cursor = conn.cursor()
	cursor.execute('SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time FROM flight WHERE status = "DELAYED"')
	data1 = cursor.fetchall()
	msg = ''
	flight = ''

	if request.method == 'POST':
		departure = request.form['departure']
		arrival = request.form['arrival']
		date = request.form['date']
		a = datetime.strptime(date, '%Y-%m-%d')

		if departure.isupper() is True and arrival.isupper() is False or departure.isupper() is False and arrival.isupper() is True:
			msg = 'Please fill in the both blanks in Airport Code or City Name!'
		
		elif a < datetime.today():
			msg = 'You can only search for upcoming flights!'

		else:
			if departure.isupper():
				cursor = conn.cursor()
				query = "SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time, arrival_time, price, status FROM flight WHERE departure_airport = \'{}\' AND arrival_airport = \'{}\' AND departure_time LIKE \'{}\'"
				cursor.execute(query.format(departure, arrival, '%'+str(date)+'%'))
				flight = cursor.fetchall()
			
				if not flight:
					msg = "There's no available flight based on the condition you insert."

			else:
				cursor = conn.cursor()
				query = "SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time, arrival_time, price, status \
				FROM airport AS a, flight AS b, airport AS c \
				WHERE a.airport_name = b.departure_airport\
				AND b.arrival_airport = c.airport_name\
				AND a.airport_city= \'{}\' \
				AND c.airport_city = \'{}\' \
				AND departure_time LIKE \'{}\'"
				cursor.execute(query.format(departure, arrival, '%'+str(date)+'%'))
				flight = cursor.fetchall()

				if not flight:
					msg = "There's no available flight based on the condition you insert."

	return render_template('search.html', msg=msg, flight=flight, data1=data1)

@app.route('/status', methods=['GET', 'POST'])
def status():
	cursor = conn.cursor()
	cursor.execute('SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time FROM flight WHERE status = "DELAYED"')
	data1 = cursor.fetchall()
	msg = ''
	flight = ''

	if request.method == 'POST':
		airline = request.form['airline']
		flight_num = request.form['flight#']
		date = request.form['date']
	
		cursor = conn.cursor()
		query = "SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time, arrival_time, status \
			FROM flight WHERE airline_name = \'{}\' AND flight_num = \'{}\' AND departure_time LIKE \'{}\'"

		cursor.execute(query.format(airline, flight_num, '%'+str(date)+'%'))
		flight = cursor.fetchall()

		if not flight:
			msg = "There's no available flight based on the condition you insert."

	return render_template('status.html',flight = flight, data1=data1, msg=msg)

@app.route('/customer/status', methods=['GET', 'POST'])
def statuscus():
	if 'username' in session and 'cus' in session:
		msg = ''
		flight = ''
		
		if request.method == 'POST':
			airline = request.form['airline']
			flight_num = request.form['flight#']
			date = request.form['date']

			cursor = conn.cursor()
			query = "SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time, arrival_time, status FROM flight WHERE airline_name = \'{}\' AND flight_num = \'{}\' AND departure_time LIKE \'{}\'"

			cursor.execute(query.format(airline, flight_num, '%'+str(date)+'%'))
			flight = cursor.fetchall()

			if not flight:
				msg = "There's no available flight based on the condition you insert."

		return render_template('statuscus.html', flight=flight, msg=msg)
	return redirect(url_for('prelogin'))

@app.route('/customer/book', methods=['GET', 'POST'])
def bookcus():
	if 'username' in session and 'cus' in session:
		# cursor = conn.cursor()
		# cursor.execute('SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time FROM flight WHERE status = "DELAYED"')
		# data1 = cursor.fetchall()
		global flight_date
		global flight
		msg = ''
		flight = ''
		flight_date = ""

		if request.method == 'POST':
			
			departure = request.form['departure']
			arrival = request.form['arrival']
			flight_date = request.form['date']
			a = datetime.strptime(flight_date, '%Y-%m-%d')


			if departure.isupper() is True and arrival.isupper() is False or departure.isupper() is False and arrival.isupper() is True:
				msg = 'Please fill in the both blanks in Airport Code or City Name!'
			
			elif a < datetime.today():
				msg = 'You can only search for upcoming flights!'

			else:
				if departure.isupper():
					cursor = conn.cursor()
					query = "SELECT ALL airline_name, flight_num, departure_airport, arrival_airport, departure_time, arrival_time, price, seats-count(ticket_id) AS seat_left \
							FROM flight LEFT JOIN ticket USING (airline_name, flight_num) JOIN airplane USING (airline_name, airplane_id)\
							WHERE departure_airport = \'{}\' \
							AND arrival_airport = \'{}\'\
							AND departure_time LIKE \'{}\' \
							GROUP BY airline_name, flight_num"

					cursor.execute(query.format(departure, arrival, '%'+str(flight_date)+'%'))
					flight = cursor.fetchall()
				
					if not flight:
						msg = "There's no available flight based on the condition you insert."

				else:
					cursor = conn.cursor()
					query = "SELECT ALL airline_name, flight_num, departure_airport, arrival_airport, departure_time, arrival_time, price, seats-count(ticket_id) AS seat_left\
							FROM airport AS a, (flight LEFT JOIN ticket USING (airline_name, flight_num) JOIN airplane USING (airline_name, airplane_id)), airport AS c \
							WHERE a.airport_name = departure_airport\
							AND arrival_airport = c.airport_name\
							AND a.airport_city= \'{}\'\
							AND c.airport_city = \'{}\'\
							AND departure_time LIKE \'{}\'\
							GROUP BY airline_name, flight_num"

					cursor.execute(query.format(departure, arrival, '%'+str(flight_date)+'%'))
					flight = cursor.fetchall()

					if not flight:
						msg = "There's no available flight based on the condition you insert."

		return render_template('bookcus.html', msg=msg, flight=flight)

	return redirect(url_for('prelogin'))

@app.route('/customer/bookconfirm', methods=['GET', 'POST'])
def bookcusconfirm():
	if 'username' in session and 'cus' in session:
		email = session['username']
		msg = ''
		airline = request.form['airline']
		flight_num = request.form['flight_num']
		cursor = conn.cursor()
		#executes query
		query = "SELECT seats-count(ticket_id) AS seat_left\
		FROM flight JOIN ticket USING (airline_name, flight_num) JOIN airplane USING (airline_name, airplane_id)\
		WHERE airline_name = \'{}\' \
		AND flight_num = \'{}\'"
		cursor.execute(query.format(airline, flight_num))
		#stores the results in a variable
		data = cursor.fetchone()
		if data[0] == None:
			msg = "The flight number does not exist!"
			return render_template('bookcus.html', msg=msg, flight=flight, date=flight_date)
		elif data[0] == 0:
			#If the previous query returns data, then user exists
			msg = "This flight has been sold out!"
			return render_template('bookcus.html', msg=msg, flight=flight, date=flight_date)
		else:
			a = 0
			while a == 0:
				tkt_id = randint(100000000, 999999999)
				query = "SELECT * FROM ticket WHERE ticket_id = \'{}\'"
				cursor.execute(query.format(tkt_id))
				data = cursor.fetchone()
				if not data:
					a = 1
			try:
				ins1 = "INSERT INTO ticket VALUES(\'{}\', \'{}\', \'{}\')"
				cursor.execute(ins1.format(tkt_id, airline, flight_num))
				today = datetime.today().strftime('%Y-%m-%d')
				ins2 = "INSERT INTO purchases (ticket_id, customer_email, purchase_date) VALUES(\'{}\', \'{}\', \'{}\')"
				cursor.execute(ins2.format(tkt_id, email, today))
				conn.commit()
				cursor.close()
				msg = "You have successfully booked the flight! " + airline + " " + flight_num + " on " + flight_date
				msg1 = "Ticket ID: " + str(tkt_id)
				#flash("Booking Successful! Flight:" + airline + flight_num)
				return render_template('bookcusconfirm.html', msg=msg, msg1=msg1)
			except NameError:
				redirect(url_for('bookcus'))

	return redirect(url_for('prelogin'))


@app.route('/customer/account', methods = ["GET", "POST"])
def accountcus():
	if 'username' in session and 'cus' in session:
		email = session['username']
		
		start_date = date.today() + relativedelta(months=-6)
		end_date = date.today()
		msg = ''
		result = []
		result_temp = []
		ran = str(start_date) + " - " + str(end_date)

		curdate = start_date
		curdate1 = start_date + relativedelta(months=+1)
		i = 0
		cursor = conn.cursor()
		while curdate < end_date:
			
			q = "SELECT SUM(price) FROM purchases NATURAL JOIN ticket NATURAL JOIN flight\
				WHERE customer_email = \'{}\'\
				AND purchase_date > \'{}\' AND purchase_date <= \'{}\'"
			cursor.execute(q.format(email, curdate, curdate1))
			result.append(cursor.fetchone()[0])
			i += 1
			curdate = curdate + relativedelta(months=+1)
			curdate1 = curdate + relativedelta(months=+1)
		

		tot = 0
		for i in result:
			if i is not None:
				tot += i


		num = dict()
		k = start_date
		#k = datetime.strptime(start_date, '%Y-%m-%d')
		k1=str(k)
		k2 = ''
		for a in k1:
			if a == '-':
				continue
			else:
				k2 += a

		for a in result:
			if a is None:
				num[k2[0:8]] = 0
			else:
				num[k2[0:8]] = a
			k = k + relativedelta(months=+1)
			k1=str(k)
			k2 = ''
			for a in k1:
				if a == '-':
					continue
				else:
					k2 += a

		if request.method == 'POST':
			start_date = request.form['start date']
			end_date = request.form['end date']
			# end_date = datetime.strptime(end_date, '%Y-%m-%d')

			ran = str(start_date) + " - " + str(end_date)
			date1 = datetime.strptime(end_date, '%Y-%m-%d')
			
			if date1 > datetime.today():
				msg = "Please enter a valid date range in the past!"
				return render_template('accountcus.html', result=result, msg=msg, tot=tot, num = num)

			else:
				i = 0
				curdate = datetime.strptime(start_date, '%Y-%m-%d')
				#curdate = start_date
				curdate1 = curdate + relativedelta(months=+1)

				cursor = conn.cursor()
				while curdate <= date1:
					q = "SELECT SUM(price) FROM purchases NATURAL JOIN ticket NATURAL JOIN flight\
					WHERE customer_email = \'{}\'\
					AND purchase_date > \'{}\' AND purchase_date <= \'{}\'"
					cursor.execute(q.format(email, str(curdate)[0:10], str(curdate1)[0:10]))
					result_temp.append(cursor.fetchone()[0])

					i += 1
					curdate = curdate + relativedelta(months=+1)
					curdate1 = curdate + relativedelta(months=+1)

					if i == 13:
						msg = 'Please keep the date range within 12 months!'
						return render_template('accountcus.html', msg=msg, tot=tot, ran=ran, num=num)

				result = result_temp

				tot = 0
				for i in result:
					if i is not None:
						tot += i


				num = dict()
				k = datetime.strptime(start_date, '%Y-%m-%d')
				k1=str(k)
				k2 = ''
				for a in k1:
					if a == '-':
						# k2 += '.'
						continue
					else:
						k2 += a

				#1 = str(k)
				#k1 = start_date
				for a in result:
					if a is None:
						num[k2[0:8]] = 0
					else:
						num[k2[0:8]] = a

					k = k + relativedelta(months=+1)
					k1=str(k)
					k2 = ''
					for a in k1:
						if a == '-':
							# k2 += '.'
							continue
						else:
							k2 += a
				

				return render_template('accountcus.html', result=result, msg=msg, ran=ran, tot=tot, num = num)

		return render_template('accountcus.html', result=result, msg=msg, ran=ran, tot=tot, num = num)
	return redirect(url_for('prelogin'))


@app.route('/customer/trips', methods=['GET', 'POST'])
def tripscus():
	if 'username' in session and 'cus' in session:
		cursor = conn.cursor()
		customer_email = session['username']
		#default time is showing all the upcoming flights
		start_date = datetime.today()
		msg = ''
		condition = ''

		q = 'SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time, arrival_time, price, status, ticket_id \
			FROM flight NATURAL JOIN ticket NATURAL JOIN purchases \
			WHERE departure_time >= \'{}\' AND customer_email = \'{}\''
		cursor.execute(q.format(start_date, customer_email))
		t = cursor.fetchall()

		if t is None:
			msg = "There's no upcoming flights! Please do advanced search!"
		else:
			condition = 'Upcoming flights:'
		
		if request.method == 'POST':
			start_date = request.form['start date']
			end_date = request.form['end date']
			departure = request.form['departure']
			arrival = request.form['arrival']

			if departure.isupper():
				cursor = conn.cursor()
				q = 'SELECT f.airline_name, f.flight_num, f.departure_airport, f.arrival_airport, f.departure_time, f.arrival_time, f.price, f.status, t.ticket_id \
					FROM flight f JOIN ticket t ON(f.airline_name = t.airline_name AND f.flight_num = t.flight_num) \
					JOIN purchases p ON(t.ticket_id = p.ticket_id) JOIN airport a ON(f.departure_airport = a.airport_name) \
					JOIN airport b ON(f.arrival_airport = b.airport_name) \
					WHERE p.customer_email = \'{}\' AND p.purchase_date <= \'{}\' AND p.purchase_date >= \'{}\' \
					AND f.departure_airport = \'{}\' AND f.arrival_airport = \'{}\' '
				cursor.execute(q.format(customer_email, end_date, start_date, departure, arrival))
				t = cursor.fetchall()
			else:
				cursor = conn.cursor()
				q = 'SELECT f.airline_name, f.flight_num, f.departure_airport, f.arrival_airport, f.departure_time, f.arrival_time, f.price, f.status, t.ticket_id \
					FROM flight f JOIN ticket t ON(f.airline_name = t.airline_name AND f.flight_num = t.flight_num) \
					JOIN purchases p ON(t.ticket_id = p.ticket_id) JOIN airport a ON(f.departure_airport = a.airport_name) \
					JOIN airport b ON(f.arrival_airport = b.airport_name) \
					WHERE p.customer_email = \'{}\' AND p.purchase_date <= \'{}\' AND p.purchase_date >= \'{}\' \
					AND a.airport_city = \'{}\' AND b.airport_city = \'{}\''
				cursor.execute(q.format(customer_email, end_date, start_date, departure, arrival))
				t = cursor.fetchall()
			
			if not t:
				msg = "There's no booked flight based on the condition you insert."
			else:
				condition = 'Search Result:'

		return render_template('tripscus.html', msg = msg, t = t, condition = condition)
		# User is not loggedin redirect to login pages
	return redirect(url_for('prelogin'))

@app.route('/customer/profile')
def profilecus():
	if 'username' in session and 'cus' in session:

		cursor = conn.cursor()
		username = session['username']
        # We need all the account info for the user so we can display it on the profile page
		q = 'SELECT * FROM customer WHERE email = \'{}\''
		cursor.execute(q.format(username))
		
		account = cursor.fetchone()
		# Show the profile page with account info
		return render_template('profilecus.html', account=account)
    # User is not loggedin redirect to login page
	return redirect(url_for('prelogin'))


@app.route('/agent/book', methods=['GET', 'POST'])
#where booking agent book the flights
def bookagent():
	if 'username' in session and 'id' in session:
		#book_id = session['id']
		# cursor = conn.cursor()
		# cursor.execute('SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time FROM flight WHERE status = "DELAYED"')
		# data1 = cursor.fetchall()
		global flight_date
		global flight
		msg = ''
		flight = ''
		flight_date = ""

		if request.method == 'POST':
			
			departure = request.form['departure']
			arrival = request.form['arrival']
			flight_date = request.form['date']
			a = datetime.strptime(flight_date, '%Y-%m-%d')


			if departure.isupper() is True and arrival.isupper() is False or departure.isupper() is False and arrival.isupper() is True:
				msg = 'Please fill in the both blanks in Airport Code or City Name!'
			
			elif a < datetime.today():
				msg = 'You can only search for upcoming flights!'

			else:
				if departure.isupper():
					cursor = conn.cursor()
					query = "SELECT ALL airline_name, flight_num, departure_airport, arrival_airport, departure_time, arrival_time, price, seats-count(ticket_id) AS seat_left \
							FROM flight LEFT JOIN ticket USING (airline_name, flight_num) JOIN airplane USING (airline_name, airplane_id)\
							WHERE departure_airport = \'{}\' \
							AND arrival_airport = \'{}\' \
							AND departure_time LIKE \'{}\' \
							GROUP BY airline_name, flight_num"

					cursor.execute(query.format(departure, arrival, '%'+str(flight_date)+'%'))
					flight = cursor.fetchall()
				
					if not flight:
						msg = "There's no available flight based on the condition you insert."

				else:
					cursor = conn.cursor()
					query = "SELECT ALL airline_name, flight_num, departure_airport, arrival_airport, departure_time, arrival_time, price, seats-count(ticket_id) AS seat_left\
							FROM airport AS a, (flight LEFT JOIN ticket USING (airline_name, flight_num) JOIN airplane USING (airline_name, airplane_id)), airport AS c \
							WHERE a.airport_name = departure_airport\
							AND arrival_airport = c.airport_name\
							AND a.airport_city= \'{}\'\
							AND c.airport_city = \'{}\'\
							AND departure_time LIKE \'{}\'\
							GROUP BY airline_name, flight_num"

					cursor.execute(query.format(departure, arrival, '%'+str(flight_date)+'%'))
					flight = cursor.fetchall()

					if not flight:
						msg = "There's no available flight based on the condition you insert."

		return render_template('bookagent.html', msg=msg, flight=flight)

	return redirect(url_for('prelogin'))

@app.route('/agent/bookconfirm', methods=['GET', 'POST'])
def bookagentconfirm():
	if 'username' in session and 'id' in session:
		
		book_id = session['id']
		msg = ''
		airline = request.form['airline']
		flight_num = request.form['flight_num']
		cus_email = request.form['cus_email']

		cursor = conn.cursor()

		preq = "SELECT * FROM customer WHERE email = \'{}\'"
		cursor.execute(preq.format(cus_email))
		content = cursor.fetchone()
		if not content:
			msg = 'Customer does not exist!'
			return render_template('bookagent.html', msg=msg, flight=flight, date=flight_date)

		else:
			#executes query
			query = "SELECT seats-count(ticket_id) AS seat_left\
			FROM flight JOIN ticket USING (airline_name, flight_num) JOIN airplane USING (airline_name, airplane_id)\
			WHERE airline_name = \'{}\' \
			AND flight_num = \'{}\'"

			cursor.execute(query.format(airline, flight_num))
			#stores the results in a variable
			data = cursor.fetchone()

			if data[0] == None:
				msg = "The flight number does not exist!"
				return render_template('bookagent.html', msg=msg, flight=flight, date=flight_date)

			elif data[0] == 0:
				#If the previous query returns data, then user exists
				msg = "This flight has been sold out!"
				return render_template('bookagent.html', msg=msg, flight=flight, date=flight_date)

			else:
				a = 0
				while a == 0:
					tkt_id = randint(100000000, 999999999)
					query = "SELECT * FROM ticket WHERE ticket_id = \'{}\'"
					cursor.execute(query.format(tkt_id))
					data = cursor.fetchone()
					if not data:
						a = 1
				try:
					ins1 = "INSERT INTO ticket VALUES(\'{}\', \'{}\', \'{}\')"
					cursor.execute(ins1.format(tkt_id, airline, flight_num))

					today = datetime.today().strftime('%Y-%m-%d')

					ins2 = "INSERT INTO purchases VALUES(\'{}\', \'{}\', \'{}\', \'{}\')"
					cursor.execute(ins2.format(tkt_id, cus_email, book_id, today))
					conn.commit()
					cursor.close()
				
					msg = "You have successfully booked the flight! " + airline + " " + flight_num + " on " + flight_date + " for " + cus_email
					msg1 = "Ticket ID: " + str(tkt_id)
					#flash("Booking Successful! Flight:" + airline + flight_num)
					return render_template('bookagentconfirm.html', msg=msg, msg1=msg1)
				except NameError:
					redirect(url_for('bookagent'))

	return redirect(url_for('prelogin'))

@app.route('/agent/trips', methods=['GET', 'POST'])
def tripsagent():
	if 'username' in session and 'id' in session:
		cursor = conn.cursor()
		booking_agent_id = session['id']
		#default time is showing all the upcoming flights
		start_date = datetime.today()
		msg = ''
		condition = ''

		q = 'SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time, arrival_time, price, status, ticket_id \
			FROM flight NATURAL JOIN ticket NATURAL JOIN purchases \
			WHERE departure_time >= \'{}\' AND booking_agent_id = \'{}\''
		cursor.execute(q.format(start_date, booking_agent_id))
		t = cursor.fetchall()

		if t is None:
			msg = "There's no upcoming flights! Please do advanced search!"
		else:
			condition = 'Upcoming flights:'
		
		if request.method == 'POST':
			start_date = request.form['start date']
			end_date = request.form['end date']
			departure = request.form['departure']
			arrival = request.form['arrival']

			if departure.isupper():
				cursor = conn.cursor()
				q = 'SELECT f.airline_name, f.flight_num, f.departure_airport, f.arrival_airport, f.departure_time, f.arrival_time, f.price, f.status, t.ticket_id \
					FROM flight f JOIN ticket t ON(f.airline_name = t.airline_name AND f.flight_num = t.flight_num) \
					JOIN purchases p ON(t.ticket_id = p.ticket_id) JOIN airport a ON(f.departure_airport = a.airport_name) \
					JOIN airport b ON(f.arrival_airport = b.airport_name) \
					WHERE p.booking_agent_id = \'{}\' AND p.purchase_date <= \'{}\' AND p.purchase_date >= \'{}\' \
					AND f.departure_airport = \'{}\' AND f.arrival_airport = \'{}\' '
				cursor.execute(q.format(booking_agent_id, end_date, start_date, departure, arrival))
				t = cursor.fetchall()
			else:
				cursor = conn.cursor()
				q = 'SELECT f.airline_name, f.flight_num, f.departure_airport, f.arrival_airport, f.departure_time, f.arrival_time, f.price, f.status , t.ticket_id \
					FROM flight f JOIN ticket t ON(f.airline_name = t.airline_name AND f.flight_num = t.flight_num) \
					JOIN purchases p ON(t.ticket_id = p.ticket_id) JOIN airport a ON(f.departure_airport = a.airport_name) \
					JOIN airport b ON(f.arrival_airport = b.airport_name) \
					WHERE p.booking_agent_id = \'{}\' AND p.purchase_date <= \'{}\' AND p.purchase_date >= \'{}\' \
					AND a.airport_city = \'{}\' AND b.airport_city = \'{}\''
				cursor.execute(q.format(booking_agent_id, end_date, start_date, departure, arrival))
				t = cursor.fetchall()
			
			if not t:
				msg = 'There is no available flight based on the condition you insert.'
			else:
				condition = 'Search Result:'

		return render_template('tripsagent.html', msg = msg, t = t, condition = condition)
		# User is not loggedin redirect to login pages
	return redirect(url_for('prelogin'))

@app.route('/agent/status', methods=['GET', 'POST'])
def statusagent():
	if 'username' in session and 'id' in session:
		msg = ''
		flight = ''

		if request.method == 'POST':
			airline = request.form['airline']
			flight_num = request.form['flight#']
			date = request.form['date']

			cursor = conn.cursor()
			query = "SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time, arrival_time, status FROM flight WHERE airline_name = \'{}\' AND flight_num = \'{}\' AND departure_time LIKE \'{}\'"

			cursor.execute(query.format(airline, flight_num, '%'+str(date)+'%'))
			flight = cursor.fetchall()

			if not flight:
				msg = "There's no available flight based on the condition you insert."

		return render_template('statusagent.html', flight=flight, msg=msg)
	return redirect(url_for('prelogin'))

@app.route('/agent/commission', methods=['GET', 'POST'])
def commissionagent():
	if 'username' in session and 'id' in session:
		cursor = conn.cursor()
		#username = session['username']
		booking_agent_id = session['id']
		#default time is in the past 30 days
		end_date = date.today()
		start_date = (end_date-timedelta(days=30))

		q = 'SELECT CAST(0.1*SUM(price) as decimal(10,2)), CAST((0.1*price)/COUNT(*) as decimal(10,2)), COUNT(*) \
			FROM purchases NATURAL JOIN ticket NATURAL JOIN flight \
		WHERE booking_agent_id = \'{}\' AND purchase_date <= \'{}\' AND purchase_date >= \'{}\''
		cursor.execute(q.format(booking_agent_id, end_date, start_date))
		commission = cursor.fetchone()

		if request.method == 'POST':
			start_date = request.form['start date']
			end_date = request.form['end date']

			q = 'SELECT CAST(0.1*SUM(price) as decimal(10,2)), CAST((0.1*price)/COUNT(*) as decimal(10,2)), COUNT(*) \
				FROM purchases NATURAL JOIN ticket NATURAL JOIN flight \
			WHERE booking_agent_id = \'{}\' AND purchase_date <= \'{}\' AND purchase_date >= \'{}\''
			cursor.execute(q.format(booking_agent_id, end_date, start_date))
			commission = cursor.fetchone()
				
		if commission is None:
			c = [[0],[0],[0]]
		else:
			c = commission

		return render_template('commissionagent.html', c = c, start_date = start_date, end_date = end_date)
		# User is not loggedin redirect to login pages
	return redirect(url_for('prelogin'))

@app.route('/agent/topcus')
def topcus():
	if 'username' in session and 'id' in session:
		result1 = []
		result2 = []
		num1 = dict()
		num2 = dict()
		cursor = conn.cursor()
		booking_agent_id = session['id']
		end_date = date.today()
		start_date = (end_date-timedelta(days=180))
		start_date_year = end_date-timedelta(days=365)
		end_date_last = start_date_year.strftime("%Y")+'-12-31'
		start_date_last = start_date_year.strftime("%Y")+'-01-01'

		q1 = "SELECT name, count(ticket_id) FROM purchases JOIN customer ON (customer.email = purchases.customer_email)\
			WHERE booking_agent_id = \'{}\'\
			AND purchase_date <= \'{}\' AND purchase_date >= \'{}\'\
			GROUP BY customer_email\
			ORDER BY COUNT(ticket_id) DESC LIMIT 5"

		cursor.execute(q1.format(booking_agent_id, end_date, start_date))
		out = cursor.fetchall()

		#i = 1
		for a in out:

			result1.append(a[0].strip())
			num1[a[0]] = a[1]
			#i += 1
		
		q2 = "SELECT name, CAST(0.1*SUM(price) as decimal(10,2))\
			FROM (purchases NATURAL JOIN ticket NATURAL JOIN flight) JOIN customer ON (customer.email = customer_email)\
			WHERE booking_agent_id = \'{}\' AND purchase_date <= \'{}\' AND purchase_date >= \'{}\'\
			GROUP BY customer_email\
			ORDER BY COUNT(ticket_id) DESC LIMIT 5"
		
		cursor.execute(q2.format(booking_agent_id, end_date_last, start_date_last))
		out = cursor.fetchall()

		for a in out:
			result2.append(a[0].strip())
			num2[a[0]] = a[1]
	

		return render_template('topcus.html', num1=num1, num2=num2, result1=result1, result2=result2)
	return redirect(url_for('prelogin'))

@app.route('/agent/profile')
def profileagent():
	if 'username' in session and 'id' in session:

		cursor = conn.cursor()
		username = session['username']
        # We need all the account info for the user so we can display it on the profile page
		q = 'SELECT * FROM booking_agent WHERE email = \'{}\''
		cursor.execute(q.format(username))
		
		account = cursor.fetchone()
		# Show the profile page with account info
		return render_template('profileagent.html', account=account)
    # User is not loggedin redirect to login page
	return redirect(url_for('prelogin'))

@app.route('/staff/trips', methods=['GET', 'POST'])
def tripsstaff():
	if 'username' in session and 'airline name' in session:
		cursor = conn.cursor()
		airline_name = session['airline name']
		#default time is showing all the upcoming flights
		start_date = datetime.today()
		end_date = start_date + timedelta(days=30)
		msg = ''
		condition = ''

		q = 'SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time, arrival_time, price, status \
			FROM flight WHERE departure_time >= \'{}\' AND departure_time <= \'{}\' AND airline_name = \'{}\''
		cursor.execute(q.format(start_date, end_date, airline_name))
		t = cursor.fetchall()

		if not t:
			msg = "There's no upcoming flights in the next 30 days! Please do advanced search!"
		else:
			condition = 'Upcoming flights in the next 30 days:'
		
		if request.method == 'POST':
			start_date = request.form['start date']
			end_date = request.form['end date']
			departure = request.form['departure']
			arrival = request.form['arrival']

			if departure.isupper():
				cursor = conn.cursor()
				q = 'SELECT f.airline_name, f.flight_num, f.departure_airport, f.arrival_airport, f.departure_time, f.arrival_time, f.price, f.status \
					FROM flight f \
					WHERE f.departure_time >= \'{}\' AND f.departure_time <= \'{}\' \
					AND f.departure_airport = \'{}\' AND f.arrival_airport = \'{}\' AND f.airline_name = \'{}\' '
				cursor.execute(q.format(start_date, end_date, departure, arrival, airline_name))
				t = cursor.fetchall()
			else:
				cursor = conn.cursor()
				q = 'SELECT f.airline_name, f.flight_num, f.departure_airport, f.arrival_airport, f.departure_time, f.arrival_time, f.price, f.status \
					FROM flight f JOIN airport a ON(f.departure_airport = a.airport_name) \
					JOIN airport b ON(f.arrival_airport = b.airport_name) \
					WHERE f.departure_time >= \'{}\' AND f.departure_time <= \'{}\' \
					AND a.airport_city = \'{}\' AND b.airport_city = \'{}\' AND f.airline_name = \'{}\''
				cursor.execute(q.format(start_date, end_date, departure, arrival, airline_name))
				t = cursor.fetchall()
			
			if not t:
				msg = "There's no available flight based on the condition you insert."
			else:
				condition = 'Search Result:'

		return render_template('tripsstaff.html', msg = msg, t = t, condition = condition)
		# User is not loggedin redirect to login pages
	return redirect(url_for('prelogin'))

@app.route('/staff/viewagents')
def viewagents():
 if 'username' in session and 'airline name' in session:
  end_date = date.today()
  start_date_month = end_date-timedelta(days=30)
  start_date_year = end_date-timedelta(days=365)
  end_date_last = start_date_year.strftime("%Y")+'-12-31'
  start_date_last = start_date_year.strftime("%Y")+'-01-01'

  cursor = conn.cursor()
  q = 'SELECT email FROM purchases NATURAL JOIN booking_agent \
   WHERE purchase_date <= \'{}\' AND purchase_date >= \'{}\' \
   GROUP BY booking_agent_id ORDER BY COUNT(*) DESC LIMIT 5'
  cursor.execute(q.format(end_date, start_date_month))
  s = cursor.fetchall()
  
  
  q = 'SELECT email FROM purchases NATURAL JOIN booking_agent \
   WHERE purchase_date <= \'{}\' AND purchase_date >= \'{}\' \
   GROUP BY booking_agent_id ORDER BY COUNT(*) DESC LIMIT 5'
  cursor.execute(q.format(end_date, start_date_year))
  y = cursor.fetchall()

  q = 'SELECT email FROM purchases NATURAL JOIN ticket NATURAL JOIN flight NATURAL JOIN booking_agent \
   WHERE purchase_date <= \'{}\' AND purchase_date >= \'{}\' \
   GROUP BY booking_agent_id ORDER BY SUM(price) DESC LIMIT 5'
  cursor.execute(q.format(end_date_last, start_date_last))
  c = cursor.fetchall()

  q = 'SELECT email FROM booking_agent'
  cursor.execute(q)
  t = cursor.fetchall()

  return render_template('viewagents.html', s = s, y = y, c = c, t = t)
 return redirect(url_for('prelogin'))



@app.route('/staff/viewcus')
def viewcus():
	if 'username' in session and 'airline name' in session:
		cursor = conn.cursor()
		airline_name = session['airline name']

		msg1 = ''
		msg2 = ''

		end_date = date.today()
		taken_time = datetime.today()
		start_date = end_date-timedelta(days=365)

		end_date_last = start_date.strftime("%Y")+'-12-31'
		start_date_last = start_date.strftime("%Y")+'-01-01'

		q = 'SELECT name, email FROM customer JOIN purchases ON (customer.email = purchases.customer_email) \
		WHERE purchase_date <= \'{}\' AND purchase_date >= \'{}\' \
		GROUP BY email ORDER BY COUNT(ticket_id) DESC'
		cursor.execute(q.format(end_date_last, start_date_last))
		cus = cursor.fetchone()

		if cus is None:
			msg1 = 'No customer bought ticket last year!'

		q = 'SELECT DISTINCT customer_email, flight_num FROM flight NATURAL JOIN ticket NATURAL JOIN purchases \
		WHERE airline_name = \'{}\' AND departure_time <= \'{}\' GROUP BY customer_email'
		cursor.execute(q.format(airline_name, taken_time))
		lst = cursor.fetchall()

		if lst is None:
			msg2 = 'No customer has bought ticket from your airline'

		return render_template('viewcus.html', msg1 = msg1, msg2 = msg2, customer = cus, lst = lst, airline_name = airline_name)
	
	# User is not loggedin redirect to login pages
	return redirect(url_for('prelogin'))


@app.route('/staff/viewreports', methods = ["GET", "POST"])
def viewreports():
	if 'username' in session and 'airline name' in session:
		airline = session['airline name']
		#email = session['username']
		
		start_date = date.today() + relativedelta(months=-12)
		end_date = date.today()
		msg = ''
		result = []
		result_temp = []
		ran = str(start_date) + " - " + str(end_date)

		curdate = start_date
		curdate1 = start_date + relativedelta(months=+1)
		i = 0
		cursor = conn.cursor()
		while curdate < end_date:
			
			q = "SELECT COUNT(ticket_id) FROM purchases NATURAL JOIN ticket\
				WHERE airline_name = \'{}\'\
				AND purchase_date > \'{}\' AND purchase_date <= \'{}\'"

			cursor.execute(q.format(airline, curdate, curdate1))
			result.append(cursor.fetchone()[0])
			i += 1
			curdate = curdate + relativedelta(months=+1)
			curdate1 = curdate + relativedelta(months=+1)
		

		tot = 0
		for i in result:
			if i is not None:
				tot += i

		num = dict()
		k = start_date
		#k = datetime.strptime(start_date, '%Y-%m-%d')
		k1=str(k)
		k2 = ''
		for a in k1:
			if a == '-':
				continue

			else:
				k2 += a

		for a in result:
			if a is None:
				num[k2[0:8]] = 0
			else:
				num[k2[0:8]] = a

			k = k + relativedelta(months=+1)
			k1=str(k)
			k2 = ''
			for a in k1:
				if a == '-':
					continue
				else:
					k2 += a

		if request.method == 'POST':
			start_date = request.form['start date']
			end_date = request.form['end date']
			# end_date = datetime.strptime(end_date, '%Y-%m-%d')

			ran = str(start_date) + " - " + str(end_date)
			date1 = datetime.strptime(end_date, '%Y-%m-%d')
			
			if date1 > datetime.today():
				msg = "Please enter a valid date range in the past!"
				return render_template('viewreports.html', result=result, msg=msg, tot=tot, num = num)

			else:
				i = 0
				curdate = datetime.strptime(start_date, '%Y-%m-%d')
				#curdate = start_date
				curdate1 = curdate + relativedelta(months=+1)

				cursor = conn.cursor()
				while curdate <= date1:
					q = "SELECT COUNT(ticket_id) FROM purchases NATURAL JOIN ticket\
					WHERE airline_name = \'{}\'\
					AND purchase_date > \'{}\' AND purchase_date <= \'{}\'"
					cursor.execute(q.format(airline, str(curdate)[0:10], str(curdate1)[0:10]))
					result_temp.append(cursor.fetchone()[0])

					i += 1
					curdate = curdate + relativedelta(months=+1)
					curdate1 = curdate + relativedelta(months=+1)

					if i == 13:
						msg = 'Please keep the date range within 12 months!'
						return render_template('viewreports.html', msg=msg, tot=tot, ran=ran, num=num)

				result = result_temp

				tot = 0
				for i in result:
					if i is not None:
						tot += i
				num = dict()
				#k = start_date
				k = datetime.strptime(start_date, '%Y-%m-%d')
				k1=str(k)
				k2 = ''
				for a in k1:
					if a == '-':
						continue

					else:
						k2 += a

				#1 = str(k)
				#k1 = start_date
				for a in result:
					if a is None:
						num[k2[0:8]] = 0
					else:
						num[k2[0:8]] = a

					k = k + relativedelta(months=+1)
					k1=str(k)
					k2 = ''
					for a in k1:
						if a == '-':
							continue
						else:
							k2 += a

				#tot = sum(result)
				return render_template('viewreports.html', result=result, msg=msg, ran=ran, tot=tot, num = num)

		return render_template('viewreports.html', result=result, msg=msg, ran=ran, tot=tot, num = num)
	return redirect(url_for('prelogin'))


@app.route('/staff/revenue')
def revenue():

	if 'username' in session and 'airline name' in session:

		num1 = dict()
		num2 = dict()

		cursor = conn.cursor()
		airline = session['airline name']
		lastYear = int(datetime.now().year) - 1
		start_date_last_year = str(lastYear) + '-01-01'
		end_date_last_year = str(lastYear) + '-12-31'
		end_date_last_month = date.today().replace(day=1) - timedelta(days=1)
		start_date_last_month = date.today().replace(day=1) - timedelta(days=end_date_last_month.day)
		

		q1 = "SELECT count(ticket_id) FROM purchases NATURAL JOIN ticket\
			WHERE booking_agent_id is NULL\
			AND airline_name = \'{}\'\
			AND purchase_date <= \'{}\' AND purchase_date >= \'{}\'"

		cursor.execute(q1.format(airline, end_date_last_month, start_date_last_month))
		out1 = cursor.fetchall()

		q2 = "SELECT count(ticket_id) FROM purchases NATURAL JOIN ticket\
			WHERE booking_agent_id is not NULL\
			AND airline_name = \'{}\'\
			AND purchase_date <= \'{}\' AND purchase_date >= \'{}\'"
		
		cursor.execute(q2.format(airline, end_date_last_month, start_date_last_month))
		out2 = cursor.fetchall()

		num1["Direct Sales"] = out1[0][0]
		num1["Indirect Sales"] = out2[0][0]
		
		q3 = "SELECT count(ticket_id) FROM purchases NATURAL JOIN ticket\
			WHERE booking_agent_id is NULL\
			AND airline_name = \'{}\'\
			AND purchase_date <= \'{}\' AND purchase_date >= \'{}\'"
		
		cursor.execute(q3.format(airline, end_date_last_year, start_date_last_year))
		out3 = cursor.fetchall()

		q4 = "SELECT count(ticket_id) FROM purchases NATURAL JOIN ticket\
			WHERE booking_agent_id is NOT NULL\
			AND airline_name = \'{}\'\
			AND purchase_date <= \'{}\' AND purchase_date >= \'{}\'"
	
		cursor.execute(q4.format(airline, end_date_last_year, start_date_last_year))
		out4 = cursor.fetchall()

		num2["Direct Sales"] = out3[0][0]
		num2["Indirect Sales"] = out4[0][0]

		return render_template('revenue.html', num1=num1, num2=num2)
	return redirect(url_for('prelogin'))


@app.route('/staff/topdest')
def topdest():
 if 'username' in session and 'airline name' in session:
  cursor = conn.cursor()

  end_date = date.today()
  start_date_year = end_date-timedelta(days=365)
  start_date_3month = end_date-timedelta(days=90)
  
  q = 'SELECT airport_city FROM flight JOIN airport ON (flight.arrival_airport = airport.airport_name) \
	  NATURAL JOIN ticket NATURAL JOIN purchases \
   WHERE purchase_date <= \'{}\' AND purchase_date >= \'{}\' \
   GROUP BY airport_city ORDER BY COUNT(*) DESC LIMIT 3'
  cursor.execute(q.format(end_date, start_date_year))
  year = cursor.fetchall()

  q = 'SELECT airport_city FROM flight JOIN airport ON (flight.arrival_airport = airport.airport_name) \
	  NATURAL JOIN ticket NATURAL JOIN purchases \
   WHERE purchase_date <= \'{}\' AND purchase_date >= \'{}\' \
   GROUP BY airport_city ORDER BY COUNT(*) DESC LIMIT 3'
  cursor.execute(q.format(end_date, start_date_3month))
  month = cursor.fetchall()

  return render_template('topdest.html', year = year, month = month, start_date_year = start_date_year, start_date_3month = start_date_3month, end_date = end_date)
    # User is not loggedin redirect to login pages
 return redirect(url_for('prelogin'))

@app.route('/staff/profile')
def profilestaff():
	if 'username' in session and 'airline name' in session:

		cursor = conn.cursor()
		username = session['username']
        # We need all the account info for the user so we can display it on the profile page
		q = 'SELECT * FROM airline_staff WHERE username = \'{}\''
		cursor.execute(q.format(username))
		
		account = cursor.fetchone()
		# Show the profile page with account info
		return render_template('profilestaff.html', account=account)
    # User is not loggedin redirect to login page
	return redirect(url_for('prelogin'))


@app.route('/staff/createflights', methods=['GET', 'POST'])
def createflights():
	if 'username' in session and 'airline name' in session:
		
		cursor = conn.cursor()
		airline_name = session['airline name']
		msg = ''
		# cursor.execute("SELECT * FROM flight WHERE departure_time <= DATE_ADD(CURRENT_TIMESTAMP (), INTERVAL 30 DAY)")
		# data = cursor.fetchall()
		start_date = datetime.today()
		end_date = start_date + timedelta(days=30)

		q = 'SELECT * \
			FROM flight WHERE departure_time >= \'{}\' AND departure_time <= \'{}\' AND airline_name = \'{}\''
		cursor.execute(q.format(start_date, end_date, airline_name))
		data = cursor.fetchall()

		if request.method == 'POST':
			# Create variables for easy access
			airline_name = session['airline name']
			#airline_name = request.form['airline name']
			flight_num = request.form['flight num']
			departure_airport = request.form['departure airport']
			departure_time = request.form['departure time']
			arrival_airport = request.form['arrival airport']
			arrival_time = request.form['arrival time']
			price = request.form['price']
			status = request.form['status']
			airplane_id = request.form['airplane id']

			query1 = "SELECT * FROM flight WHERE airline_name = \'{}\' AND flight_num = \'{}\'"
			cursor.execute(query1.format(airline_name, flight_num))
			flight = cursor.fetchone()

			query2 = "SELECT * FROM airplane WHERE airline_name = \'{}\' AND airplane_id = \'{}\'"
			cursor.execute(query2.format(airline_name, airplane_id))
			airplane = cursor.fetchone()

			query3 = "SELECT * FROM airport WHERE airport_name = \'{}\'"
			cursor.execute(query3.format(departure_airport))
			airport1 = cursor.fetchone()

			query4 = "SELECT * FROM airport WHERE airport_name = \'{}\'"
			cursor.execute(query4.format(arrival_airport))
			airport2 = cursor.fetchone()

			if flight:
				msg = 'This flight already exists!'
			elif not airplane:
				msg = 'This airplane does not exist!'
			elif (not airport1):
				msg = 'The departure airport does not exist!'
			elif (not airport2):
				msg = 'The arrival airport does not exist!'
			# elif len(airline_name) >= 50:
			# 	msg = 'The Airline Name should be less than 50 characters!'
			elif len(flight_num) > 11:
				msg = 'The Flight No. should not exceed 11 characters!'
			elif len(departure_airport) >= 50:
				msg = 'The Departure Airport should be less than 50 characters!'
			elif len(arrival_airport) >= 50:
				msg = 'The Arrival Airport should be less than 50 characters!'
			elif len(status) >= 50:
				msg = 'The Status should be less than 50 characters!'
			elif len(airplane_id) > 11:
				msg = 'Number of seats should not exceed 11 characters!'
			else:
				# Account doesnt exists and the form data is valid, now insert new account into accounts table
				ins = "INSERT INTO flight VALUES( \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\')"
				cursor.execute(ins.format(airline_name, flight_num, departure_airport, departure_time, arrival_airport, \
					arrival_time, price, status, airplane_id))
				conn.commit()
				msg = 'You have successfully added the flight!'

			q = 'SELECT * \
			FROM flight WHERE departure_time >= \'{}\' AND departure_time <= \'{}\' AND airline_name = \'{}\''
			cursor.execute(q.format(start_date, end_date, airline_name))
			data = cursor.fetchall()

		return render_template('createflights.html', msg = msg, data=data)
	return redirect(url_for('prelogin'))

@app.route('/staff/statuschange', methods=['GET', 'POST'])
def statuschange():
	if 'username' in session and 'airline name' in session:
		cursor = conn.cursor()
		msg = ''

		cursor.execute("SELECT * FROM flight")
		data = cursor.fetchall()

		if request.method == 'POST':
			airline_name = session['airline name']
			flight_num = request.form['flight num']
			changed_status = request.form['status']

			query1 = "SELECT status FROM flight WHERE airline_name = \'{}\' AND flight_num = \'{}\'"
			cursor.execute(query1.format(airline_name, flight_num))
			current_status = cursor.fetchone()

			if (not current_status):
				msg = 'This flight does not exist!'
			elif (current_status[0] == changed_status):
				msg = 'The status does not need to be changed!'
			else:
				up = "UPDATE flight SET status = \'{}\' WHERE airline_name = \'{}\' AND flight_num = \'{}\'"
				cursor.execute(up.format(changed_status, airline_name, flight_num))
				conn.commit()
				msg = 'You have successfully changed the status!'

			cursor.execute("SELECT * FROM flight")
			data = cursor.fetchall()

		return render_template('statuschange.html', msg = msg, data=data)
	return redirect(url_for('prelogin'))

@app.route('/staff/addplane', methods=['GET', 'POST'])
def addplane():
	if 'username' in session and 'airline name' in session:
		cursor = conn.cursor()
		msg = ''
		cursor.execute("SELECT * FROM airplane")
		data = cursor.fetchall()
		if request.method == 'POST':
			# Create variables for easy access
			airline_name = session['airline name']
			airplane_id = request.form['airplane id']
			num_of_seats = request.form['seats']

			#Check if airplane exists using MySQL
			query1 = "SELECT * FROM airplane WHERE airline_name = \'{}\' AND airplane_id = \'{}\'"
			cursor.execute(query1.format(airline_name, airplane_id))
			airplane = cursor.fetchone()

			query2 = "SELECT * FROM airline WHERE airline_name = \'{}\'"
			cursor.execute(query2.format(airline_name))
			airline = cursor.fetchone()
			# If airplane exists show error and validation checks
			if airplane:
				msg = 'This airplane already exists!'
			elif (not airline):
				msg = 'This airline does not exist!'
			# elif len(airline_name) >= 50:
			# 	msg = 'The Airline Name should be less than 50 characters!'
			elif len(airplane_id) > 11:
				msg = 'The Airplane ID should not exceed 11 characters!'
			#type changed to varchar(11)
			elif len(num_of_seats) > 11:
				msg = 'Number of seats should not exceed 11 characters!'
			
			else:
				# Account doesnt exists and the form data is valid, now insert new account into accounts table
				ins = "INSERT INTO airplane VALUES( \'{}\', \'{}\', \'{}\')"
				cursor.execute(ins.format(airline_name, airplane_id, num_of_seats))
				conn.commit()
				msg = 'You have successfully added the airplane!'

			cursor.execute("SELECT * FROM airplane")
			data = cursor.fetchall()

		return render_template('addplane.html', msg=msg, data=data)
	return redirect(url_for('prelogin'))

@app.route('/staff/addairport', methods=['GET', 'POST'])
def addairport():
	if 'username' in session and 'airline name' in session:

		cursor = conn.cursor()
		msg = ''
		cursor.execute("SELECT * FROM airport")
		data = cursor.fetchall()
		if request.method == 'POST':
	
			# Create variables for easy access
			airport_name = request.form['airport name']
			airport_city = request.form['airport city']

			#Check if airport_name exists using MySQL
			query1 = "SELECT * FROM airport WHERE airport_name = \'{}\'"
			cursor.execute(query1.format(airport_name))
			airport = cursor.fetchone()

			# If airplane exists show error and validation checks
			if airport:
				msg = 'This airport already exists!'
			elif len(airport_name) >= 50:
				msg = 'The Airport Name should be less than 50 characters!'
			elif len(airport_city) >= 50:
				msg = 'The Airport City Name should be less than 50 characters!'
			else:
				# Account doesnt exists and the form data is valid, now insert new account into accounts table
				ins = "INSERT INTO airport VALUES( \'{}\', \'{}\')"
				cursor.execute(ins.format(airport_name, airport_city))
				conn.commit()
				msg = 'You have successfully added the airport!'

			cursor.execute("SELECT * FROM airport")
			data = cursor.fetchall()

		return render_template('addairport.html', msg=msg, data=data)
	
	return redirect(url_for('prelogin'))

#Define route for login
@app.route("/prelogin")
def prelogin():
	session.pop('username', None)
	session.pop('cus', None)
	session.pop('name', None)
	session.pop('airline name', None)
	session.pop('id', None)
	cursor = conn.cursor()
	cursor.execute('SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time FROM flight WHERE status = "DELAYED"')
	data1 = cursor.fetchall()

	return render_template('prelogin.html', data1=data1)

@app.route("/customerlogin", methods=['GET', 'POST'])
def customerlogin():
 	# connect
	cursor = conn.cursor()
	cursor.execute('SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time FROM flight WHERE status = "DELAYED"')
	data1 = cursor.fetchall()
    # Output message if something goes wrong...
	msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)		
	if request.method == 'POST':

        # Create variables for easy access
		email = request.form['email']
		password = request.form['password']
       
		cursor.execute('SELECT * FROM customer WHERE email = %s AND password = %s', (email, password))
        # Fetch one record and return result
		data = cursor.fetchone()
		
		# If account exists in accounts table in out database
		if data:
            # Create session data, we can access this data in other routes
			#session['name'] = ''.join(name).strip('',)
			name = data[1]
			session['name'] = name.strip('')
			session['cus'] = 'yes'
			session['username'] = email
			# Redirect to home page
			return redirect(url_for('cushome'))
		else:
            # Account doesnt exist or username/password incorrect
			msg = 'The email address or password you entered is incorrect!'
    
	return render_template('logincus.html', msg=msg, data1=data1)


@app.route("/booklogin", methods=['GET', 'POST'])
def booklogin():
	# connect
	cursor = conn.cursor()
	cursor.execute('SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time FROM flight WHERE status = "DELAYED"')
	data1 = cursor.fetchall()
	# Output message if something goes wrong...
	msg = ''
	# Check if "username" and "password" POST requests exist (user submitted form)
	if request.method == 'POST':
		# Create variables for easy access
		email = request.form['email']
		password = request.form['password']
		# Check if account exists using MySQL
		cursor.execute('SELECT * FROM booking_agent WHERE email = %s AND password = %s', (email, password))
		# Fetch one record and return result
		account = cursor.fetchone()
		# If account exists in accounts table in out database
		if account:
			# Create session data, we can access this data in other routes
			session['username'] = email
			session['id'] = account[2]
			# Redirect to home page
			return redirect(url_for('bookhome'))
		else:
			# Account doesnt exist or username/password incorrect
			msg = 'The email address or password you entered is incorrect!'

	return render_template('loginbook.html', msg=msg, data1=data1)


@app.route("/stafflogin", methods=['GET', 'POST'])
def stafflogin():
	# connect
	cursor = conn.cursor()
	cursor.execute('SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time FROM flight WHERE status = "DELAYED"')
	data1 = cursor.fetchall()
	# Output message if something goes wrong...
	msg = ''
	# Check if "username" and "password" POST requests exist (user submitted form)
	if request.method == 'POST':

		# Create variables for easy access
		email = request.form['email']
		password = request.form['password']
		# Check if account exists using MySQL
		cursor.execute('SELECT * FROM airline_staff WHERE username = %s AND password = %s', (email, password))
        # Fetch one record and return result
		account = cursor.fetchone()
		
		# If account exists in accounts table in out database
		if account:
		# Create session data, we can access this data in other routes
			name = account[2]
			airline_name = account[5]
			session['username'] = email
			session['name'] = name
			session['airline name'] = airline_name
			# Redirect to home page
			return redirect(url_for('staffhome'))

		else:
			# Account doesnt exist or username/password incorrect
			msg = 'The email address or password you entered is incorrect!'

	return render_template('loginstaff.html', msg=msg, data1=data1)



# homepage for logged in users
@app.route('/customer')
def cushome():
    # Check if user is loggedin
    if 'username' in session and 'cus' in session:
		#user = session["user"]
        # User is loggedin show them the home page
        return render_template('homecus.html', name=session['name'], username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('prelogin'))

@app.route('/agent')
def bookhome():
    # Check if user is loggedin
    if 'username' in session and 'id' in session:
        # User is loggedin show them the home page
        return render_template('homebook.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('prelogin'))

@app.route('/staff')
def staffhome():
    # Check if user is loggedin
    if 'username' in session and 'airline name' in session:
        # User is loggedin show them the home page
        return render_template('homestaff.html', name=session['name'], username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('prelogin'))




@app.route('/logout')
def logout():
   session.pop('username', None)
   session.pop('name', None)
   session.pop('airline name', None)
   session.pop('id', None)
   session.pop('cus', None)

   # Redirect to login page
   return redirect(url_for('prelogin'))


@app.route("/preregister")
def preregister():
	cursor = conn.cursor()
	cursor.execute('SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time FROM flight WHERE status = "DELAYED"')
	data1 = cursor.fetchall()

	return render_template('preregister.html', data1=data1)

@app.route("/customerreg", methods=['GET', 'POST'])
def customerreg():
	cursor = conn.cursor()
	msg = ''
	cursor.execute('SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time FROM flight WHERE status = "DELAYED"')
	data1 = cursor.fetchall()
	if request.method == 'POST':
		# Create variables for easy access
		email = request.form['email']
		name = request.form['name']
		password = request.form['password']
		building_number = request.form['building number']
		street = request.form['street']
		city = request.form['city']
		state = request.form['state']
		phone_number = request.form['phone number']
		passport_number = request.form['passport number']
		passport_expiration = request.form['passport expiration']
		passport_country = request.form['passport country']
		date_of_birth = request.form['date of birth']


		#Check if account exists using MySQL
		query = "SELECT * FROM customer WHERE email = \'{}\'"
		cursor.execute(query.format(email))
		#cursor.execute('SELECT * FROM accounts WHERE username = %s', (username))
		account = cursor.fetchone()
		# If account exists show error and validation checks
		if account:
			msg = 'Email already exists!'
		elif len(email) >= 50:
			msg = 'The email address should be less than 50 characters!'
		elif len(name) >= 50:
			msg = 'The name should be less than 50 characters!'
		elif len(password) >= 50:
			msg = 'The password should should be less than 50 characters!'
		elif len(building_number) >= 30:
			msg = 'The building number should be less than 30 characters!'
		elif len(street) >= 30:
			msg = 'The street should be less than 30 characters!'
		elif len(city) >= 30:
			msg = 'The city should be less thand 30 characters!'
		elif len(state) >= 30:
			msg = 'The state should be less thand 30 characters!'
		#type changed to varchar(11)
		elif len(phone_number) > 11:
			msg = 'The phone number should not exceed 11 characters!'
		elif len(passport_number) >= 30:
			msg = 'The passport number should be less than 30 characters!'
		elif len(passport_country) >= 50:
			msg = 'The passport country should be less than 50 characters!'

		else:
			# Account doesnt exists and the form data is valid, now insert new account into accounts table
			ins = "INSERT INTO customer VALUES( \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\')"
			cursor.execute(ins.format( email, name, password, building_number, street, city, state, phone_number, passport_number, passport_expiration, passport_country, date_of_birth))
			conn.commit()
			msg = 'You have successfully registered! Log in to view your homepage!'

	return render_template('registercus.html', msg=msg, data1=data1)	

@app.route("/bookreg", methods=['GET', 'POST'])
def bookreg():
	cursor = conn.cursor()
	cursor.execute('SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time FROM flight WHERE status = "DELAYED"')
	data1 = cursor.fetchall()
	msg = ''
	if request.method == 'POST':
		# Create variables for easy access
		email = request.form['email']
		password = request.form['password']
		booking_agent_id = request.form['booking agent id']

		#Check if account exists using MySQL
		query = "SELECT * FROM booking_agent WHERE email = \'{}\'"
		cursor.execute(query.format(email))
		#cursor.execute('SELECT * FROM accounts WHERE username = %s', (username))
		account = cursor.fetchone()
		# If account exists show error and validation checks
		if account:
			msg = 'Email already exists!'

		elif len(email) >= 50:
			msg = 'The email address should be less than 50 characters!'
		elif len(password) >= 50:
			msg = 'The password should should be less than 50 characters!'
		#type changed to varchar(11)
		elif len(booking_agent_id) > 11:
			msg = 'The booking agent id should not exceed 11 characters!'
		
		else:
			# Account doesnt exists and the form data is valid, now insert new account into accounts table
			ins = "INSERT INTO booking_agent VALUES( \'{}\', \'{}\', \'{}\')"
			cursor.execute(ins.format(email, password, booking_agent_id))
			conn.commit()
			msg = 'You have successfully registered! Log in to view your homepage!'

	return render_template('registerbook.html', msg=msg, data1=data1)	

@app.route("/staffreg", methods=['GET', 'POST'])
def staffreg():
	cursor = conn.cursor()
	cursor.execute('SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time FROM flight WHERE status = "DELAYED"')
	data1 = cursor.fetchall()
	msg = ''
	if request.method == 'POST':
		# Create variables for easy access
		email = request.form['email']
		password = request.form['password']
		first_name = request.form['first name']
		last_name = request.form['last name']
		date_of_birth = request.form['date of birth']
		airline_name = request.form['airline name']

		#Check if account exists using MySQL
		query = "SELECT * FROM airline_staff WHERE username = \'{}\'"
		cursor.execute(query.format(email))
		#cursor.execute('SELECT * FROM accounts WHERE username = %s', (username))
		account = cursor.fetchone()
		# If account exists show error and validation checks
		if account:
			msg = 'Email already exists!'
		elif len(email) >= 50:
			msg = 'The email address should be less than 50 characters!'
		elif len(first_name) >= 50:
			msg = 'The first name you enter should be less than 50 characters!'
		elif len(last_name) >= 50:
			msg = 'The last name you enter should should be less than 50 characters!'
		elif len(airline_name) >= 50:
			msg = 'The airline name should be less than 50 characters!'

		else:
			q = 'SELECT * FROM airline WHERE airline_name = \'{}\''
			cursor.execute(q.format(airline_name))
			data = cursor.fetchone()
			if not data:
				msg = "The airline does not exist!"
			else:
				# Account doesnt exists and the form data is valid, now insert new account into accounts table
				ins = "INSERT INTO airline_staff VALUES( \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\')"
				cursor.execute(ins.format( email, password, first_name, last_name, date_of_birth, airline_name))
				conn.commit()
				msg = 'You have successfully registered! Log in to view your homepage!'

	return render_template('registerstaff.html', msg=msg, data1=data1)	


@app.route("/about")
def about():
	cursor = conn.cursor()
	cursor.execute('SELECT airline_name, flight_num, departure_airport, arrival_airport, departure_time FROM flight WHERE status = "DELAYED"')
	data1 = cursor.fetchall()

	return render_template('about.html', title='About', data1=data1)







if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
