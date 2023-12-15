#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json, sys, datetime
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database (already done in config.py)

# create a Migrate object to generate migration file
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# create a many-to-many relationship table between Venue and Genre, by creating a new table "venue_genres_table"
# Notice that: this Association Table should be placed ABOVE the Venue class, so that the Venue class can reference it, or else it will throw an error "venue_genres_table not defined"
venue_genres_table = db.Table('venue_genres_table',
                              db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True),
                              db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True))

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
# create a many-to-many relationship table between Venue and Artist, by creating a new table "shows_table"
# shows_table = db.Table('shows_table',
#                        db.Column('id', db.Integer, primary_key=True),
#                        db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), nullable=False),
#                        db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), nullable=False),
#                        db.Column('start_time', db.DateTime, nullable=False, default=datetime.now()))

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String())
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String())
    genres = db.relationship('Genre', secondary=venue_genres_table, backref=db.backref('venues', lazy=True, cascade='all, delete'))
    shows = db.relationship('Show', backref='venue', lazy=True, cascade='all, delete')
    
    def __repr__(self):
      return f'<Venue ID: {self.id}, name: {self.name}, city: {self.city}, state: {self.state}, address: {self.address}, phone: {self.phone}, image_link: {self.image_link}, facebook_link: {self.facebook_link}, website: {self.website}, seeking_talent: {self.seeking_talent}, seeking_description: {self.seeking_description}, genres: {self.genres}, shows: {self.shows}>'

# create a many-to-many relationship table between Artist and Genre, by creating a new table "artist_genres_table"
# Notice that: this Association Table should be placed ABOVE the Artist class, so that the Artist class can reference it, or else it will throw an error "artist_genres_table not defined"
artist_genres_table = db.Table('artist_genres_table', 
                               db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True),
                               db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True))

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120), nullable=False)
    #genres = db.Column(db.String(120)) # remove this line, since we have created a many-to-many relationship table between Artist and Genre
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String())
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String())
    genres = db.relationship('Genre', secondary=artist_genres_table, backref=db.backref('artists', lazy=True, cascade='all, delete'))
    # venues = db.relationship('Venue', secondary=shows_table, backref=db.backref('artists', lazy=True))
    shows = db.relationship('Show', backref='artist', lazy=True, cascade='all, delete')
    
    def __repr__(self):
      return f'<Artist ID: {self.id}, name: {self.name}, city: {self.city}, state: {self.state}, phone: {self.phone}, image_link: {self.image_link}, facebook_link: {self.facebook_link}, website: {self.website}, seeking_venue: {self.seeking_venue}, seeking_description: {self.seeking_description}, genres: {self.genres}, shows: {self.shows}>'
# create Genre Model class (child to Artist, and Venue model class), to implement many-to-many relationship

# Because Show is an Entity (a Venue Owner can Post a Show), so we need to create a Model class for Show. Not create the Association Table "shows_table", which is just like a "virtual table" that serves only for representing the many-to-many relationship between Artist, Venue
class Show(db.Model):
  __tablename__ = 'Show'
  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False, default=datetime.now())
  
  def __repr__(self):
    return f'<Show ID: {self.id}, venue_id: {self.venue_id}, artist_id: {self.artist_id}, start_time: {self.start_time}>'

class Genre(db.Model):
  __tablename__ = 'Genre'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String())
  
  def __repr__(self):
    return f'<Genre ID: {self.id}, name: {self.name}>'
  

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  # data=[{
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "venues": [{
  #     "id": 1,
  #     "name": "The Musical Hop",
  #     "num_upcoming_shows": 0,
  #   }, {
  #     "id": 3,
  #     "name": "Park Square Live Music & Coffee",
  #     "num_upcoming_shows": 1,
  #   }]
  # }, {
  #   "city": "New York",
  #   "state": "NY",
  #   "venues": [{
  #     "id": 2,
  #     "name": "The Dueling Pianos Bar",
  #     "num_upcoming_shows": 0,
  #   }]
  # }]
  data = []
  list_of_tuples_containing_city_and_state = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state).all()
  print("list_of_tuples_containing_city_and_state: ", list_of_tuples_containing_city_and_state)
  for each_tuple in list_of_tuples_containing_city_and_state:
    city = each_tuple[0]
    state = each_tuple[1]
    # get the list of venues for each city and state (group by each unique (city and state))
    list_of_venues = Venue.query.filter_by(city=city, state=state).all()
    print("list_of_venues: ", list_of_venues)
    venue_list = []
    for each_venue in list_of_venues:
      number_of_upcoming_shows = 0
      # get the list of shows for each venue. (we can not use Venue.shows, because Venue.shows is a relationship, not a list)
      list_of_shows = each_venue.shows # access the "shows" attribute of Venue object, just like OOP
      print("list_of_shows: ", list_of_shows)
      for each_show in list_of_shows:
        # check if the show is upcoming or past, by comparing the show.start_time with current time
        if each_show.start_time >= datetime.now():
          number_of_upcoming_shows += 1
      print("number_of_upcoming_shows: ", number_of_upcoming_shows)
      # append the "customized" object, into "venue_list"
      venue_list.append({
        "id": each_venue.id,
        "name": each_venue.name,
        "num_upcoming_shows": number_of_upcoming_shows
      })
      print("venue_list: ", venue_list)
      # append the "customized" object, into "data", which will be rendered on the pages/venues.html to display the Venue, grouped by (city, and state), and their upcomming shows for that Venue
    data.append({
      "city": city,
      "state": state,
      "venues": venue_list
    })
    print("data: ", data)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  # response={
  #   "count": 1,
  #   "data": [{
  #     "id": 2,
  #     "name": "The Dueling Pianos Bar",
  #     "num_upcoming_shows": 0,
  #   }]
  # }
  search_term = request.form.get('search_term', '').strip() # get the search term from the form, and remove the leading and trailing spaces. if we don't use the second argument in request.form.get('search_term', ''), then it will return None, instead of empty string ''
  print("search_term: ", search_term)
  # if the user just enters whitespace, then redirect to the venues page
  if search_term == '':
    #flash('Please enter a search term!')
    return redirect(url_for('venues'))
  list_of_found_venues = Venue.query.filter(Venue.name.like('%' + search_term + '%')).all() # for CASE-INSENSITIVE search, use Venue.name.ilike('%' + search_term + '%')
  print("list_of_found_venues: ", list_of_found_venues)
  number_of_found_venue = len(list_of_found_venues)
  print("number_of_found_venue: ", number_of_found_venue)
  if number_of_found_venue == 0:
    flash('No results found for: ' + search_term)
    return redirect(url_for('venues'))
  else:
    list_of_customized_found_venues = []
    customized_found_venue = {}
    for each_found_venue in list_of_found_venues:
      # get the list of all upcoming shows for each found venue, by filtering the Show table by venue_id, and start_time >= current time
      list_of_all_upcoming_shows = Show.query.filter(Show.venue_id == each_found_venue.id).filter(Show.start_time >= datetime.now()).all()
      # create a "customized_found_venue" dictionary for each found venue
      customized_found_venue = {
        'id': each_found_venue.id,
        'name': each_found_venue.name,
        'num_upcoming_shows': len(list_of_all_upcoming_shows)
      }
      # append the "customized_found_venue" dictionary to the list_of_customized_found_venues in each iteration (for each each_venue)
      list_of_customized_found_venues.append(customized_found_venue)
    # after the for loop, we will have a list of "customized_found_venue" dictionaries, each of which contains the information of a found venue, and the number of upcoming shows for that venue
    response = {
      'count': number_of_found_venue,
      'data': list_of_customized_found_venues
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  # data1={
  #   "id": 1,
  #   "name": "The Musical Hop",
  #   "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
  #   "address": "1015 Folsom Street",
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "123-123-1234",
  #   "website": "https://www.themusicalhop.com",
  #   "facebook_link": "https://www.facebook.com/TheMusicalHop",
  #   "seeking_talent": True,
  #   "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
  #   "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
  #   "past_shows": [{
  #     "artist_id": 4,
  #     "artist_name": "Guns N Petals",
  #     "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #     "start_time": "2019-05-21T21:30:00.000Z"
  #   }],
  #   "upcoming_shows": [],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 0,
  # }
  # data2={
  #   "id": 2,
  #   "name": "The Dueling Pianos Bar",
  #   "genres": ["Classical", "R&B", "Hip-Hop"],
  #   "address": "335 Delancey Street",
  #   "city": "New York",
  #   "state": "NY",
  #   "phone": "914-003-1132",
  #   "website": "https://www.theduelingpianos.com",
  #   "facebook_link": "https://www.facebook.com/theduelingpianos",
  #   "seeking_talent": False,
  #   "image_link": "https://images.unsplash.com/photo-1497032205916-ac775f0649ae?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=750&q=80",
  #   "past_shows": [],
  #   "upcoming_shows": [],
  #   "past_shows_count": 0,
  #   "upcoming_shows_count": 0,
  # }
  # data3={
  #   "id": 3,
  #   "name": "Park Square Live Music & Coffee",
  #   "genres": ["Rock n Roll", "Jazz", "Classical", "Folk"],
  #   "address": "34 Whiskey Moore Ave",
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "415-000-1234",
  #   "website": "https://www.parksquarelivemusicandcoffee.com",
  #   "facebook_link": "https://www.facebook.com/ParkSquareLiveMusicAndCoffee",
  #   "seeking_talent": False,
  #   "image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #   "past_shows": [{
  #     "artist_id": 5,
  #     "artist_name": "Matt Quevedo",
  #     "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #     "start_time": "2019-06-15T23:00:00.000Z"
  #   }],
  #   "upcoming_shows": [{
  #     "artist_id": 6,
  #     "artist_name": "The Wild Sax Band",
  #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #     "start_time": "2035-04-01T20:00:00.000Z"
  #   }, {
  #     "artist_id": 6,
  #     "artist_name": "The Wild Sax Band",
  #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #     "start_time": "2035-04-08T20:00:00.000Z"
  #   }, {
  #     "artist_id": 6,
  #     "artist_name": "The Wild Sax Band",
  #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #     "start_time": "2035-04-15T20:00:00.000Z"
  #   }],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 1,
  # }
  list_of_customized_object = []
  list_of_all_venues = db.session.query(Venue).all()
  for each_venue in list_of_all_venues:
    list_of_all_shows = each_venue.shows
    past_shows = []
    upcoming_shows = []
    for each_show in list_of_all_shows:
      if each_show.start_time >= datetime.now():
        upcoming_shows.append({
          "artist_id": each_show.artist_id,
          "artist_name": each_show.artist.name,
          "artist_image_link": each_show.artist.image_link,
          "start_time": each_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })
      else:
        past_shows.append({
          "artist_id": each_show.artist_id,
          "artist_name": each_show.artist.name,
          "artist_image_link": each_show.artist.image_link,
          "start_time": each_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    customized_object = {
      'id': each_venue.id,
      'name': each_venue.name,
      'genres': [each_genre.name for each_genre in each_venue.genres],
      'address': each_venue.address,
      'city': each_venue.city,
      'state': each_venue.state,
      'phone': each_venue.phone,
      'website': each_venue.website,
      'facebook_link': each_venue.facebook_link,
      'seeking_talent': each_venue.seeking_talent,
      'seeking_description': each_venue.seeking_description,
      'image_link': each_venue.image_link,
      'past_shows': past_shows,
      'upcoming_shows': upcoming_shows,
      'past_shows_count': len(past_shows),
      'upcoming_shows_count': len(upcoming_shows)
    }
    list_of_customized_object.append(customized_object)
  data = list(filter(lambda d: d['id'] == venue_id, list_of_customized_object))[0]
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm(request.form)
  venue = Venue(name=form.name.data, city=form.city.data, state=form.state.data, address=form.address.data, phone=form.phone.data, image_link=form.image_link.data, facebook_link=form.facebook_link.data, website=form.website_link.data, seeking_talent=form.seeking_talent.data, seeking_description=form.seeking_description.data)
  print("venue: ", venue)
  # get the list of genres from the form
  genre_name_list = request.form.getlist('genres')
  # print("genre_list type: ", type(genre_name_list))
  # print("genre_list data: ", genre_name_list)
  # print("form.genres.data: ", form.genres.data)
  print("genre_name_list: ", request.form.getlist('genres'))


  for each_genre_name in genre_name_list:
    # create a new Genre object
    genre = Genre(name=each_genre_name)
    # append the new Genre object to the venue.genres list
    venue.genres.append(genre)
  print("venue.genres: ", venue.genres)
  print('Venue After adding genres: ', venue)
  if not form.validate():
    flash(form.errors)
    return redirect(url_for('create_venue_submission'))
  try: 
    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    print(sys.exc_info())
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  finally:
    db.session.close()
  return redirect(url_for('pages/home.html'))

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + venue_id + ' could not be deleted.')
    abort(500)
  else:
    flash('Venue ' + venue_id + ' was successfully deleted!')
  return redirect(url_for('index'))

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  # data=[{
  #   "id": 4,
  #   "name": "Guns N Petals",
  # }, {
  #   "id": 5,
  #   "name": "Matt Quevedo",
  # }, {
  #   "id": 6,
  #   "name": "The Wild Sax Band",
  # }]
  data = []
  list_of_artists = db.session.query(Artist).all()
  for each_artist in list_of_artists:
    data.append({
      'id' : each_artist.id,
      'name' : each_artist.name
    })
  print("list_of_artists: ", data)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response={
    "count": 1,
    "data": [{
      "id": 4,
      "name": "Guns N Petals",
      "num_upcoming_shows": 0,
    }]
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  # data1={
  #   "id": 4,
  #   "name": "Guns N Petals",
  #   "genres": ["Rock n Roll"],
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "326-123-5000",
  #   "website": "https://www.gunsnpetalsband.com",
  #   "facebook_link": "https://www.facebook.com/GunsNPetals",
  #   "seeking_venue": True,
  #   "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
  #   "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #   "past_shows": [{
  #     "venue_id": 1,
  #     "venue_name": "The Musical Hop",
  #     "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
  #     "start_time": "2019-05-21T21:30:00.000Z"
  #   }],
  #   "upcoming_shows": [],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 0,
  # }
  # data2={
  #   "id": 5,
  #   "name": "Matt Quevedo",
  #   "genres": ["Jazz"],
  #   "city": "New York",
  #   "state": "NY",
  #   "phone": "300-400-5000",
  #   "facebook_link": "https://www.facebook.com/mattquevedo923251523",
  #   "seeking_venue": False,
  #   "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #   "past_shows": [{
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2019-06-15T23:00:00.000Z"
  #   }],
  #   "upcoming_shows": [],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 0,
  # }
  # data3={
  #   "id": 6,
  #   "name": "The Wild Sax Band",
  #   "genres": ["Jazz", "Classical"],
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "432-325-5432",
  #   "seeking_venue": False,
  #   "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "past_shows": [],
  #   "upcoming_shows": [{
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2035-04-01T20:00:00.000Z"
  #   }, {
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2035-04-08T20:00:00.000Z"
  #   }, {
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2035-04-15T20:00:00.000Z"
  #   }],
  #   "past_shows_count": 0,
  #   "upcoming_shows_count": 3,
  # }
  
  # create a list of "customized_data" dictionaries, each of which is a Dictionary that contains {some information of an artist, and their shows (past and upcoming), and the number of past and upcoming shows}
  list_of_customized_data = []
  # get the list of all artists
  list_of_all_artists = db.session.query(Artist).all() # the same as: Artist.query.all()
  for each_artist in list_of_all_artists:
    # get the list of all shows for an artist
    list_of_all_shows = each_artist.shows
    past_shows = []
    upcoming_shows = []
    for each_show in list_of_all_shows:
      # check if the show is upcoming or past, by comparing the show.start_time with current time
      if each_show.start_time >= datetime.now():
        upcoming_shows.append({
          "venue_id": each_show.venue_id,
          "venue_name": each_show.venue.name,
          "venue_image_link": each_show.venue.image_link,
          "start_time": each_show.start_time.strftime('%Y-%m-%d %H:%M:%S') # convert the datetime object to string, so that it can be displayed on the page. An example of this format: "2019-05-21 21:30:00"
        })
      else:
        past_shows.append({
          "venue_id": each_show.venue_id,
          "venue_name": each_show.venue.name,
          "venue_image_link": each_show.venue.image_link,
          "start_time": each_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    # create a "customized_data" dictionary for each artist in the for loop
    customized_data = {
      'id': each_artist.id,
      'name': each_artist.name,
      'genres': [each_genre.name for each_genre in each_artist.genres], # list comprehension, to get the list of Genres' names of each artist
      'city': each_artist.city,
      'state': each_artist.state,
      'phone': each_artist.phone,
      'website': each_artist.website,
      'facebook_link': each_artist.facebook_link,
      'seeking_venue': each_artist.seeking_venue,
      'seeking_description': each_artist.seeking_description,
      'image_link': each_artist.image_link,
      'past_shows': past_shows,
      'upcoming_shows': upcoming_shows,
      'past_shows_count': len(past_shows), # get the number of past shows of each artist, by getting the length of the list of past shows
      'upcoming_shows_count': len(upcoming_shows) # get the number of upcoming shows of each artist, by getting the length of the list of upcoming shows
    }
    list_of_customized_data.append(customized_data)
  # get the data of a particular artist (with a particular artist_id) to display on the page. In this case, we just need to get the first element of the list_of_customized_data, because we have already filtered the list_of_customized_data by artist_id
  data = list(filter(lambda d: d['id'] == artist_id, list_of_customized_data))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  # artist={
  #   "id": 4,
  #   "name": "Guns N Petals",
  #   "genres": ["Rock n Roll"],
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "326-123-5000",
  #   "website": "https://www.gunsnpetalsband.com",
  #   "facebook_link": "https://www.facebook.com/GunsNPetals",
  #   "seeking_venue": True,
  #   "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
  #   "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  # }
  # TODO: populate form with fields from artist with ID <artist_id>
  artist = Artist.query.filter_by(id=artist_id).first()
  list_of_genres_object = artist.genres # get the list of Genres Object of each artist
  list_of_genres_name = [each_genre_object.name for each_genre_object in list_of_genres_object]
  form.genres.data = list_of_genres_name # apply Server-Side Rendering to prepopulate ONLY the "genres" field (because the "genres" field is a multiple select field, and we can't prepopulate it using Client-side Rendering in the edit_artist.html)
  # the rest of the fields will be prepopulated using Client-side Rendering in the edit_artist.html
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  artist = Artist.query.get(artist_id)
  artist.name = form.name.data
  artist.city = form.city.data
  artist.state = form.state.data
  artist.phone = form.phone.data
  artist.image_link = form.image_link.data
  artist.facebook_link = form.facebook_link.data
  artist.website = form.website_link.data
  artist.seeking_venue = form.seeking_venue.data
  artist.seeking_description = form.seeking_description.data
  # clear the list of current Genres of that Artist
  artist.genres = []
  #list_of_updated_genres_name = request.form.getlist('genres') # "form.genres.data" is equivalent to "request.form.getlist('genres')", which returns the list of Genres' names that the user has selected on the form
  #list_of_updated_genres_object = form.genres.data
  if not form.validate:
    flash(form.errors)
    return redirect(url_for('edit_artist_submission', artist_id=artist_id))
  list_of_updated_genres_name = form.genres.data # return the list of Genres' names that the user has selected on the form
  # for each_update_genre_object in list_of_updated_genres_object:
  #   list_of_updated_genres_name.append(each_update_genre_object.name)
  for each_updated_genre_name in list_of_updated_genres_name:
    genre = Genre(name=each_updated_genre_name)
    artist.genres.append(genre)
  try:
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  # venue={
  #   "id": 1,
  #   "name": "The Musical Hop",
  #   "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
  #   "address": "1015 Folsom Street",
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "123-123-1234",
  #   "website": "https://www.themusicalhop.com",
  #   "facebook_link": "https://www.facebook.com/TheMusicalHop",
  #   "seeking_talent": True,
  #   "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
  #   "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  # }
  # TODO: populate form with values from venue with ID <venue_id>
  # get the current data of a particular Venue (with a particular venue_id) to display on the edit page, for user to edit their existing data
  venue = db.session.query(Venue).filter(Venue.id==venue_id).all()[0] # .all()[0] is equivalent to .first()

  list_of_genres_object = venue.genres # get the list of Genres Object of each venue
  list_of_genres_name = [each_genre_object.name for each_genre_object in list_of_genres_object] # list comprehension, to get the list of Genres' names of each venue
  # list_of_genres_name = []
  # for each_genre_object in list_of_genres_object:
  #   list_of_genres_name.append(each_genre_object.name)
  
  # implement Server-side Rendering, by pre-populating the form with the existing data of the Venue in the server, and send the pre-populated form to the client (forms/edit_venue.html), so that the client can edit the existing data of the Venue
  form.name.data = venue.name
  form.city.data = venue.city
  form.state.data = venue.state
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.image_link.data = venue.image_link
  form.facebook_link.data = venue.facebook_link
  form.website_link.data = venue.website
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.genres.data = list_of_genres_name
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)
  venue = Venue.query.get(venue_id)
  print('venue before update: ', venue)
  venue.name = form.name.data
  print('venue.name: ', form.name.data)
  venue.city = form.city.data
  venue.state = form.state.data
  venue.address = form.address.data
  venue.phone = form.phone.data
  venue.image_link = form.image_link.data
  venue.facebook_link = form.facebook_link.data
  venue.website = form.website_link.data
  venue.seeking_talent = form.seeking_talent.data
  venue.seeking_description = form.seeking_description.data
  
  # This logic for Update the Genres of a Venue is that: if the updated Genre is not in the Genre list of that Venue, then add that Genre to the Genre list of that Venue. If the updated Genre is already in the Genre list of that Venue, then do nothing (keep what is existing, add what is new)
  # list_of_current_genres_object = venue.genres
  # list_of_current_genreName = []
  # for each_genre_object in list_of_current_genres_object:
  #   list_of_current_genreName.append(each_genre_object.name)
  # list_of_updated_genres_name = request.form.getlist('genres')
  # for each_updated_genre_name in list_of_updated_genres_name:
  #   if not each_updated_genre_name in list_of_current_genreName:
  #     genre = Genre(name=each_updated_genre_name)
  #     venue.genres.append(genre)
  
  # this logic for Update the Genres of a Venue is that: clear the list of current Genres of that Venue, and then add the updated Genres to the list of Genres of that Venue (clear what is existing, add what is new)
  list_of_updated_genres_name = request.form.getlist('genres')
  # Validate the form, by checking if the form is valid or not (basing on the constraints of the VenueForm class in forms.py)
  if not form.validate():
    flash(form.errors)
    return redirect(url_for('edit_venue_submission', venue_id=venue_id))
  # clear the list of current Genres of that Venue
  venue.genres.clear()
  for each_updated_genre_name in list_of_updated_genres_name:
    genre = Genre(name=each_updated_genre_name)
    venue.genres.append(genre)
  print(f'updated genres of this Venue, with venue_id = {venue_id}: ', venue.genres)
  print('updated venue: ', venue)
  
  try:
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
  finally:
    db.session.close()
    
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form)
  artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data, phone=form.phone.data, image_link=form.image_link.data, facebook_link=form.facebook_link.data, website=form.website_link.data, seeking_venue=form.seeking_venue.data, seeking_description=form.seeking_description.data)
  genre_name_list = request.form.getlist('genres')
  for each_genre_name in genre_name_list:
    # create a new Genre object
    genre = Genre(name=each_genre_name)
    # append the new Genre object to the venue.genres list
    artist.genres.append(genre)
  if not form.validate():
    flash(form.errors)
    return redirect(url_for('create_artist_submission'))
  try:
    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  # data=[{
  #   "venue_id": 1,
  #   "venue_name": "The Musical Hop",
  #   "artist_id": 4,
  #   "artist_name": "Guns N Petals",
  #   "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #   "start_time": "2019-05-21T21:30:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 5,
  #   "artist_name": "Matt Quevedo",
  #   "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #   "start_time": "2019-06-15T23:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-01T20:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-08T20:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-15T20:00:00.000Z"
  # }]
  data = []
  list_of_all_shows = Show.query.all()
  for each_show in list_of_all_shows:
    artist_name = db.session.query(Artist.name).filter(Artist.id==each_show.artist_id).first()[0] # Artist.query.with_entities(Artist.name).filter(Artist.id == Show.artist_id).first()[0]
    data.append({
      'venue_id': each_show.venue_id,
      'venue_name': each_show.venue.name,
      'artist_id': each_show.artist_id,
      'artist_name': artist_name, # or: each_show.artist.name
      'artist_image_link': each_show.artist.image_link,
      'start_time': each_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm(request.form)
  # Because shows_table is just an Association Table to connect Venue and Artist, so we can't create an object of type shows_table
  #show = shows_table(venue_id=form.venue_id.data, artist_id=form.artist_id.data, start_time=form.start_time.data)
  # instead, we will create a new entry in the shows_table, by using the insert() method
  # Create a new entry in the shows_table
  # here, show_entry is an object of type sqlalchemy.sql.dml.Insert object, which is returned by the insert() method, and it contains the values that we want to insert into the shows_table
  # show_entry = shows_table.insert().values(
  #       venue_id=form.venue_id.data,
  #       artist_id=form.artist_id.data,
  #       start_time=form.start_time.data)
  show = Show(venue_id=form.venue_id.data, artist_id=form.artist_id.data, start_time=form.start_time.data)
  if not form.validate():
    flash(form.errors)
    return redirect(url_for('create_show_submission'))
  try:
    # because we don't create an object of type shows_table, so we can't use db.session.add(show), because db.session.add() only accepts an object as parameter
    #db.session.add(show_entry)
    # instead, we will use db.session.execute() to execute the insert() method
    db.session.add(show)
    # commit the changes to the database. Because db.session.execute() only executes the insert() method, but doesn't commit the changes to the database
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
