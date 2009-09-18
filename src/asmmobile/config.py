from zope.app.appsetup.product import getProductConfiguration
import datetime

config = getProductConfiguration('assembly-mobile')

if config is None:
    config = {}

clock = datetime.datetime(2009, 1, 1)

siteName = config.get('site-name', u"Assembly Mobile")
sourceUrl = config.get('source-url', u"http://bitbucket.org/barro/assembly-mobile/")
partyName = config.get('party-name', u"Assembly")
locations = config.get('locations', u"location")
events = config.get('events', u"event")

nextEventsEndHours = int(config.get('next-events-show-end-hours', 2))
nextEventsStartHours = int(config.get('next-events-show-start-hours', 10))

mobileMode = config.get('mobile-mode', True)
