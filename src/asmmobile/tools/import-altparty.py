import xml.etree.ElementTree as etree
import dateutil.parser
import datetime

def importer(filename, prefix):
    events = {}
    locations = {}
    for event in etree.parse(filename).getroot():
        if event.find("public").text != "true":
            continue
        id = prefix + event.find("id").text
        start = dateutil.parser.parse(event.find("start-at").text)
        end = start + \
            datetime.timedelta(minutes=int(event.find("duration").text))
        location = event.find("location").text
        description = event.find("description").text
        events[id] = {'name': event.find("title").text,
                      'start': start,
                      'end': end,
                      'location': location,
                      'description': description,
                      'url': '',
                      'categories': [],
                      }
        locations[location] = ""

    return (locations, events)

