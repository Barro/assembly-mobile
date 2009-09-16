import csv
import datetime

def parseCsvDate(dateString):
    # Date is in format:
    # Mon 14.7.09 18:00
    dayName, date, time = dateString.split(" ")
    day, month, year = (int(x) for x in date.split("."))
    hour, minute = (int(x) for x in time.split(":"))
    return datetime.datetime(2000 + year, month, day, hour, minute)


def importer(filename, prefix, language):
    # Schedule is in format:
    # FIELDNAME1;FIELDNAME2;...
    # field_value1;field_value2;...
    fp = open(filename, "r")
    reader = csv.DictReader(fp, delimiter=';')
    locations = {}
    events = {}
    for entry in reader:
        if entry['Public'] == 'No':
            continue
        # Ignore empty entries:
        if entry['Title_' + language] == "":
            continue
        locationName = entry['Location_' + language]
        locationUrl = entry['Location_URL']
        # Add absolute URL to main website if location is relative
        if not locationUrl.startswith("http"):
            locationUrl = "http://www.assembly.org%s" % locationUrl

        locations[locationName] = locationUrl
        startTime = parseCsvDate(entry['Start_Date'])
        eventId = "%s%d_%s" % (prefix, startTime.year, entry['ID'])
        categories = []
        if entry['Major'] == 'Yes':
            categories.append("Major_event")
        if len(entry['Class']) > 0:
            categories += entry['Class'].split(" ")

        url = entry['URL']
        # Add absolute URL to main website if location is relative
        if not url.startswith("http"):
            url = "http://www.assembly.org%s" % url

        events[eventId] = {'name': entry['Title_' + language],
                           'url': url,
                           'start': startTime,
                           'end': parseCsvDate(entry['Finish_Date']),
                           'location': locationName,
                           'categories': categories,
                           }
    return (locations, events)
