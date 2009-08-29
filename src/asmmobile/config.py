from zope.app.appsetup.product import getProductConfiguration
import datetime

config = getProductConfiguration('assembly-mobile')

if config is None:
    config = {}

clock = datetime.datetime(2009, 1, 1)

partyName = config.get('party-name', u"Assembly")
locations = config.get('locations', u"location")
events = config.get('events', u"event")
