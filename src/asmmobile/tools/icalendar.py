import icalendar

def importer(filename, prefix='', locationMap={}):
    calFp = open(filename, "r")
    cal = icalendar.Calendar.from_string(calFp.read())
    calFp.close()

    locations = {}
    events = {}
    for event in cal.walk('vevent'):
        id = event.decoded('uid')
        start = event.decoded('DTSTART')
        end = event.decoded('DTEND')
        categories = event.decoded('CATEGORIES').split(" ")
#         url = event.decoded('URL')
        url = u''
        name = event.decoded('SUMMARY')

        location = event.decoded('LOCATION')
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


