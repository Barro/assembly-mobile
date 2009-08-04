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
from mobile import MobileView
from util import getTimeHourMinute
import asmmobile.mobile

from asmmobile import AsmMobileMessageFactory as _

from zope.publisher.interfaces import INotFound
from zope.security.interfaces import IUnauthorized
from zope.app.exception.systemerror import SystemErrorView

# class ErrorPage401(grok.View, SystemErrorView):
#     grok.context(IUnauthorized)
#     grok.name('index.html')

#     def render(self):
#         return "401"


# class ErrorPage404(grok.View, SystemErrorView):
#     grok.context(INotFound)
#     grok.name('index.html')

#     def render(self):
#         try:
#             self.redirect("index")
#         except ValueError, e:
#             print "REDIRECTFAILED %s" % e
#         return "404"

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


def locationUrl(location):
    return "%s/%s" % (AsmMobile.LOCATIONS, location.__name__)

def eventUrl(event):
    return "%s/%s" % (AsmMobile.EVENTS, event.__name__)

class AsmMobile(grok.Application, grok.Container):
    zope.interface.implements(asmmobile.interfaces.IAsmMobile)

    otherLanguage = _(u"link|other_language", default=u'/')

    EVENTS = 'event'
    LOCATIONS = 'location'

    def __init__(self, **vars):
        super(AsmMobile, self).__init__(**vars)

        self[self.LOCATIONS] = asmmobile.location.LocationContainer()
        self[self.EVENTS] = asmmobile.event.EventContainer()

    def getEvents(self):
        return self[self.EVENTS]

    events = property(getEvents)


    def getLocations(self):
        return self[self.LOCATIONS]

    locations = property(getLocations)

    def addLocation(self, name, url, priority, hideUntil, majorLocationName):
        if majorLocationName is not None:
            majorLocation = self.locations.getLocation(majorLocationName)
        else:
            majorLocation = None

        return self.locations.addLocation(name,
                                          url,
                                          priority,
                                          hideUntil,
                                          majorLocation)

    def updateEvents(self, events):
        updateEvents = {}
        for eventId, values in events.items():
            location = self.locations.getLocation(values['location'])
            updateEvents[eventId] = {'name': values['name'],
                                     'start': values['start'],
                                     'end': values['end'],
                                     'url': values['url'],
                                     'location': location}

        self.events.updateEvents(updateEvents)

    def getCurrentEvents(self, now):
        eventFilter = lambda event : (event.start <= now and now < event.end)
        return self.events.getEvents(eventFilter)


    def getNextEvents(self, now):
        return self.events.getEvents(NextEventFilter(now))

    def getEvents(self):
        return self.events.getEvents(None)

    def getLocationEvents(self, location):
        eventFilter = lambda event : (event.location == location)
        return self.events.getEvents(eventFilter)


class DisplayEvent(object):
    def __init__(self, event, timeString):
        self.name = asmmobile.mobile.shortenName(event.name)
        self.url = eventUrl(event)

        # Time string is either string that indicates how much is remaining of
        # an event, how long there is till next event or how long the event is
        # depending on event type and view.
        self.timeString = timeString

        self.locationName = event.location.name
        self.locationUrl = locationUrl(event.location)

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


def getEventList(events, timeGetter, locationAdder, outLocations):
    result = []
    for event in events:
        locationName = event.location.name
        displayEvent = DisplayEvent(event, getTimeHourMinute(timeGetter(event)))
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

        outLocations = {}
        events = self.context.getEvents()
        self.events = getEventList(events,
                                   (lambda event: event.length),
                                   (lambda event, location, outLocations: True),
                                   outLocations)
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
