#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
from mylog import mylog
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app,db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String)
    show = db.relationship('Show', backref='venue', lazy ='joined', passive_deletes=True)

    def __repr__(self):
        return f'<V: {self.id}, {self.name}, {self.city}, {self.state}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String)
    show = db.relationship('Show', backref='artist', lazy='joined', passive_deletes=True)

    def __repr__(self):
        return f'<A: {self.id} {self.name}>'


    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id', ondelete='CASCADE'))
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id', ondelete='CASCADE'))
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<S: {self.artist_id} {self.venue_id} {self.start_time}>'
# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

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
    # implementing recently added in "Suggestions to make your project stand out" section 2
    recent_artists = Artist.query.order_by(Artist.id.desc()).limit(10).all()
    recent_venues = Venue.query.order_by(Venue.id.desc()).limit(10).all()

    return render_template('pages/home.html', recent_venues=recent_venues, recent_artists = recent_artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  locations = Venue.query.with_entities(Venue.state, Venue.city).distinct(Venue.state, Venue.city).all()
  data = []
  for i in range(len(locations)):
      venues = Venue.query.filter_by(state=locations[i][0], city=locations[i][1])
      data.append({
      'city': locations[i][1],
      'state': locations[i][0],
      'venues': []
      })
      for venue in venues:
          shows = Show.query.filter_by(venue_id=venue.id).all()
          count = 0
          for show in shows:
              if show.start_time > datetime.now():
                  count = count + 1

          item = {
           'id': venue.id,
           'name': venue.name,
           'num_upcoming_shows': count
          }
          data[i]['venues'].append(item)

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike("%" + search + "%")).all()

  response ={
    'count': len(venues),
    'data':[]
  }

  for venue in venues:
      shows = Show.query.filter_by(venue_id=venue.id).all()
      count = 0
      for show in shows:
          if show.start_time > datetime.now():
              count = count + 1

      response["data"].append({
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': count
      })

  return render_template('pages/search_venues.html', results=response, search_term=search)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.filter_by(id=venue_id).first()
  now = datetime.now()
  past_shows = Show.query.filter(Show.venue_id==venue_id, Show.start_time < now).all()
  upcoming_shows = Show.query.filter(Show.venue_id==venue_id, Show.start_time > now).all()

  # organize genres into an array. For some reason form returns it in a weird way, all characters seperated by a comma
  t = ''.join(venue.genres)
  genres = t[1:-1].replace('"','').split(',')
  # mylog(venue.genres)
  data = {
    'id': venue.id,
    'name': venue.name,
    'genres': genres,
    'address': venue.address,
    'city': venue.city,
    'state': venue.state,
    'phone': venue.phone,
    'website': venue.website_link,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description,
    'image_link': venue.image_link,
    'past_shows_count': len(past_shows),
    'upcoming_shows_count': len(upcoming_shows)
  }

  past = []
  upcoming = []
  for show in past_shows:
      artist = Artist.query.filter_by(id=show.artist_id).first()
      info = {
        'artist_id': artist.id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link,
        'start_time': show.start_time.strftime("%m-%d-%Y %H:%M:%S")
      }
      past.append(info)
  data["past_shows"] = past

  for show in upcoming_shows:
      artist = Artist.query.filter_by(id=show.artist_id).first()
      info = {
        'artist_id': artist.id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link,
        'start_time': show.start_time.strftime("%m-%d-%Y %H:%M:%S")
      }
      upcoming.append(info)
  data["upcoming_shows"] = upcoming
  # mylog(data)
  # data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
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
  form = VenueForm()
  try:
    venue = Venue(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        address = form.address.data,
        phone = form.phone.data,
        genres = form.genres.data,
        image_link = form.image_link.data,
        facebook_link = form.facebook_link.data,
        website_link = form.website_link.data,
        seeking_talent = form.seeking_talent.data,
        seeking_description = form.seeking_description.data
        )
    db.session.add(venue)
    db.session.commit()
    # mylog(venue.genres)
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('Something went wrong! Venue ' + request.form['name'] + ' could not be listed. Please try again.')
  finally:
    db.session.close()

  return redirect(url_for('index'))
  # return render_template('pages/home.html')

# @app.route('/venues/<int:venue_id>', methods=['DELETE'])
# switcing DELETE in favor of POST
@app.route('/venues/<int:venue_id>', methods=['POST'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
    flash('Venue(ID:' + str(venue_id) + ') was successfully deleted!')
  except:
    db.session.rollback()
    flash('Oops! Something went wrong!')
    # mylog(sys.exc_info())
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  # return None
  return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  return render_template('pages/artists.html', artists=Artist.query.order_by('id').all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike("%" + search + "%")).all()

  response = {
    'count': len(artists),
    'data': []
  }

  for artist in artists:
      shows = Show.query.filter_by(artist_id=artist.id).all()
      count = 0
      for show in shows:
          if show.start_time > datetime.now():
              count = count + 1

      response["data"].append({
        'id': artist.id,
        'name': artist.name,
        'num_upcoming_shows': count
        })

  return render_template('pages/search_artists.html', results=response, search_term=search)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.get_or_404(artist_id)
  # genres = artist.genres[0][1:-1].split(',')
  # mylog(genres)
  now = datetime.now()
  past_shows = Show.query.filter(Show.artist_id == artist.id, Show.start_time < now).all()
  upcoming_shows = Show.query.filter(Show.artist_id == artist.id, Show.start_time > now).all()
  data = {
    'id': artist.id,
    'name': artist.name,
    'genres': artist.genres,
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,
    'website': artist.website_link,
    'facebook_link': artist.facebook_link,
    'seeking_venue': artist.seeking_venue,
    'seeking_description': artist.seeking_description,
    'image_link': artist.image_link,
    'past_shows_count': len(past_shows),
    'upcoming_shows_count': len(upcoming_shows)
  }
  past = []
  upcoming = []

  for show in past_shows:
      venue = Venue.query.filter_by(id=show.venue_id).first()
      info = {
        'venue_id': venue.id,
        'venue_name': venue.name,
        'venue_image_link': venue.image_link,
        'start_time': show.start_time.strftime("%m-%d-%Y %H:%M:%S")
      }
      past.append(info)

  data["past_shows"] = past

  for show in upcoming_shows:
      venue = Venue.query.filter_by(id=show.venue_id).first()
      info = {
        'venue_id': venue.id,
        'venue_name': venue.name,
        'venue_image_link': venue.image_link,
        'start_time': show.start_time.strftime("%m-%d-%Y %H:%M:%S")
      }
      upcoming.append(info)

  data["upcoming_shows"] = upcoming

  # data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  # genres = artist.genres[0][1:-1].split(',')
  data = {
   "id": artist.id,
   "name": artist.name,
   "genres": artist.genres,
   "city": artist.city,
   "state": artist.state,
   "phone": artist.phone,
   "website_link": artist.website_link,
   "facebook_link": artist.facebook_link,
   "seeking_venue": artist.seeking_venue,
   "seeking_description": artist.seeking_description,
   "image_link": artist.image_link
  }
  form = ArtistForm(data=data)
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm()
    try:
        artist.name = form.name.data
        artist.genres = form.genres.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.website_link = form.website_link.data
        artist.facebook_link = form.facebook_link.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        artist.image_link = form.image_link.data
        db.session.commit()
        flash('Artist(ID:' + str(artist_id) + ') info was successfully updated.')
    except:
        db.session.rollback()
        mylog(sys.exc_info())
        flash('Something went wrong! Artist info could not be updated.')
    finally:
        db.session.close()
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get_or_404(venue_id)
  t = ''.join(venue.genres)
  genres = t[1:-1].replace('"','').split(',')
  data = {
    'id': venue.id,
    'name': venue.name,
    'genres': genres,
    'address': venue.address,
    'city': venue.city,
    'state': venue.state,
    'phone': venue.phone,
    'website_link': venue.website_link,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description,
    'image_link': venue.image_link
  }
  # form = VenueForm(obj=venue)
  # Can't use obj attr, becasue genres get created messed up. I fix it on my own data then fill with items in data.
  form = VenueForm(data=data)

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get_or_404(venue_id)
  form = VenueForm()
  try:
      venue.name = form.name.data
      venue.genres = form.genres.data
      venue.address = form.address.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.phone = form.phone.data
      venue.website_link = form.website_link.data
      venue.facebook_link = form.facebook_link.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data
      venue.image_link = form.image_link.data
      db.session.commit()
      flash('Venue(ID:' + str(venue_id) + ') info was successfully updated.')
  except:
      db.session.rollback()
      # mylog(sys.exc_info())
      flash('Something went wrong! Venue info could not be updated.')
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
  # TODO: insert form data as a new Artist record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
    form = ArtistForm()
    artist = Artist(
        name =form.name.data,
        city = form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        genres = form.genres.data,
        image_link = form.image_link.data,
        facebook_link = form.facebook_link.data,
        website_link = form.website_link.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description = form.seeking_description.data
        )
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    # on successful db insert, flash success
  except:
    db.session.rollback()
    flash('Something went wrong! Artist ' + request.form['name'] + ' could not be listed. Please try again.')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  finally:
    db.session.close()
  return redirect(url_for('index'))
  # return render_template('pages/home.html')

@app.route('/artists/<int:artist_id>', methods=['POST'])
def delete_artist(artist_id):
  # Implement artist deletion
  try:
    Artist.query.filter_by(id=artist_id).delete()
    db.session.commit()
    flash('Artist(ID:' + str(artist_id) + ') was successfully deleted!')
  except:
    db.session.rollback()
    flash('Oops! Something went wrong!')
    # mylog(sys.exc_info())
  finally:
    db.session.close()

  return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = []
  shows = Show.query.order_by(Show.start_time.desc()).all()
  for show in shows:
      venue = Venue.query.filter_by(id=show.venue_id).first()
      artist = Artist.query.filter_by(id=show.artist_id).first()
      data.extend([{
        'venue_id': venue.id,
        'venue_name': venue.name,
        'artist_id': artist.id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link,
        'start_time': show.start_time.strftime("%m-%d-%Y %H:%M:%S")
      }])

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
  try:
    form = ShowForm()
    show = Show(
      artist_id = form.artist_id.data,
      venue_id = form.venue_id.data,
      start_time = form.start_time.data
    )
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('Something went wrong! Show could not be listed.')

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
    app.run(host='0.0.0.0')

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
