from zope.app.appsetup.product import getProductConfiguration

config = getProductConfiguration('assembly-mobile')

if config is None:
    config = {}

# Either "now" or time given in following format: year-month-day-hour-minute
time = config.get("time", "now")

siteName = config.get("site-name", u"Assembly Mobile")
sourceUrl = config.get("source-url", u"http://bitbucket.org/barro/assembly-mobile/")
partyName = config.get("party-name", u"Assembly")
mainSiteUrl = config.get("main-site-url", u"http://www.assembly.org/")
locations = config.get("locations", u"location")
events = config.get("events", u"event")

nextEventsEndHours = int(config.get('next-events-show-end-hours', 2))
nextEventsStartHours = int(config.get('next-events-show-start-hours', 10))

mobileMode = config.get('mobile-mode', True)

# Sort types: start-time, location-priority
sortCurrentEvents = config.get("sort-current-events", "start-time")
sortNextEvents = config.get("sort-next-events", "start-time")

# Selector types for future events:
#
# one-per-location = one event per location
# not-hidden = only events that are visible
# maximum-amount = masimum number of events (maximum-amount:4)
#
# Multiple selectors can be combined with "&" to filter themselves.
selectNextEvents = config.get("select-next-events", "not-hidden&one-per-location")

# Importing options:

# Names that are shorten that short-name-maximum-length are not shortened.
shortNameMaximumLength = config.get("short-name-maximum-length", 60)

# Names are shortened to this length before starting to search for word
# boundary. Names are cut at word boundaries instead of coldly cutting them
# to short length.
shortNameShortenTo = config.get("short-name-shorten-to", 55)

# Characters that we use to find word boundaries.
shortNameNonWordCharacters = config.get("short-name-non-word-characters", "-#:,.?!/ ")

# Cut postfix is added to the end of shortened names.
shortNameCutPostfix = config.get("short-name-cut-postfix", "...")

# Calendar cache times:
calendarCacheMinutes = int(config.get("calendar-cache-minutes", "15"))
