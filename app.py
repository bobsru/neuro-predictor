# -*- coding: utf-8 -*-

from scripts import tabledef
from scripts import forms
from scripts import helpers
from flask import Flask, redirect, url_for, render_template, request, session
import json
import sys
import os
import stripe
from scripts import pred
from keras.models import load_model
import datetime
#import private_keys

stripe_keys = {
  'secret_key': os.environ['SECRET_KEY'],
  'publishable_key': os.environ['PUBLISHABLE_KEY']
}

stripe.api_key = stripe_keys['secret_key']

app = Flask(__name__)
app.secret_key = os.urandom(12)  # Generic key for dev purposes only
fxpairs = ["EURUSD",'GBPUSD','USDJPY','USDCHF']
#timeframes = ['M5','M15','M30','H1','H4','D1']
timeframes = ['D1']

model_name = './static/models/cnn_model_fx.h5'
model = load_model (model_name)
model._make_predict_function()

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
    if user.expiry:
        date = user.expiry
    else:
        date="0001-01-01"
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
        user = user = helpers.get_user()
        if user.expiry:
            if user.expiry >= datetime.datetime.now().date():
                if request.method == 'POST':
                    fxpair = request.form['fxpair']
                    tf = request.form['tf']
                    try:
                        resp = pred.make_prediction(fxpair, model)
                        if resp == "UP":
                            response = '<span class="tag is-success is-medium" id="feedback">UP</span>'
                        else:
                            response = '<span class="tag is-danger is-medium" id="feedback">DOWN</span>'
                    except:
                        response = '<span class="tag is-white is-medium" id="feedback">ERROR</span>'
                    return response
        else:
            return '<span class="tag is-white is-medium" id="feedback">NO SUBS</span>'

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
                response = datetime.datetime.now() + datetime.timedelta(days=30)
                response = response.date()
                #save to database
                helpers.change_user(expiry=response)
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
    else:
        app.run(host="0.0.0.0", port=80)
