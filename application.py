from flask import Flask, render_template, \
    request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc, desc, join, exc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
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


engine = create_engine('sqlite:///catalog.db?check_same_thread=False')
Base.metadata.bind = engine


DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data.decode('utf-8')

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
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

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
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; \
        border-radius: 150px;-webkit-border-radius: \
        150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
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
    except exc.SQLAlchemyError:
        return None


@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:

        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/category/JSON')
def categoryJSON():
    category = session.query(Category).all()
    return jsonify(Category=[i.serialize for i in category])


@app.route('/category/<int:category_id>/items/JSON')
def categoryItemJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(
        category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/category/<int:category_id>/item/<int:item_id>/JSON')
def itemItemJSON(category_id, item_id):
    Item_Item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item_Item=Item_Item.serialize)


@app.route('/')
@app.route('/categories/')
def showMain():
    categories = session.query(Category).order_by(asc(Category.name)).all()
    latests = session.query(Item).join(Category).filter(
        Item.category_id == Category.id).order_by(
        desc(Item.created_date)).limit(10)
    if 'username' not in login_session:
        return render_template(
            'public_main.html', categories=categories, latests=latests
        )
    else:
        return render_template(
            'categories.html', categories=categories,
            latests=latests, user=login_session['email']
        )


@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showMain'))
    else:
        return render_template(
            'new_category.html', user=login_session['email']
        )


@app.route('/category/<int:category_id>')
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category.id)
    creator = getUserInfo(category.user_id)
    if 'username' not in login_session:
        return render_template(
            'public_categories.html', category=category, items=items
        )
    elif creator.id == login_session['user_id']:
        return render_template(
            'category_items.html', category=category, items=items,
            is_creator=True, user=login_session['email']
        )
    else:
        return render_template(
            'category_items.html', category=category,
            items=items, is_creator=False, user=login_session['email']
        )


@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    toEditCategory = session.query(Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if toEditCategory.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are \
            not authorized to edit this category. Please create \
            your own category in order to \
            edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            toEditCategory.name = request.form['name']
            flash('Category Successfully Edited %s' % toEditCategory.name)
            return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template(
            'edit_category.html', category=toEditCategory,
            user=login_session['email']
        )


@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    if categoryToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are \
            not authorized to delete this category. Please create \
            your own category in order to delete.');}</script> \
            <body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(categoryToDelete)
        flash('%s Successfully Deleted' % categoryToDelete.name)
        session.commit()
        return redirect(url_for('showMain'))
    else:
        return render_template(
            'delete_category.html', category=categoryToDelete,
            user=login_session['email']
        )


@app.route('/item/<int:item_id>/')
def showItem(item_id):
    # category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    creator = getUserInfo(item.user_id)

    if 'username' not in login_session:
        return render_template('public_item.html', item=item, creator=creator)
    elif creator.id == login_session['user_id']:
        return render_template(
            'item.html', item=item, creator=creator,
            is_creator=True, user=login_session['email']
        )
    else:
        return render_template(
            'item.html', item=item, creator=creator, is_creator=False
        )


@app.route('/category/<int:category_id>/item/new/', methods=['GET', 'POST'])
def newItem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are \
         not authorized to add items to this category. Please \
         create your own category in order to add items.');}\
         </script><body onload='myFunction()''>"
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            category_id=category_id,
            user_id=category.user_id)
        session.add(newItem)
        session.commit()
        flash('New Item %s Item Successfully Created' % (newItem.name))

        return redirect(url_for('showItem', item_id=newItem.id))
    else:
        return render_template(
            'new_item.html', category_id=category_id,
            user=login_session['email']
        )


@app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id):
    if 'username' not in login_session:
        return redirect('/login')
    toEditItem = session.query(Item).filter_by(id=item_id).one()
    # category = session.query(Category).filter_by(id=category_id).one()
    if login_session['user_id'] != toEditItem.user_id:
        return "<script>function myFunction() {alert('You are \
        not authorized to edit items to this category. Please \
        create your own category in order to edit items.');}\
        </script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            toEditItem.name = request.form['name']
        if request.form['description']:
            toEditItem.description = request.form['description']
        if request.form['price']:
            toEditItem.price = request.form['price']
        session.add(toEditItem)
        session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('showItem', item_id=item_id))
    else:
        return render_template(
            'edit_item.html', item=toEditItem, user=login_session['email'])


@app.route('/item/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(item_id):
    if 'username' not in login_session:
        return redirect('/login')
    # category = session.query(Category).filter_by(id=category_id).one()
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if login_session['user_id'] != itemToDelete.user_id:
        return "<script>function myFunction() {alert('You are \
        not authorized to delete items to this category. Please \
        create your own category in order to delete items.');} \
        </script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for(
            'showCategory', category_id=itemToDelete.category_id)
        )
    else:
        return render_template(
            'delete_item.html', item=itemToDelete,
            user=login_session['email']
        )


@app.route('/disconnect')
def disconnect():
        gdisconnect()
        flash("You have successfully been logged out.")
        return redirect(url_for('showMain'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
