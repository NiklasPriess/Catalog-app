from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Items, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['email']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['email'])
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['email'], email=login_session[
                   'email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# Mainpage show all categories and items that were added last
@app.route('/')
@app.route('/category/')
def showCategories():
	user = login_session['user_id']
	categories = session.query(Category).order_by(asc(Category.name))
	latestitems = session.query(Items).order_by(desc(Items.id)).limit(10).all()
	return render_template('mainpage.html', categories=categories, latestitems=latestitems, user=user)


# Create a new category
@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    # if 'username' not in login_session:
    #     return redirect('/login')
    if request.method == 'POST':
        if request.form['name'] == "":
            flash('Please fill in a category name')
            return render_template('newcategory.html')
        newCategory = Category(
            name=request.form['name'], user_id=5) #user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newcategory.html')


# Edit a Category
@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['name'] == "" and request.form['submit'] == "submit":
            flash('Please fill in a category name')
            return render_template('editcategory.html', category=category)
        if request.form['submit'] == "submit":
            category.name = request.form['name']
            session.add(category)
            flash('Category %s successfully edited' % category.name)
            session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('editcategory.html', category=category)


# Delete a Category
@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Items).filter_by(category_id=category_id).all()
    print items
    if request.method == 'POST':
        if request.form['submit'] == "delete":
            session.delete(category)
            for item in items:
                session.delete(item)
            session.commit()
            flash('Category %s and associated items have been successfully deleted' % category.name)
        return redirect(url_for('showCategories'))
    else:
        return render_template('deletecategory.html', category=category, items=items)


# Create a new item for a category
@app.route('/category/items/new/', methods=['GET', 'POST'])
def newItem():
    # if 'username' not in login_session:
    #     return redirect('/login')
    categories = session.query(Category).all()
    if request.method == 'POST':
        if request.form['name'] == "" or request.form['description'] == "":
            flash('Please fill in a item name and a description')
            return render_template('newitem.html', categories=categories)
        category = request.form['category']
        category_id = session.query(Category).filter_by(name=category).one().id
        newItem = Items(
            name=request.form['name'], description=request.form['description'], category_id=category_id, user_id=5) #user_id=login_session['user_id'])
        session.add(newItem)
        flash('New Item %s Successfully Created' % newItem.name)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newitem.html', categories=categories)


# Edit a certain item
@app.route('/category/<int:category_id>/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    item = session.query(Items).filter_by(id=item_id).one()
    if category_id != item.category_id:
        return redirect(url_for('showCategories'))
    if request.method == 'POST':
        if (request.form['name'] == "" or request.form['description'] == "") and request.form['submit'] == "submit":
            flash('Please fill in a item name and a description')
            return render_template('edititem.html', item=item)
        if request.form['submit'] == "submit":
            item.name = request.form['name']
            item.description = request.form['description']
            session.add(item)
            flash('Item %s successfully edited' % item.name)
            session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('edititem.html', item=item)


# Delete a certain item
@app.route('/category/<int:category_id>/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Items).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['submit'] == "delete":
            session.delete(item)
            session.commit()
            flash('Item %s has been successfully deleted from category %s' % (item.name, category.name))
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteitem.html', category=category, item=item)


# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)