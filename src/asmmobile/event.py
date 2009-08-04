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

import datetime
import grok
import asmmobile.interfaces
from mobile import MobileView
from util import getTimeHourMinute, DisplayEvent

def _sortByStartTime(first, second):
    return cmp(first.start, second.start)

class EventContainer(grok.Container):
    grok.implements(asmmobile.interfaces.IEventContainer)

    def updateEvents(self, values):
        currentKeys = set(self.keys())
        newKeys = set(values.keys())

        removeKeys = currentKeys.difference(newKeys)
        for key in removeKeys:
            del self[key]

        addKeys = newKeys.difference(currentKeys)
        for key in addKeys:
            eventValues = values[key]
            self[key] = Event(name=eventValues['name'],
                              start=eventValues['start'],
                              end=eventValues['end'],
                              location=eventValues['location'],
                              url=eventValues['url'])

        updateKeys = newKeys.intersection(currentKeys)
        for key in updateKeys:
            eventValues = values[key]
            event = self[key]
            event.name = eventValues['name']
            event.start = eventValues['start']
            event.end = eventValues['end']
            event.location = eventValues['location']
            event.url = eventValues['url']

    def getEvents(self, eventFilter):
        events = list(self.values())
        events.sort(_sortByStartTime)
        return filter(eventFilter, events)


class Event(grok.Model):
    grok.implements(asmmobile.interfaces.IEvent)

    def __init__(self,
                 name,
                 start,
                 end,
                 location,
                 url,
                 description=None,
                 categories=[]):
        self.name = name
        self.start = start
        self.end = end
        self.location = location
        self.url = url
        self.description = description
        self.categories = categories

    def getMajorLocation(self):
        return self.location.majorLocation

    majorLocation = property(getMajorLocation)

    def getLength(self):
        return self.end - self.start

    length = property(getLength)


class EventIndex(grok.View, MobileView):
    grok.name("index")
    grok.context(Event)

    zeroSeconds = datetime.timedelta(seconds=0)

    def getTitle(self):
        return self.context.name

    title = property(getTitle)

    def formatInterval(self, interval):
        return getTimeHourMinute(interval)

    def update(self):
        self.mobileUpdate()

class EventIcal(grok.View, MobileView):
    grok.name("event.ical")
    grok.context(Event)

    def update(self):
        self.mobileUpdate()
        self.response.setHeader('Content-Type', "text/calendar")

        self.events = [DisplayEvent(self, self.context, "")]
