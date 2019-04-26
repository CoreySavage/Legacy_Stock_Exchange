# -*- coding: utf-8 -*-
import sys
from secrets import SESSION_KEY

import webapp2
from webapp2 import WSGIApplication, Route


# inject './lib' dir in the path so that we can simply do "import ndb"
# or whatever there's in the app lib dir.
if 'lib' not in sys.path:
    sys.path[0:0] = ['lib']


# webapp2 config
app_config = {
  'webapp2_extras.sessions': {
    'cookie_name': '_simpleauth_sess',
    'secret_key': SESSION_KEY
  },
  'webapp2_extras.auth': {
    'user_attributes': []
  }
}


# Map URLs to handlers
routes = [
  # Home
  Route('/', handler='handlers.RootHandler'),
  # About
  Route('/about', handler='handlers.AboutHandler', name='about'),
  # Downloads
  Route('/download', handler='handlers.DownloadHandler', name='download'),
   # Search for Items
  Route('/<server>/<faction:alliance|horde|neutral>/search', handler='handlers.SearchHandler', name='search'),
  # Compare items selected from search - redirects to search with message if no items selected for comparison
  Route('/<server>/<faction:alliance|horde|neutral>/compare', handler='handlers.CompareHandler', name='compare'),
  # Specifc profession data - Material costs - Recipe costs - Top Craftable costs - Top craftable profit margins
  Route('/<server>/<faction:alliance|horde|neutral>/profession/(.*)', handler='handlers.ProfessionHandler', name='profession'),
  # Data for a specific server and faction
  Route('/<server>/<faction:alliance|horde|neutral>', handler='handlers.ServerHandler', name='server'),
  # Data for a specific item on a server and faction
  Route('/<server>/<faction:alliance|horde|neutral>/<itemId>', handler='handlers.ItemHandler', name='item'),
  # Administration, Login, and Uploader handlers
  Route('/sign_in', handler='handlers.SignInHandler', name='sign_in'),
  Route('/admin', handler='handlers.AdminHandler', name='admin'),
  Route('/admin/items', handler='handlers.AdminItemsHandler', name='admin_items'),
  Route('/admin/server', handler='handlers.AdminServerHandler', name='server'),
  Route('/admin/uploader', handler='handlers.AdminUploaderHandler', name='uploader'),
  Route('/settings', handler='handlers.SettingsHandler', name='settings'),
  Route('/profile', handler='handlers.ProfileHandler', name='profile'),
  Route('/upload', handler='handlers.UploadHandler', name='upload'),
  Route('/logout', handler='handlers.AuthHandler:logout', name='logout'),
  Route('/auth/<provider>', handler='handlers.AuthHandler:_simple_auth', name='auth_login'),
  Route('/auth/<provider>/callback', handler='handlers.AuthHandler:_auth_callback', name='auth_callback'),
  # Test page for new content
  Route('/playground', handler='handlers.PlaygroundHandler', name='playground')
]


app = WSGIApplication(routes, config=app_config, debug=True)
