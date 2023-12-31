#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json, sys, datetime
import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm as Form
from forms import *
from flask_migrate import Migrate
from models import db, Artist, Venue, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.app_context().push() # add this line to fix the error "RuntimeError: No application found. Either work inside a view function or push an application context." when using the Interactive Shell, because we are using the "app" object outside of the view function, which means that we are using the "app" object outside of the application context. So we need to push the application context, so that we can use the "app" object outside of the view function. The view function is the function that is decorated with the app.route decorator, for example: @app.route('/venues/create', methods=['GET']). if we don't use this, why we access the app outside the view function, because we are using the "app" object outside of the application context, so it will throw an error "RuntimeError: Working outside of application context." But this error didn't happen when we use db = SQLAlchemy(app), because SQLAlchemy(app) will automatically push the application context for us, so that we can use the "app" object outside of the view function. But when we use db = SQLAlchemy(), we have to push the application context manually, so that we can use the "app" object outside of the view function. Another way to solve this error is
db.init_app(app) # initialize db with app

# TODO: connect to a local postgresql database (already done in config.py)

# create a Migrate object to generate migration file
migrate = Migrate(app, db)


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

  search_term = request.form.get('search_term', '').strip() # get the search term from the form, and remove the leading and trailing spaces. if we don't use the second argument in request.form.get('search_term', ''), then it will return None, instead of empty string ''
  print("search_term: ", search_term)
  # if the user just enters whitespace, then redirect to the venues page
  if search_term == '':
    #flash('Please enter a search term!')
    return redirect(url_for('venues'))
  list_of_found_venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all() # for CASE-SENSITIVE search, use Venue.name.like('%' + search_term + '%')
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
      'genres': each_venue.genres,
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
 
  # set the csrf to False, to disable the csrf protection, otherwise it will throw an error "The CSRF token is missing."
  form = VenueForm(request.form, meta={'csrf': False})
  
  if not form.validate():
    message = []
    for field, errors in form.errors.items():
      for error in errors:
        message.append(field + ' ' + error)
    flash('Errors ' + str(message))
    return redirect(url_for('create_venue_submission'))
  
  # get the list of genres from the form
  #genre_name_list = request.form.getlist('genres')
  # print("genre_list type: ", type(genre_name_list))
  # print("genre_list data: ", genre_name_list)
  # print("form.genres.data: ", form.genres.data)
  #print("genre_name_list: ", request.form.getlist('genres'))


  #for each_genre_name in genre_name_list:
    # create a new Genre object
    #genre = Genre(name=each_genre_name)
    # append the new Genre object to the venue.genres list
    #venue.genres.append(genre)
  
  try: 
    venue = Venue(name=form.name.data, 
                  city=form.city.data, 
                  state=form.state.data, 
                  address=form.address.data, 
                  phone=form.phone.data, 
                  image_link=form.image_link.data, 
                  facebook_link=form.facebook_link.data, 
                  website=form.website_link.data, 
                  seeking_talent=form.seeking_talent.data, 
                  seeking_description=form.seeking_description.data, 
                  genres = form.genres.data)
    
    print("venue: ", venue)
    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    print(sys.exc_info())
  finally:
    db.session.close()
  return redirect(url_for('index'))

@app.route('/venues/<int:venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
    print("delete haha")
    flash('Venue ' + venue_id + ' was successfully deleted!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    print("delete huhu")
    flash('An error occurred. Venue ' + venue_id + ' could not be deleted.')
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + venue_id + ' could not be deleted.')
    abort(500)
  else:
    flash('Venue ' + venue_id + ' was successfully deleted!')
  return jsonify({ 'success': True })

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  
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
  
  search_term = request.form.get('search_term', '').strip()
  if search_term == '':
    return redirect(url_for('artists'))
  list_of_found_artists = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all() # for CASE-SENSITIVE search, use Artist.name.like('%' + search_term + '%')
  number_of_found_artists = len(list_of_found_artists)
  if number_of_found_artists == 0:
    flash('No results found for: ' + search_term)
    return redirect(url_for('artists'))
  else:
    # use list comprehension to create a list of "customized_artists" dictionaries, each of which contains the information of an artist, and the number of upcoming shows for that artist
    list_of_customized_artists = [{'id': each_found_artist.id, 'name': each_found_artist.name, 'num_upcoming_shows': Show.query.filter(Show.artist_id == each_found_artist.id).filter(Show.start_time >= datetime.now()).count()} for each_found_artist in list_of_found_artists]
    response = {
      'count': number_of_found_artists,
      'data': list_of_customized_artists
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  
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
      'genres': each_artist.genres, 
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
  
  artist = Artist.query.filter_by(id=artist_id).first()
  #list_of_genres_object = artist.genres # get the list of Genres Object of each artist
  #list_of_genres_name = [each_genre_object.name for each_genre_object in list_of_genres_object]
  form.genres.data = artist.genres # apply Server-Side Rendering to prepopulate ONLY the "genres" field (because the "genres" field is a multiple select field, and we can't prepopulate it using Client-side Rendering in the edit_artist.html)
  # the rest of the fields will be prepopulated using Client-side Rendering in the edit_artist.html
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  
  form = ArtistForm(request.form, meta={'csrf': False})
  
  if not form.validate:
    message = []
    for field, errors in form.errors.items():
      for error in errors:
        message.append(field + ' ' + error)
    flash('Errors ' + str(message))
    return redirect(url_for('edit_artist_submission', artist_id=artist_id))
  
  
  # clear the list of current Genres of that Artist
  #artist.genres = []
  #list_of_updated_genres_name = request.form.getlist('genres') # "form.genres.data" is equivalent to "request.form.getlist('genres')", which returns the list of Genres' names that the user has selected on the form
  #list_of_updated_genres_object = form.genres.data
  
  #list_of_updated_genres_name = form.genres.data # return the list of Genres' names that the user has selected on the form
  # for each_update_genre_object in list_of_updated_genres_object:
  #   list_of_updated_genres_name.append(each_update_genre_object.name)
  # for each_updated_genre_name in list_of_updated_genres_name:
  #   genre = Genre(name=each_updated_genre_name)
  #   artist.genres.append(genre)
  try:
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
    artist.genres = form.genres.data
    
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
  
 
  # get the current data of a particular Venue (with a particular venue_id) to display on the edit page, for user to edit their existing data
  venue = db.session.query(Venue).filter(Venue.id==venue_id).all()[0] # .all()[0] is equivalent to .first()

  #list_of_genres_object = venue.genres # get the list of Genres Object of each venue
  #list_of_genres_name = [each_genre_object.name for each_genre_object in list_of_genres_object] # list comprehension, to get the list of Genres' names of each venue
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
  form.genres.data = venue.genres # pre-populate the "genres" field of the form with the list of Genres' names of the Venue
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
 
  form = VenueForm(request.form, meta={'csrf': False})
  if not form.validate():
    message = []
    for field, errors in form.errors.items():
      for error in errors:
        message.append(field + ' ' + error)
    flash('Errors ' + str(message))
    return redirect(url_for('edit_venue_submission', venue_id=venue_id))
  
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
  #list_of_updated_genres_name = request.form.getlist('genres')
  # Validate the form, by checking if the form is valid or not (basing on the constraints of the VenueForm class in forms.py)
  # if not form.validate():
  #   flash(form.errors)
  #   return redirect(url_for('edit_venue_submission', venue_id=venue_id))
  # clear the list of current Genres of that Venue
  #venue.genres.clear()
  # for each_updated_genre_name in list_of_updated_genres_name:
  #   genre = Genre(name=each_updated_genre_name)
  #   venue.genres.append(genre)
  # print(f'updated genres of this Venue, with venue_id = {venue_id}: ', venue.genres)
  # print('updated venue: ', venue)
  
  try:
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
    venue.genres = form.genres.data
    
    db.session.add(venue)
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
  
  form = ArtistForm(request.form, meta={'csrf': False})
  if not form.validate():
    message = []
    for field, errors in form.errors.items():
      for error in errors:
        message.append(field + ' ' + error)
    flash('Errors ' + str(message))
    return redirect(url_for('create_artist_form'))
  
  #genre_name_list = request.form.getlist('genres')
  # for each_genre_name in genre_name_list:
  #   # create a new Genre object
  #   genre = Genre(name=each_genre_name)
  #   # append the new Genre object to the venue.genres list
  #   artist.genres.append(genre)
  
  try:
    artist = Artist(name=form.name.data, 
                    city=form.city.data, 
                    state=form.state.data, 
                    phone=form.phone.data, 
                    image_link=form.image_link.data, 
                    facebook_link=form.facebook_link.data, 
                    website=form.website_link.data, 
                    seeking_venue=form.seeking_venue.data, 
                    seeking_description=form.seeking_description.data, 
                    genres=form.genres.data)

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
  form = ShowForm(request.form, meta={'csrf': False})
  if not form.validate():
    message = []
    for field, errors in form.errors.items():
      for error in errors:
        message.append(field + ' ' + error)
    flash('Errors ' + str(message))
    return redirect(url_for('create_show_submission'))
  # Because shows_table is just an Association Table to connect Venue and Artist, so we can't create an object of type shows_table
  #show = shows_table(venue_id=form.venue_id.data, artist_id=form.artist_id.data, start_time=form.start_time.data)
  # instead, we will create a new entry in the shows_table, by using the insert() method
  # Create a new entry in the shows_table
  # here, show_entry is an object of type sqlalchemy.sql.dml.Insert object, which is returned by the insert() method, and it contains the values that we want to insert into the shows_table
  # show_entry = shows_table.insert().values(
  #       venue_id=form.venue_id.data,
  #       artist_id=form.artist_id.data,
  #       start_time=form.start_time.data)
 
  
  try:
    show = Show(venue_id=form.venue_id.data, 
                artist_id=form.artist_id.data, 
                start_time=form.start_time.data)
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
