from flask import Flask , render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

from flask import session as login_session
import random, string

app = Flask(__name__)

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html')


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token


    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"



@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    menuItem = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(MenuItem=menuItem.serialize)


@app.route('/')
def defaultMenu():
    restaurants=session.query(Restaurant).all()
    menus=session.query(MenuItem).all()
    output=""
    for restaurant in restaurants:
        output+="<h2>"
        output += restaurant.name
        output+="</h2>"
        output += "</br>"
        for menu in menus:
            if menu.restaurant_id==restaurant.id:
                output+=menu.name
                output+="</br>"
                output+=menu.price
                output+="</br>"
    return output

@app.route('/restaurants/<int:res_id>/menu')
def restaurantMenu(res_id):
    restaurant = session.query(Restaurant).filter_by(id=res_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    return render_template('menu.html', restaurant=restaurant, items=items, restaurant_id=res_id)


@app.route('/restaurants/<int:res_id>/new', methods=['GET','POST'])
def newMenuItem(res_id):
    if request.method=='POST':
        newItem=MenuItem(name=request.form['name'], restaurant_id= res_id)
        session.add(newItem)
        session.commit()
        flash("new menu item created!")
        return redirect(url_for('restaurantMenu',res_id=res_id))

    else:
        return render_template('newmenu.html', restaurant_id=res_id)

@app.route('/restaurants/<int:res_id>/<int:menu_id>/edit', methods=['GET','POST'])
def editMenuItem(res_id, menu_id):
    editItem = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editItem.name = request.form['name']
        session.add(editItem)
        session.commit()
        flash("Item has been edited!")
        return redirect(url_for('restaurantMenu', res_id=res_id))
    else:
        return render_template('editmenu.html',  editItem= editItem)

@app.route('/restaurants/<int:res_id>/<int:menu_id>/delete', methods=['GET','POST'])
def deleteMenuItem(res_id, menu_id):
    itemtoDelete = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        session.delete(itemtoDelete)
        session.commit()
        flash("Item has been deleted!")
        return redirect(url_for('restaurantMenu',res_id=res_id))
    else:
        return render_template('deletemenu.html', item=itemtoDelete)
    

# @app.route('/restaurant/<int:restaurant_id>/new/')
# def newMenuItem(restaurant_id):
#     return "page to create a new menu item. Task 1 complete!"

# # Task 2: Create route for editMenuItem function here


# @app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/edit/')
# def editMenuItem(restaurant_id, menu_id):
#     return "page to edit a menu item. Task 2 complete!"

# # Task 3: Create a route for deleteMenuItem function here


# @app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/delete/')
# def deleteMenuItem(restaurant_id, menu_id):
#     return "page to delete a menu item. Task 3 complete!"



if __name__ == '__main__':
    app.secret_key="super_secret_key"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
