#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Assembly mobile - mobile content for visitors of Assembly computer festival.
# Copyright (C) 2009  Assembly Organizing
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3 of the
# License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import urlparse
import re
import datetime

EVENTS = 'event'
LOCATIONS = 'location'

NAME_MAX_LENGTH = 60
NAME_SHORTEN_TO = 55
NON_WORD_CHARACTERS = "-#:,. "
CUT_POSTFIX = "..."

def shortenName(name):
    shortName = re.sub("ARTtech seminars - ", "", name)
    # Name is too long. Cut it so that the three dots (...) come directly after
    # the last full word.
    if len(shortName) > NAME_MAX_LENGTH:
        # Cut to maximum length of a name.
        newShortName = shortName[:NAME_SHORTEN_TO]
        # Reverse name to cut to last full word.
        reversedName = newShortName[::-1]
        firstNonAlpha = 0
        # Find the beginning of last partial word.
        while reversedName[firstNonAlpha] not in NON_WORD_CHARACTERS:
            firstNonAlpha += 1
        # Find the end of last full word
        while reversedName[firstNonAlpha] in NON_WORD_CHARACTERS:
            firstNonAlpha += 1
        # Cut the not wanted characters from the end of the name.
        reversedName = reversedName[firstNonAlpha:]
        # Reverse the name
        newShortName = reversedName[::-1]
        # Add dots to cut name to indicate cutting.
        shortName = newShortName + CUT_POSTFIX
    return shortName

def applicationRelativeUrl(view, name):
    targetUrl = view.application_url(name)
    myUrl = view.url()
    maxCommon = 0
    minLength = min(len(targetUrl), len(myUrl))
    while (maxCommon < minLength
           and targetUrl[maxCommon] == myUrl[maxCommon]):
        maxCommon += 1
    if maxCommon == len(myUrl):
        return myUrl.split("/")[-1]
    elif "/" not in myUrl[maxCommon:]:
        return targetUrl[maxCommon:]
    else:
        return urlparse.urlparse(targetUrl)[2]


def locationUrl(view, location):
    return "%s/%s" % (applicationRelativeUrl(view, LOCATIONS),
                      location.__name__)


def eventUrl(view, event):
    return "%s/%s" % (applicationRelativeUrl(view, EVENTS),
                      event.__name__)


INTERVAL_ZERO_SECONDS = datetime.timedelta(seconds=0)
INTERVAL_ONE_MINUTE = datetime.timedelta(minutes=1)

def getTimeHourMinute(interval):
    """Returns time interval in human readable format.

    Examples:
    1 h 23 min
    23 min

    If interval is zero seconds, then this returns an empty string.

    @param interval Object with same interface as datetime.timedelta.
    """
    if interval == INTERVAL_ZERO_SECONDS:
        return ""
    # Ceiling to next minute.
    if interval.seconds + interval.microseconds/1000000.0 > 0:
        # Adding one minute. Next call will floor the time to exact minute.
        interval += INTERVAL_ONE_MINUTE
    intervalMinutes = (interval.days*86400 + interval.seconds)/60
    hours = intervalMinutes/60
    minutes = intervalMinutes%60
    timeList = []
    if hours > 0:
        timeList.append("%d h" % hours)
    if minutes > 0:
        timeList.append("%d min" % minutes)
    return " ".join(timeList)


class DisplayEvent(object):
    def __init__(self, view, event, timeString):
        self.id = event.__name__
        self.shortname = shortenName(event.name)
        self.name = event.name
        self.url = "%s/%s" % (view.application_url(EVENTS), self.id)
        self.shorturl = eventUrl(view, event)
        self.description = event.description
        self.categories = event.categories

        # Time string is either string that indicates how much is remaining of
        # an event, how long there is till next event or how long the event is
        # depending on event type and view.
        self.timeString = timeString

        self.locationName = event.location.name
        self.locationUrl = locationUrl(view, event.location)

        self.start = event.start
        self.end = event.end
        self.length = event.length


class GroupingLocation(object):
    def __init__(self, name, url, priority, currentEvents, nextEvents):
        self.name = name
        self.url = url
        self.priority = priority
        self.currentEvents = currentEvents
        self.nextEvents = nextEvents


def getEventList(view,
                 events,
                 timeGetter,
                 locationAdder,
                 outLocations):
    result = []
    for event in events:
        locationName = event.location.name
        displayEvent = DisplayEvent(view,
                                    event,
                                    getTimeHourMinute(timeGetter(event)))
        result.append(displayEvent)
        location = event.majorLocation
        if location not in outLocations:
            outLocations[location] = GroupingLocation(event.location.name,
                                                      event.location.url,
                                                      event.location.priority,
                                                      [],
                                                      [])
        locationAdder(displayEvent, location, outLocations)
    return result
