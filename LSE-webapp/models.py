from google.appengine.ext import ndb
	

class Item(ndb.Model):
	id = ndb.IntegerProperty()
	sub_id = ndb.IntegerProperty()
	category = ndb.IntegerProperty()
	subcategory = ndb.IntegerProperty()
	item_slot = ndb.IntegerProperty()
	rarity = ndb.IntegerProperty()
	level = ndb.IntegerProperty()
	link = ndb.StringProperty()

class AuctionHouse(ndb.Model):
	id = ndb.StringProperty()
	server_name = ndb.StringProperty()
	faction = ndb.IntegerProperty()
	auctions = ndb.JsonProperty()
	daily_totals = ndb.IntegerProperty(repeated=True)


class Server(ndb.Model):
	id = ndb.StringProperty()
	name = ndb.StringProperty()
	expansion = ndb.IntegerProperty()
	ah_type = ndb.IntegerProperty()
	ah_id = ndb.StringProperty(repeated=True)
