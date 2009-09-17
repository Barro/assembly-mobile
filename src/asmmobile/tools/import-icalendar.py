import icalendar
import dateutil.tz

def importer(filename, prefix='', locationMap={}):
    calFp = open(filename, "r")
    cal = icalendar.Calendar.from_string(calFp.read())
    calFp.close()

    locations = {}
    events = {}
    for event in cal.walk('vevent'):
        id = event.decoded('uid')
        start = event.decoded('DTSTART').replace(tzinfo=dateutil.tz.tzlocal())
        end = event.decoded('DTEND').replace(tzinfo=dateutil.tz.tzlocal())
        categories = event.decoded('CATEGORIES').split(" ")
        url = event.decoded('URL', u'')
        name = event.decoded('SUMMARY', u'')

        location = event.decoded('LOCATION', u'')
        if location in locationMap:
            location = locationMap[location]

        locations[location] = ""

        events[id] = {'name': name,
                      'start': start,
                      'end': end,
                      'url': url,
                      'location': location,
                      'categories': categories,
                      }

    return (locations, events)


