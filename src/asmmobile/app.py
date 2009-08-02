#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Assembly mobile - mobile content for visitors of Assembly computer festival.
# Copyright (C) 2009  Jussi Judin
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
import icalendar
import zope.interface
import asmmobile.interfaces
import datetime

import re

import asmmobile.location
import asmmobile.event

from asmmobile import AsmMobileMessageFactory as _

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

    def getCss(self):
        fp = open("src/asmmobile/static/asmmobile.css", "r")
        data = fp.read()
        fp.close()
        compressed = data
        newlinesMatch = re.compile(r" *\n *")
        compressed = newlinesMatch.sub("", compressed)
        separatorMatch = re.compile(r" *([,:\{;]) *")
        compressed = separatorMatch.sub(r"\1", compressed)
        return compressed


    def getCurrentEvents(self, now):
        return self['events'].getCurrentEvents(now)


    def getNextEvents(self, now):
        return self['events'].getNextEvents(now)


_TIME_FACTORY = datetime.datetime(2000, 1, 1)


class MobileView(object):


    def setHeaders(self):
        self.response.setHeader("Content-Type", "text/html; charset=UTF-8")
        nextMinute = _TIME_FACTORY.utcnow()
        nextMinute += datetime.timedelta(seconds=(60 - nextMinute.second%60))
        self.response.setHeader("Expires",
                                nextMinute.strftime("%a, %d %b %Y %H:%M:%S +0000"))


    def updateMobile(self):
        self.setHeaders()

#         requestTime = None
#         if requestTime is None:
# f            requestTime = timeFactory.now().strftime("%Y%m%d%H%M")
        self.now = _TIME_FACTORY.now()


    def getTime(self):
        timeFormat = "%Y-%m-%d %H:%M %z"
        return _(u"Current time: %s" % self.now.strftime(timeFormat))


class DisplayEvent(object):
    def __init__(self, name, url, timeString, locationName, locationUrl):
        self.name = name
        self.url = url
        self.timeString = timeString
        self.locationName = locationName
        self.locationUrl = locationUrl

def getTimeHourMinute(interval):
    intervalMinutes = (interval.days*86400 + interval.seconds)/60
    if intervalMinutes >= 60:
        hours = intervalMinutes/60
        minutes = intervalMinutes%60
        return "%d h %d min" % (hours, minutes)
    else:
        return "%d min" % intervalMinutes


class Index(grok.View, MobileView):
    title = _(u"Assembly mobile")

    def update(self):
        self.updateMobile()

        now = datetime.datetime(2009, 8, 7, 18, 3)

        self.currentEvents = []
        for event in self.context.getCurrentEvents(now):
            self.currentEvents.append(
                DisplayEvent(event.name,
                             event.url,
                             getTimeHourMinute(event.end - now),
                             event.location.name,
                             event.location.url))

        self.nextEvents = []
        for event in self.context.getNextEvents(now):
            self.nextEvents.append(
                DisplayEvent(event.name,
                             event.url,
                             getTimeHourMinute(event.start - now),
                             event.location.name,
                             event.location.url))


class ScheduleTime(grok.View, MobileView):
    grok.name("schedule-time")

    title = _(u"Schedule by time")

    def update(self):
        self.updateMobile()

        self.events = self.context.getEvents()


class ScheduleLocation(grok.View, MobileView):
    grok.name("schedule-location")

    title = _(u"Schedule by location")

    def update(self):
        self.updateMobile()


class Layout(grok.View):
    """The view that contains the main view."""
    grok.context(zope.interface.Interface)

