# -*- coding: utf-8 -*-

from scripts import tabledef
from scripts import forms
from scripts import helpers
from flask import Flask, redirect, url_for, render_template, request, session
import json
import sys
import os

app = Flask(__name__)
app.secret_key = os.urandom(12)  # Generic key for dev purposes only

# Heroku
#from flask_heroku import Heroku
#heroku = Heroku(app)

# ======== Routing =========================================================== #
# -------- Login ------------------------------------------------------------- #
@app.route('/', methods=['GET', 'POST'])
def login():
    if not session.get('logged_in'):
        form = forms.LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username'].lower()
            password = request.form['password']
            if form.validate():
                if helpers.credentials_valid(username, password):
                    session['logged_in'] = True
                    session['username'] = username
                    return json.dumps({'status': 'Login successful'})
                return json.dumps({'status': 'Invalid user/pass'})
            return json.dumps({'status': 'Both fields required'})
        return render_template('login.html', form=form)
    user = helpers.get_user()
    fxpairs = ["EURUSD",'GPBUSD','USDJPY','USDCHF']
    timeframes = ['M5','M15','M30','H1','H4','D1']



    fxpairselected = fxpairs[0]
    timeframeselected = timeframes[0]

    #CHECK SUBSCRIPTION
    date="01-12-2019"
    return render_template('home.html', user=user, fxpairs=fxpairs, fxpairselected=fxpairselected,
                           timeframes=timeframes, timeframeselected=timeframeselected, date=date)


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))


# -------- Signup ---------------------------------------------------------- #
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if not session.get('logged_in'):
        form = forms.LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username'].lower()
            password = helpers.hash_password(request.form['password'])
            email = request.form['email']
            if form.validate():
                if not helpers.username_taken(username):
                    helpers.add_user(username, password, email)
                    session['logged_in'] = True
                    session['username'] = username
                    return json.dumps({'status': 'Signup successful'})
                return json.dumps({'status': 'Username taken'})
            return json.dumps({'status': 'User/Pass required'})
        return render_template('login.html', form=form)
    return redirect(url_for('login'))


# -------- Settings ---------------------------------------------------------- #
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('logged_in'):
        if request.method == 'POST':
            password = request.form['password']
            if password != "":
                password = helpers.hash_password(password)
            email = request.form['email']
            helpers.change_user(password=password, email=email)
            return json.dumps({'status': 'Saved'})
        user = helpers.get_user()
        return render_template('settings.html', user=user)
    return redirect(url_for('login'))

# -------- Prediction ---------------------------------------------------------- #
@app.route('/predict', methods=['POST'])
def predict():
    if session.get('logged_in'):
        if request.method == 'POST':
            fxpair = request.form['fxpair']
            tf = request.form['tf']

            # HERE"S THE SNIPPET OF PREDICTION

            response = "UP"
            return response

    return redirect(url_for('login'))

# -------- Prediction ---------------------------------------------------------- #
@app.route('/subscription', methods=['POST'])
def subscription():
    if session.get('logged_in'):
        if request.method == 'POST':

            #HERE"S THE SNIPPET OF CHECKING THE SUBSCRIPTION DATE

            response = "02-12-2019"
            return response

    return redirect(url_for('login'))


# ======== Main ============================================================== #
if __name__ == "__main__":
    host = os.getenv ('IP', '127.0.0.10')
    port = int (os.getenv ('PORT', 5000))
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['RELOAD'] = True
    app.config['DEBUG'] = True
    #app.config['SERVER_NAME'] = 'neuro.onrender.com'
    app.run(host=host, port=port)
