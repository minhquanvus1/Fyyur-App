from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# declare db variable, without initializing it with app
db = SQLAlchemy()

# create a many-to-many relationship table between Venue and Genre, by creating a new table "venue_genres_table"
# Notice that: this Association Table should be placed ABOVE the Venue class, so that the Venue class can reference it, or else it will throw an error "venue_genres_table not defined"
# venue_genres_table = db.Table('venue_genres_table',
#                               db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True),
#                               db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True))

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
    # use the list of genres in the form.py, to create a new column in the Venue table, called genres
    genres = db.Column(db.ARRAY(db.String()), nullable=True)
    # genres = db.relationship('Genre', secondary=venue_genres_table, backref=db.backref('venues', lazy=True, cascade='all, delete'))
    shows = db.relationship('Show', backref='venue', lazy='joined', cascade='all, delete')
    
    
    def __repr__(self):
      return f'<Venue ID: {self.id}, name: {self.name}, city: {self.city}, state: {self.state}, address: {self.address}, phone: {self.phone}, image_link: {self.image_link}, facebook_link: {self.facebook_link}, website: {self.website}, seeking_talent: {self.seeking_talent}, seeking_description: {self.seeking_description}, genres: {self.genres}, shows: {self.shows}>'

# create a many-to-many relationship table between Artist and Genre, by creating a new table "artist_genres_table"
# Notice that: this Association Table should be placed ABOVE the Artist class, so that the Artist class can reference it, or else it will throw an error "artist_genres_table not defined"
# artist_genres_table = db.Table('artist_genres_table', 
#                                db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True),
#                                db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True))

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String())
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String())
    genres = db.Column(db.ARRAY(db.String()), nullable=True)
    # genres = db.relationship('Genre', secondary=artist_genres_table, backref=db.backref('artists', lazy=True, cascade='all, delete'))
    # venues = db.relationship('Venue', secondary=shows_table, backref=db.backref('artists', lazy=True))
    shows = db.relationship('Show', backref='artist', lazy='joined', cascade='all, delete')
    # use lazy='joined' to load the related object in the same query as the parent using a JOIN statement. This will allow us to access the related object without another query. This is usually sufficient for simple associations and it can be disabled by setting lazy=False.
    # what I mean is that for example when we query the Artist table, we can also get the related Show table, without having to query the Show table again. This is because we have the "shows" relationship in the Artist table, and we set lazy='joined' for the "shows" relationship, so that we can get the related Show table in the same query as the Artist table, using a JOIN statement. so artist.shows will return the related Show table, without having to query the Show table again. If we use lazy=True, then artist.shows will return a query object, and we have to use artist.shows.all() to get the related Show table.
    def __repr__(self):
      return f'<Artist ID: {self.id}, name: {self.name}, city: {self.city}, state: {self.state}, phone: {self.phone}, image_link: {self.image_link}, facebook_link: {self.facebook_link}, website: {self.website}, seeking_venue: {self.seeking_venue}, seeking_description: {self.seeking_description}, genres: {self.genres}, shows: {self.shows}>'
# create Genre Model class (child to Artist, and Venue model class), to implement many-to-many relationship

# Because Show is an Entity (a Venue Owner can Post a Show), so we need to create a Model class for Show. Not create the Association Table "shows_table", which is just like a "virtual table" that serves only for representing the many-to-many relationship between Artist, Venue
class Show(db.Model):
  __tablename__ = 'Show'
  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
  
  def __repr__(self):
    return f'<Show ID: {self.id}, venue_id: {self.venue_id}, artist_id: {self.artist_id}, start_time: {self.start_time}>'

# class Genre(db.Model):
#   __tablename__ = 'Genre'
#   id = db.Column(db.Integer, primary_key=True)
#   name = db.Column(db.String())
  
#   def __repr__(self):
#     return f'<Genre ID: {self.id}, name: {self.name}>'