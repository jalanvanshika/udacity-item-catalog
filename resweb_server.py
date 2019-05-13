from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi

# import CRUD Operations from Lesson 1
from database_setup import Base, Restaurant, MenuItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create session and connect to DB
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


class webServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:

            if self.path.endswith("/delete"):
                resIDpath=self.path.split("/")[2]
                resname=session.query(Restaurant).filter_by(id=resIDpath).one()
                if resname !=[]:
                    self.send_response(200)
                    self.send_header('content-type', 'text/html')
                    self.end_headers()
                    output=""
                    output +="<html><body>"
                    output +="<h2>Are you sure about deleting %s ?</h2>" %resname.name
                    output += "<form method = 'POST' enctype='multipart/form-data' action = '/restaurants/%s/delete'>" %resIDpath
                    output += "<input type='submit' value='Delete'>"
                    output += "</body></html>"
                    self.wfile.write(output)
                    return



            if self.path.endswith("/edit"):
                resIDpath=self.path.split("/")[2]
                resname=session.query(Restaurant).filter_by(id=resIDpath).one()
                if resname !=[]:
                    self.send_response(200)
                    self.send_header('content-type', 'text/html')
                    self.end_headers()
                    output = ""
                    output += "<html><body>"
                    output += "<h1>%s</h1>" %resname.name
                    output += "<form method = 'POST' enctype='multipart/form-data' action = '/restaurants/%s/edit'>" %resIDpath
                    output += "<input name = 'newRestaurantName' type = 'text' placeholder = %s > " %resname.name                   
                    output += "<input type='submit' value='Rename'>"
                    output += "</form></body></html>"
                    self.wfile.write(output)
                    return





            # Objective 3 Step 2 - Create /restarants/new page
            if self.path.endswith("/restaurants/new"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ""
                output += "<html><body>"
                output += "<h1>Make a New Restaurant</h1>"
                output += "<form method = 'POST' enctype='multipart/form-data' action = '/restaurants/new'>"
                output += "<input name = 'newRestaurantName' type = 'text' placeholder = 'New Restaurant Name' > "
                output += "<input type='submit' value='Create'>"
                output += "</form></body></html>"
                self.wfile.write(output)
                return

            if self.path.endswith("/restaurants"):
                restaurants = session.query(Restaurant).all()
                output = ""
                # Objective 3 Step 1 - Create a Link to create a new menu item
                output += "<a href = '/restaurants/new' > Make a New Restaurant Here </a></br></br>"

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output += "<html><body>"
                for restaurant in restaurants:
                    output += restaurant.name
                    output += "</br>"
                    # Objective 2 -- Add Edit and Delete Links
                    output += "<a href ='restaurants/%s/edit'>Edit </a> " %restaurant.id
                    output += "</br>"
                    output += "<a href ='restaurants/%s/delete'> Delete </a>" %restaurant.id
                    output += "</br></br></br>"

                output += "</body></html>"
                self.wfile.write(output)
                return

        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    # Objective 3 Step 3- Make POST method
    def do_POST(self):
        try:

            if self.path.endswith("/delete"):
                resIDpath=self.path.split("/")[2]
                resname=session.query(Restaurant).filter_by(id=resIDpath).one()
                if resname !=[]:
                    session.delete(resname)
                    session.commit()

                    self.send_response(301)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Location', '/restaurants')
                    self.end_headers()

            if self.path.endswith("/edit"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('newRestaurantName')
                    resIDpath=self.path.split("/")[2]

                    resname=session.query(Restaurant).filter_by(id=resIDpath).one()
                    if resname !=[]:
                        resname.name=messagecontent[0]
                        session.add(resname)
                        session.commit()

                        self.send_response(301)
                        self.send_header('Content-type', 'text/html')
                        self.send_header('Location', '/restaurants')
                        self.end_headers()



            if self.path.endswith("/restaurants/new"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('newRestaurantName')

                    # Create new Restaurant Object
                    newRestaurant = Restaurant(name=messagecontent[0])
                    session.add(newRestaurant)
                    session.commit()

                    self.send_response(301)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Location', '/restaurants')
                    self.end_headers()

        except:
            pass  


def main():
    try:
        server = HTTPServer(('', 8080), webServerHandler)
        print 'Web server running... Open localhost:8080/restaurants in your browser'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    main()