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

import grok
import zope.interface
import asmmobile.interfaces
import datetime

import re

import asmmobile.location
import asmmobile.event

from asmmobile import AsmMobileMessageFactory as _

from zope.publisher.interfaces import INotFound
from zope.security.interfaces import IUnauthorized
from zope.app.exception.systemerror import SystemErrorView

class ErrorPage401(grok.View, SystemErrorView):
    grok.context(IUnauthorized)
    grok.name('index.html')

    def render(self):
        return "401"


class ErrorPage404(grok.View, SystemErrorView):
    grok.context(INotFound)
    grok.name('index.html')

    def render(self):
        try:
            self.redirect("index")
        except ValueError, e:
            print "REDIRECTFAILED %s" % e
        return "404"


class NextEventFilter(object):
    def __init__(self, now):
        self.now = now
        self.locationizedEvents = {}

    def __call__(self, event):
        if event.start <= self.now:
            return False

        if self.now + event.majorLocation.hideUntil < event.start:
            return False

        location = event.majorLocation
        if location in self.locationizedEvents:
            if event.start == self.locationizedEvents[location]:
                return True
            else:
                return False
        else:
            self.locationizedEvents[location] = event
            return True


class AsmMobile(grok.Application, grok.Container):
    zope.interface.implements(asmmobile.interfaces.IAsmMobile)

    otherLanguage = _(u"link|other_language", default=u'/')

    def __init__(self, **vars):
        super(AsmMobile, self).__init__(**vars)

        self['locations'] = asmmobile.location.LocationContainer()
        self['events'] = asmmobile.event.EventContainer()


    def addLocation(self, name, url, priority, hideUntil, majorLocationName):
        if majorLocationName is not None:
            majorLocation = self['locations'].getLocation(majorLocationName)
        else:
            majorLocation = None

        return self['locations'].addLocation(name,
                                             url,
                                             priority,
                                             hideUntil,
                                             majorLocation)

    def updateEvents(self, events):
        updateEvents = {}
        for eventId, values in events.items():
            location = self['locations'].getLocation(values['location'])
            updateEvents[eventId] = {'name': values['name'],
                                     'start': values['start'],
                                     'end': values['end'],
                                     'url': values['url'],
                                     'location': location}

        self['events'].updateEvents(updateEvents)

    def getCurrentEvents(self, now):
        eventFilter = lambda event : (event.start <= now and now < event.end)
        return self['events'].getEvents(eventFilter)


    def getNextEvents(self, now):
        return self['events'].getEvents(NextEventFilter(now))

    def getEvents(self):
        return self['events'].getEvents(None)


_TIME_FACTORY = datetime.datetime(2000, 1, 1)

class MobileView(object):

    def mobileUpdate(self):
        self.now = datetime.datetime(2009, 8, 7, 18, 3)

        self.request.response.setHeader("Content-Type", "text/html; charset=UTF-8")
        nextMinute = _TIME_FACTORY.utcnow()
        maxAge = 60 - nextMinute.second%60
        nextMinute += datetime.timedelta(seconds=(maxAge))
        self.request.response.setHeader(
            "Expires", nextMinute.strftime("%a, %d %b %Y %H:%M:%S +0000"))
        self.request.response.setHeader("Cache-Control", "max-age=%d" % maxAge)


    def getTime(self):
        timeFormat = "%Y-%m-%d %H:%M %z"
        return _(u"Current time: %s" % self.now.strftime(timeFormat))


    def getCss(self):
        fp = open("src/asmmobile/static/asmmobile.css", "r")
        compressed = fp.read()
        fp.close()
        newlinesMatch = re.compile(r" *\n *")
        compressed = newlinesMatch.sub("", compressed)
        separatorMatch = re.compile(r" *([,:\{;]) *")
        compressed = separatorMatch.sub(r"\1", compressed)
        return compressed


class DisplayEvent(object):
    def __init__(self, name, url, timeString, locationName, locationUrl):
        self.name = name
        self.url = url
        self.timeString = timeString
        self.locationName = locationName
        self.locationUrl = locationUrl


class GroupingLocation(object):
    def __init__(self, name, url, priority, currentEvents, nextEvents):
        self.name = name
        self.url = url
        self.priority = priority
        self.currentEvents = currentEvents
        self.nextEvents = nextEvents


def getTimeHourMinute(interval):
    intervalMinutes = (interval.days*86400 + interval.seconds)/60
    hours = intervalMinutes/60
    minutes = intervalMinutes%60
    timeList = []
    if hours > 0:
        timeList.append("%d h" % hours)
    if minutes > 0:
        timeList.append("%d min" % minutes)
    return " ".join(timeList)


def getEventList(events, timeGetter, locationAdder, outLocations):
    result = []
    for event in events:
        displayEvent = DisplayEvent(event.name,
                                    event.url,
                                    getTimeHourMinute(timeGetter(event)),
                                    event.location.name,
                                    event.location.url)
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


class Index(grok.View, MobileView):
    title = _(u"Assembly mobile")
    grok.context(AsmMobile)

    def update(self):
        self.mobileUpdate()

        locations = {}
        self.currentEvents = \
            getEventList(self.context.getCurrentEvents(self.now),
                         (lambda event: event.end - self.now),
                         (lambda event, location, outLocations:
                          outLocations[location].currentEvents.append(event)),
                         locations)

        self.nextEvents = \
            getEventList(self.context.getNextEvents(self.now),
                         (lambda event: self.now - event.start),
                         (lambda event, location, outLocations:
                          outLocations[location].nextEvents.append(event)),
                         locations)

        self.locations = locations.values()


class ScheduleTime(grok.View, MobileView):
    grok.name("schedule-time")
    grok.context(AsmMobile)

    title = _(u"Full schedule")

    zeroSeconds = datetime.timedelta(seconds=0)

    def formatInterval(self, interval):
        return getTimeHourMinute(interval)

    def update(self):
        self.mobileUpdate()

        self.events = self.context.getEvents()
        self.anchorEvent = None
        previousEvent = None
        for event in self.events:
            if event.start >= self.now:
                self.anchorEvent = previousEvent
                break
            previousEvent = event


class ScheduleLocation(grok.View, MobileView):
    grok.name("schedule-location")
    grok.context(AsmMobile)

    title = _(u"Schedule by location")

    zeroSeconds = datetime.timedelta(seconds=0)

    def formatInterval(self, interval):
        return getTimeHourMinute(interval)

    def update(self):
        self.mobileUpdate()

        self.events = self.context.getEvents()
        self.anchorEvent = None
        previousEvent = None
        for event in self.events:
            if event.start >= self.now:
                self.anchorEvent = previousEvent
                break
            previousEvent = event


class Layout(grok.View):
    """The view that contains the main layout."""
    grok.context(zope.interface.Interface)


class Favicon(grok.View):
    grok.context(zope.interface.Interface)

    grok.name("favicon.ico")

    def render(self):
        return self.static.get("favicon.ico").GET()
