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
import grok
import string

import interfaces

EVENTS = 'event'
LOCATIONS = 'location'

NAME_MAX_LENGTH = 60
NAME_SHORTEN_TO = 55
NON_WORD_CHARACTERS = "-#:,. "
CUT_POSTFIX = "..."

class KeyNormalize(grok.View):
    grok.context(unicode)
    grok.name("keynormalize")

    locationKeyChars = (string.ascii_letters.decode('ascii') \
                            + string.digits.decode('ascii'))

    def render(self):
        return re.sub(ur'([^%s]+)' % self.locationKeyChars, ur'_',
                      self.context.lower()).strip("_")


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


def applicationRelativeUrl(view, obj=None):
    targetUrl = view.application_url(obj)
    myUrl = view.url()

    if not (view.request.environment['PATH_INFO'].endswith("/")
            or view.request.environment['PATH_INFO'].endswith(view.__name__)):
        pass
        #myUrl += "/"

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

class IntervalHourMinute(grok.View):
    """Returns time interval in human readable format.

    Examples:
    (1 h 23 min)
    (23 min)

    If interval is zero seconds, then this returns an empty string.

    @param interval Object with same interface as datetime.timedelta.
    """

    grok.context(datetime.timedelta)
    grok.name("hourminute")

    def render(self):
        if self.context == INTERVAL_ZERO_SECONDS:
            return u""
        interval = self.context
        # Ceiling to next minute.
        if interval.seconds % 60 != 0:
            # Adding one minute. Next call will floor the time to exact minute.
            interval += INTERVAL_ONE_MINUTE
        intervalMinutes = (interval.days*86400 + interval.seconds)/60
        hours = intervalMinutes/60
        minutes = intervalMinutes%60
        timeList = []
        if hours > 0:
            timeList.append(u"%d h" % hours)
        if minutes > 0:
            timeList.append(u"%d min" % minutes)
        return u" ".join(timeList)


class IntervalHourMinuteParenthesis(IntervalHourMinute):
    grok.name("hourminuteparenthesis")

    def render(self):
        result = super(IntervalHourMinuteParenthesis, self).render()
        if len(result):
            return u"(%s)" % result
        else:
            return result


class TimeHourMinute(grok.View):
    grok.context(datetime.datetime)
    grok.name("hourminute")

    def render(self):
        return self.context.strftime("%H:%M")


class TimeDayname(grok.View):
    grok.context(datetime.datetime)
    grok.name("dayname")

    def render(self):
        return self.context.strftime("%A")


class DisplayEvent(object):
    def __init__(self, view, event, timeTillChangePoint):
        self.id = event.__name__
        self.shortname = shortenName(event.name)
        self.name = event.name
        self.url = "%s/%s" % (view.application_url(EVENTS), self.id)
        self.shorturl = eventUrl(view, event)
        self.description = event.description
        self.categories = event.categories

        self.locationName = event.location.name
        self.locationUrl = locationUrl(view, event.location)

        self.timeTillChangePoint = timeTillChangePoint

        self.start = event.start
        self.end = event.end
        self.length = event.length

    @property
    def isMajor(self):
        return 'Major_event' in self.categories


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
                                    timeGetter(event))
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



def ceilToNextMinute(self, utcnow):
    maxAge = 60 - utcnow.second%60
    return datetime.timedelta(seconds=(maxAge))


class AddTime(object):
    def __init__(self, addAmount):
        self.addAmount = addAmount

    def __call__(self, utcnow):
        return self.addAmount
