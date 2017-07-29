from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, abort
from sqlalchemy import create_engine, asc, desc, exists
from sqlalchemy.orm import sessionmaker, exc
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
from functools import wraps
import sys


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"


# Decoraters in order to check if post/comment exists, if the user is
# logged in and if the user owns the post/comment
def category_exists(function):
    @wraps(function)
    def wrapper(category_id, item_id, uid):
        try:
            category = session.query(Category).filter_by(id=category_id).one()
            return function(category_id, item_id, uid)
        except:
            return abort(404)
    return wrapper


def item_owned(function):
    @wraps(function)
    def wrapper(category_id, item_id, uid):
        if session.query(Items).filter_by(id=item_id).one().user_id == uid:
            return function(category_id, item_id)
        else:
            return abort(404)
    return wrapper


def item_exists(function):
    @wraps(function)
    def wrapper(category_id, item_id, uid):
        try:
            category = session.query(Category).filter_by(id=category_id).one()
            item = session.query(Items).filter_by(id=item_id).one()
            return function(category_id, item_id, uid)
        except:
            return abort(404)
    return wrapper


def category_owned(function):
    @wraps(function)
    def wrapper(category_id, item_id, uid):
        if session.query(Category).filter_by(id=category_id).one().user_id == uid:
            return function(category_id)
        else:
            return abort(404)
    return wrapper


def user_logged_in(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if 'category_id' in kwargs:
            category_id = kwargs['category_id']
        else:
            category_id = ""
        if 'item_id' in kwargs:
            item_id = kwargs['item_id']
        else:
            item_id = ""
        if 'user_id' in login_session:
            uid = login_session['user_id']
            return function(category_id, item_id, uid)
        else:
            return redirect("/login")

    return wrapper