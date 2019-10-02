# -*- coding: utf-8 -*-

from scripts import tabledef
from scripts import forms
from scripts import helpers
from flask import Flask, redirect, url_for, render_template, request, session
import json
import sys
import os
import stripe

stripe_keys = {
  'secret_key': os.environ['SECRET_KEY'],
  'publishable_key': os.environ['PUBLISHABLE_KEY']
}

stripe.api_key = stripe_keys['secret_key']

app = Flask(__name__)
app.secret_key = os.urandom(12)  # Generic key for dev purposes only
fxpairs = ["EURUSD",'GPBUSD','USDJPY','USDCHF']
timeframes = ['M5','M15','M30','H1','H4','D1']


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
    fxpairselected = fxpairs[0]
    timeframeselected = timeframes[0]

    #CHECK SUBSCRIPTION
    date="2019-09-30"
    return render_template('home.html', user=user, fxpairs=fxpairs, fxpairselected=fxpairselected,
                           timeframes=timeframes, timeframeselected=timeframeselected, date=date,
                           key=stripe_keys['publishable_key'])


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
            amount = 100

            charged = stripe.Charge.create(
                amount=amount,
                currency='usd',
                card=request.form['stripeToken'],
                description='Subscription Renewal'
            )

            if charged != None and "id" in charged:
                response = "2019-10-30"
            else:
                response = 'Failed Renewing'

        user = helpers.get_user()
        fxpairselected = fxpairs[0]
        timeframeselected = timeframes[0]



        return render_template('home.html', user=user, fxpairs=fxpairs, fxpairselected=fxpairselected,
                           timeframes=timeframes, timeframeselected=timeframeselected, date=response,
                           key=stripe_keys['publishable_key'])
    return redirect(url_for('login'))


# ======== Main ============================================================== #
if __name__ == "__main__":

    if os.environ['ENV'] != 'prod':
        host = os.getenv ('IP', '127.0.0.1')
        port = int (os.getenv ('PORT', 5000))
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.config['RELOAD'] = True
        app.config['DEBUG'] = True
        app.run(host=host, port=port)
