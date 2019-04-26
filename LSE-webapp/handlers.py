# -*- coding: utf-8 -*-
import logging
import secrets

import webapp2
import webob.multidict
import json

from google.appengine.ext import ndb
from models import AuctionHouse
from models import Server

from db_dictionary import factions
from db_dictionary import factions_abbr
from db_dictionary import item_dict
from db_dictionary import item_ids
from db_dictionary import auctionable_items

from webapp2_extras import auth, sessions, jinja2
from jinja2.runtime import TemplateNotFound

from simpleauth import SimpleAuthHandler

servers = {0:'All'}
servers_to_add = Server.query().order(Server.name).fetch()
for server in servers_to_add:
  servers[len(servers)] = server.name
server_current = "None"
faction_current =  "None"


class BaseRequestHandler(webapp2.RequestHandler):

  def dispatch(self):
    # Get a session store for this request.
    self.session_store = sessions.get_store(request=self.request)

    try:
      # Dispatch the request.
      webapp2.RequestHandler.dispatch(self)
    finally:
      # Save all sessions.
      self.session_store.save_sessions(self.response)

  def get_server_dict(self):
    servers_ordered = {0:'All'}
    servers_to_order = Server.query().order(Server.name).fetch()
    for server in servers_to_order:
      servers_ordered[len(servers_ordered)] = server.name

    return servers_ordered

  @webapp2.cached_property
  def jinja2(self):
    """Returns a Jinja2 renderer cached in the app registry"""
    return jinja2.get_jinja2(app=self.app)

  @webapp2.cached_property
  def session(self):
    """Returns a session using the default cookie key"""
    return self.session_store.get_session()

  @webapp2.cached_property
  def auth(self):
      return auth.get_auth()

  @webapp2.cached_property
  def current_user(self):
    """Returns currently logged in user"""
    user_dict = self.auth.get_user_by_session()
    return self.auth.store.user_model.get_by_id(user_dict['user_id'])

  @webapp2.cached_property
  def logged_in(self):
    """Returns true if a user is currently logged in, false otherwise"""
    return self.auth.get_user_by_session() is not None

  def render(self, template_name, template_vars={}):
    # Preset values for the template

    values = {
      'url_for': self.uri_for,
      'logged_in': self.logged_in,
      'flashes': self.session.get_flashes(),
      'search_suggestions': auctionable_items
    }
    if self.logged_in:
      values['admin'] = self.current_user.admin
      values['uploader'] = self.current_user.uploader
      values['faction'] = factions_abbr.get(self.current_user.faction)
      values['server'] = self.current_user.server
    else:
      values['server'] = server_current
      values['faction'] = faction_current
      values['destination_url'] = '/settings'

    # Add manually supplied template values
    values.update(template_vars)

    # read the template or 404.html
    try:
      self.response.write(self.jinja2.render_template(template_name, **values))
    except TemplateNotFound:
      self.abort(404)

  def head(self, *args):
    """Head is used by Twitter. If not there the tweet button shows 0"""
    pass


class RootHandler(BaseRequestHandler):
  def get(self):
    """Handles default landing page"""
    if self.logged_in:
      self.render('home.html', {
        'name': self.current_user.name,
        'server': self.current_user.server,
        'faction': factions.get(self.current_user.faction),
        'home': True,
        'page_id': 'home'
        })
    else:
      self.render('home.html', {
        'servers': servers,
        'factions': factions,
        'destination_url': '/settings',
        'home': True,
        'page_id': 'home'
        })

class AboutHandler(BaseRequestHandler):
  def get(self):
    self.render('construction.html', {
      'page': 'About',
      'server': self.session.get('server'),
      'faction': self.session.get('faction')
      })

class DownloadHandler(BaseRequestHandler):
  def get(self):
    self.render('construction.html', {
      'page': 'Downloads',
      'server': self.session.get('server'),
      'faction': self.session.get('faction')
      })

class SearchHandler(BaseRequestHandler):
  def get(self, server=None, faction=None):
    self.render('construction.html', {
      'page': 'Search',
      'server': server,
      'faction': faction
      })

class CompareHandler(BaseRequestHandler):
  def get(self, server=None, faction=None):
    self.render('construction.html', {
      'page': 'Compare',
      'server': server,
      'faction': faction
      })

class ProfessionHandler(BaseRequestHandler):
  def get(self, server=None, faction=None):
    self.render('construction.html', {
      'page': 'Profession',
      'server': server,
      'faction': faction
      })

class ServerHandler(BaseRequestHandler):
  def get(self, server=None, faction=None):
    self.session['server'] = server
    self.session['faction'] = faction
    self.render('construction.html', {
      'page': 'Server',
      'server': server,
      'faction': faction
      })
    

class ItemHandler(BaseRequestHandler):
  def get(self, server=None, faction=None, itemId=None):
    if int(itemId) in item_dict:
      item_name = item_dict[int(itemId)]
    else:
      self.abort(404);
    self.render('item.html', {
      'server': server,
      'faction': faction,
      'item_id': itemId,
      'item_name': item_name
      })

class SignInHandler(BaseRequestHandler):
  def get(self):
    """Handles default landing page"""
    self.render('sign_in.html', {'destination_url': '/settings'})

class AdminHandler(BaseRequestHandler):
  def get(self):
    """Handles GET /admin"""
    if self.logged_in and self.current_user.admin is True:
      self.render('admin.html', {
        'name': self.current_user.name,
        'servers': servers,
      })
    else:
      self.abort(403)

class AdminServerHandler(BaseRequestHandler):
  def get(self):
    """Handles GET /admin/server"""
    if self.logged_in and self.current_user.admin is True:
      self.render('server-admin.html', {
        'name': self.current_user.name,
        'servers': servers,
      })
    else:
      self.abort(403)

  def post(self):
    if self.logged_in and self.current_user.admin is True:
      server_name = self.request.get('name')
      server_type = int(self.request.get('ah'))
      new_server = Server(name=server_name, ah_type=server_type)
      new_server.put()
      new_server.id = new_server.key.urlsafe()
      new_server.put()
      servers = self.get_server_dict()
      if server_type:
        for num in range(1,4):
          new_ah = AuctionHouse(server_name=server_name, faction=num)
          new_ah.put()
          new_ah.id = new_ah.key.urlsafe()
          new_ah.put()
          new_server.ah_id = new_server.ah_id + [new_ah.id]
      else:
        new_ah = AuctionHouse(server_name=server_name, faction=0)
        new_ah.put()
        new_ah.id = new_ah.key.urlsafe()
        new_ah.put()
        new_server.ah_id = new_server.ah_id + [new_ah.id]
      new_server.put()


      self.render('server-admin.html', {
        'name': self.current_user.name,
        'servers': servers,
      })
    else:
      self.abort(403)

class AdminUploaderHandler(BaseRequestHandler):
  def get(self):
    """Handles GET /admin/uploader"""
    if self.logged_in and self.current_user.admin is True:
      self.render('uploader-admin.html', {
        'name': self.current_user.name,
        'servers':servers
      })
    else:
      self.abort(403)

  def post(self):
    if self.logged_in and self.current_user.admin is True:
      user_token = self.request.get('token')
      server_name = self.request.get('server')
      add = int(self.request.get('add_remove'))
      user = self.auth.store.user_model.get_by_auth_id(user_token)
      variables = {
        'uploader_name':user.name,
        'upload_server':server_name,
        'name': self.current_user.name,
        'servers': servers,
        'add':False
      }
      if add:
        user.uploader = True
        user.upload_server = server_name
        user.put()
        variables['add'] = True
      else:
        user.uploader = False
        user.upload_server = None
        user.put()
         
      self.render('uploader-admin.html', variables)
    else:
      self.abort(403)

class AdminItemsHandler(BaseRequestHandler):
  def get(self):
    """Handles GET /admin/items"""
    if self.logged_in and self.current_user.admin is True:
      self.render('items-admin.html', {
        'name': self.current_user.name,
        'servers':servers
      })
    else:
      self.abort(403)

  def post(self):
    if self.logged_in and self.current_user.admin is True:
      self.render('upload.html', variables) 
    else:
      self.abort(403)     
    



class SettingsHandler(BaseRequestHandler):
  def get(self):
    """Handles GET /settings"""
    if self.logged_in:
      variables = {
        'name': self.current_user.name,
        'server': self.current_user.server,
        'faction': factions.get(self.current_user.faction),
        'servers': servers,
        'factions': factions,
      }
      self.render('settings.html', variables)
    else:
      self.redirect('/sign_in')

  def post(self):
    if self.logged_in:
      updated_server = self.request.get('server')
      updated_faction = self.request.get('faction')
      self.current_user.server = updated_server
      self.current_user.faction = int(updated_faction)
      self.current_user.put()
      variables = {
        'name': self.current_user.name,
        'server': self.current_user.server,
        'faction': factions.get(self.current_user.faction),
        'servers': servers,
        'factions': factions,
      }
      self.render('settings.html', variables)
    else:
      self.redirect('/sign_in')

class ProfileHandler(BaseRequestHandler):
  def get(self):
    """Handles GET /profile"""
    if self.logged_in:
      variables = {
        'name': self.current_user.name,
        'server': self.current_user.server,
        'faction': factions.get(self.current_user.faction),
        'admin': False,
        'uploader': False
      }
      if self.current_user.admin:
        variables['admin'] = True
      if self.current_user.uploader:
        variables['uploader'] = True
      self.render('profile.html', variables)
    else:
      self.redirect('/')

class UploadHandler(BaseRequestHandler):
  def get(self):
    """Handles GET /upload"""
    if self.logged_in and self.current_user.uploader is True:
      variables = {
        'name': self.current_user.name,
        'server': self.current_user.uploader_server,
        'factions': factions,
        'servers': None
      }
      if self.current_user.uploader_server == 'All':
        variables['servers'] = servers

      self.render('upload.html', variables) 
    else:
      self.abort(403)

  def post(self):
    """Handles POST /upload"""
    if self.logged_in and self.current_user.uploader is True:
      filename = self.request.params['data'].filename
      faction_key = int(self.request.get('faction'))
      faction_name = factions.get(faction_key) 
      server = self.request.get('server')
      variables = {
        'name': self.current_user.name,
        'filename': filename,
        'server': server,
        'factions': factions,
        'faction': faction_name,
        'servers': None,
        'newData': False,
        'error_faction': False,
        'error_server': False,
        'success': False
      }
      # Filename
      if filename != 'LSE-addon.json':
        self.abort(400)

      ah_data = json.loads(self.request.get('data'))
      # Faction
      if ah_data['LSE']['faction'] != faction_name:
        self.response.write(faction)
        self.response.write(ah_data['LSE']['faction'])
        variables['error_faction'] = True
      # Server
      if ah_data['LSE']['server'] != server:
        variables['error_server'] = True

      if self.current_user.upload_server == 'All':
        variables['servers'] = servers

      if variables.get('error_faction') == False and variables.get('error_server') == False:
        variables['success'] = True
        scan_date = ah_data['LSE']['date'] 
        ah = AuctionHouse.query(AuctionHouse.server_name == server, AuctionHouse.faction == faction_key).get()
        if ah.auctions:
          ah.auctions.update(ah_data['auctions'])
        else:
          ah.auctions = ah_data['auctions']
        ah.put()

      self.render('upload.html', variables)
    else:
      self.abort(403)

class PlaygroundHandler(BaseRequestHandler):
  def get(self):
    """Handles GET /playground"""
    variables = {
      'servers': servers,
      'factions': factions,
      'page_id': 'playground',
      'item_name': 'Black Lotus'
    }
    if self.logged_in:
      variables['name'] = self.current_user.name,

    self.render('playground.html', variables)

class AuthHandler(BaseRequestHandler, SimpleAuthHandler):
  """Authentication handler for OAuth 2.0, 1.0(a) and OpenID."""

  # Enable optional OAuth 2.0 CSRF guard
  OAUTH2_CSRF_STATE = True

  USER_ATTRS = {
    'facebook': {
      'name': 'name'
    },
    'googleplus': {
      'displayName': 'name'
    },
    'windows_live': {
      'name': 'name'
    },
    'twitter': {
      'screen_name': 'name'
    },
  }

  def _on_signin(self, data, auth_info, provider, extra=None):
    """Callback whenever a new or existing user is logging in.
     data is a user info dictionary.
     auth_info contains access token or oauth token and secret.
     extra is a dict with additional params passed to the auth init handler.
    """
    logging.debug('Got user data: %s', data)

    auth_id = '%s:%s' % (provider, data['id'])

    logging.debug('Looking for a user with id %s', auth_id)
    user = self.auth.store.user_model.get_by_auth_id(auth_id)
    _attrs = self._to_user_model_attrs(data, self.USER_ATTRS[provider])

    if user:
      logging.debug('Found existing user to log in')
      # Existing users might've changed their profiile data so we update our
      # local model anyway. This might result in quite inefficient usage
      # of the Datastore, but we do this anyway for demo purposes.
      #
      # In a real app you could compare _attrs with user's properties fetched
      # from the datastore and update local user in case something's changed.
      user.populate(**_attrs)
      user.put()
      self.auth.set_session(self.auth.store.user_to_dict(user))

    else:
      # check whether there's a user currently logged in
      # then, create a new user if nobody's signed in,
      # otherwise add this auth_id to currently logged in user.

      if self.logged_in:
        logging.debug('Updating currently logged in user')

        u = self.current_user
        u.populate(**_attrs)
        # The following will also do u.put(). Though, in a real app
        # you might want to check the result, which is
        # (boolean, info) tuple where boolean == True indicates success
        # See webapp2_extras.appengine.auth.models.User for details.
        u.add_auth_id(auth_id)

      else:
        logging.debug('Creating a brand new user')
        ok, user = self.auth.store.user_model.create_user(auth_id, **_attrs)
        if ok:
          self.auth.set_session(self.auth.store.user_to_dict(user))

    # user settings page
    destination_url = '/settings'
    if extra is not None:
      params = webob.multidict.MultiDict(extra)
      destination_url = str(params.get('destination_url', '/settings'))
    return self.redirect(destination_url)

  def logout(self):
    self.auth.unset_session()
    self.redirect('/')

  def handle_exception(self, exception, debug):
    logging.error(exception)
    self.render('error.html', {'exception': exception})

  def _callback_uri_for(self, provider):
    return self.uri_for('auth_callback', provider=provider, _full=True)

  def _get_consumer_info_for(self, provider):
    """Returns a tuple (key, secret) for auth init requests."""
    return secrets.AUTH_CONFIG[provider]

  def _get_optional_params_for(self, provider):
    """Returns optional parameters for auth init requests."""
    return secrets.AUTH_OPTIONAL_PARAMS.get(provider)
		
  def _to_user_model_attrs(self, data, attrs_map):
    """Get the needed information from the provider dataset."""
    user_attrs = {}
    for k, v in attrs_map.iteritems():
      attr = (v, data.get(k)) if isinstance(v, str) else v(data.get(k))
      user_attrs.setdefault(*attr)

    user_attrs.setdefault('server', 'All')
    user_attrs.setdefault('faction', 0)
    user_attrs.setdefault('admin', True)
    user_attrs.setdefault('uploader', True)
    user_attrs.setdefault('upload_server', None)

    return user_attrs
