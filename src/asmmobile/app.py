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

import grokcore.component
import grokcore.view.components
import grokcore.view.interfaces

import zope.interface
import asmmobile.interfaces
import datetime

import re

import asmmobile.location
import asmmobile.event
from mobile import MobileView
from util import getEventList, LOCATIONS, EVENTS, DisplayEvent
import asmmobile.mobile

from asmmobile import AsmMobileMessageFactory as _

from zope.publisher.interfaces import INotFound
from zope.security.interfaces import IUnauthorized
from zope.app.exception.systemerror import SystemErrorView


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


class MobileTemplate(grokcore.view.components.PageTemplate):
    charset = "utf-8"

    def render(self, view):
        return super(MobileTemplate, self).render(view).encode(self.charset)


class MobileTemplateFactory(grok.GlobalUtility):
    grok.implements(grokcore.view.interfaces.ITemplateFileFactory)
    grok.name('ptm')

    def __call__(self, filename, _prefix=None):
        return MobileTemplate(filename=filename, _prefix=_prefix)


class AsmMobile(grok.Application, grok.Container):
    zope.interface.implements(asmmobile.interfaces.IAsmMobile)

    otherLanguage = _(u"link|other_language", default=u'/')

    partyName = u"Assembly Summer 2009"

    def __init__(self, **vars):
        super(AsmMobile, self).__init__(**vars)

        self[LOCATIONS] = asmmobile.location.LocationContainer()
        self[EVENTS] = asmmobile.event.EventContainer()

    def getEvents(self):
        return self[EVENTS]

    events = property(getEvents)


    def getLocations(self):
        return self[LOCATIONS]

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
                                     'location': location,
                                     'categories': values['categories'],
                                     }

        self.events.updateEvents(updateEvents)

    def getCurrentEvents(self, now):
        eventFilter = lambda event : (event.start <= now and now < event.end)
        return self.events.getEvents(eventFilter)


    def getNextEvents(self, now):
        return self.events.getEvents(NextEventFilter(now))

    def getEvents(self, eventFilter=None):
        return self.events.getEvents(eventFilter)

    def getLocationEvents(self, location):
        eventFilter = lambda event : (event.location == location)
        return self.events.getEvents(eventFilter)


def _reverseOrderByMajorLocation(first, second):
    result = cmp(second.majorLocation.priority,
                 first.majorLocation.priority)
    # If events are of equal priority, order by their ID
    if result == 0:
        return cmp(first.id, second.id)
    return result


class Index(MobileView):
    title = _(u"Assembly Mobile")
    grok.context(AsmMobile)

    def _getCurrentNextEvents(self, now):
        locations = {}
        currentEvents = self.context.getCurrentEvents(now)
        currentEvents.sort(_reverseOrderByMajorLocation)
        self.currentEvents = \
            getEventList(self,
                         currentEvents,
                         (lambda event: event.end - now),
                         (lambda event, location, outLocations:
                          outLocations[location].currentEvents.append(event)),
                         locations)

        nextEvents = self.context.getNextEvents(now)
        nextEvents.sort(_reverseOrderByMajorLocation)
        self.nextEvents = \
            getEventList(self,
                         nextEvents,
                         (lambda event: event.start - now),
                         (lambda event, location, outLocations:
                          outLocations[location].nextEvents.append(event)),
                         locations)

        self.locations = locations.values()


    def _getPartyStatus(self, now, nextEvents):
        allEvents = self.context.getEvents()
        hasUpcomingEvents = len(nextEvents) > 0
        haveEvents = len(allEvents) > 0
        self.partyHasStarted = haveEvents and allEvents[0].start <= now
        self.partyHasEnded = haveEvents and allEvents[-1].end < now
        partyIsOngoing = (haveEvents and \
                              self.partyHasStarted and not self.partyHasEnded)
        # Event might be starting in a while so we event can be ongoing even
        # though no event has started yet.
        if hasUpcomingEvents or partyIsOngoing:
            self.partyIsOngoing = True
        else:
            self.partyIsOngoing = False


    def update(self):
        self._getCurrentNextEvents(self.now)
        self._getPartyStatus(self.now, self.nextEvents)



class ScheduleTime(MobileView):
    grok.name("full-schedule")
    grok.context(AsmMobile)

    title = _(u"Full schedule")

    startDifference = datetime.timedelta(hours=2)
    endDifference = datetime.timedelta(hours=10)

    dateFormat = "%Y-%m-%d-%H"
    dateValidate = re.compile(r"\d\d\d\d-\d\d-\d\d-\d\d")

    def update(self, s=None):

        if s is not None and self.dateValidate.match(s):
            (year, month, day, hour) = (int(x) for x in s.split("-"))
            displayCenter = datetime.datetime(year=year,
                                              month=month,
                                              day=day,
                                              hour=hour)
        else:
            displayCenter = self.now

        # Round to next full hour.
        secondsTillNextHour = \
            (3600 - (displayCenter.second + displayCenter.minute * 60))%3600
        displayCenter += datetime.timedelta(seconds=secondsTillNextHour)

        displayStart = displayCenter - self.startDifference
        displayEnd = displayCenter + self.endDifference

        self.previousCenter = \
            (displayStart - self.endDifference).strftime(self.dateFormat)
        self.nextCenter = \
            (displayEnd + self.startDifference).strftime(self.dateFormat)

        events = self.context.getEvents(
            (lambda event: displayStart < event.end \
                 and event.start <= displayEnd))

        # If the first displayable event is the same as the first event out of
        # all events, we don't have any more events in past and disable the
        # "previous 24 hours" link.
        allEvents = self.context.getEvents()
        if len(events) > 0 and events[0] != allEvents[0]:
            self.showPrevious = True
        else:
            self.showPrevious = False

        # If the first displayable event is the same as the last event out of
        # all events, we don't have any more events in future and disable the
        # "next 24 hours" link.
        if len(events) > 0 and events[-1] != allEvents[-1]:
            self.showNext = True
        else:
            self.showNext = False

        self.events = getEventList(self,
                                   events,
                                   (lambda event: event.length),
                                   (lambda event, location, outLocations: True),
                                   {})
        self.anchorEvent = None
        previousEvent = None
        for event in self.events:
            if event.start >= self.now:
                self.anchorEvent = previousEvent
                break
            previousEvent = event


class Layout(MobileView):
    """The view that contains the main layout."""
    grok.context(zope.interface.Interface)


class Favicon(grok.View):
    grok.context(zope.interface.Interface)

    grok.name("favicon.ico")

    def render(self):
        return self.static.get("favicon.ico").GET()


class ScheduledEvent(grok.View):
    grok.context(DisplayEvent)


class AllEvents(MobileView):
    grok.name("all-events")
    grok.context(AsmMobile)

    title = _(u"All events")

    def update(self):

        self.events = getEventList(self,
                                   self.context.getEvents(),
                                   (lambda event: event.length),
                                   (lambda event, location, outLocations: True),
                                   {})

        self.length = self.events[-1].end - self.events[0].start
