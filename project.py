from flask import Flask

# import CRUD Operations from Lesson 1
from database_setup import Base, Restaurant, MenuItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create session and connect to DB
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

@app.route('/')
@app.route('/restaurants')

def HelloWorld():
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

	# restaurant = session.query(Restaurant).first()
	# items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
	# output = ''
	# for i in items:
	#     output += i.name
	#     output += '</br>'
	# return output

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)