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
import urlparse
import time

from asmmobile.components import MobileView
import asmmobile.interfaces as interfaces
import asmmobile.util as util

class EventOwnerWrapper(grok.Model):
    def __init__(self, contentType, context, request):
        self.contentType = contentType
        self.context = context
        self.request = request

    @property
    def events(self):
        return self.context.getEvents(self.request)

    @property
    def lastModified(self):
        return self.context.getLastModified(self.request)


class ICalendarWrapper(grok.View):
    """The view that contains the iCalendar events."""
    grok.context(EventOwnerWrapper)


class ICalendar(MobileView):
    """The view that contains the iCalendar events."""

    template = None

    grok.context(EventOwnerWrapper)
    grok.name("index")

    def _initialize(config):
        cls = ICalendar
        cls.cacheTime = util.defaultCacheTime(config)

    util.runDeferred(_initialize)

    def update(self):
        self.response.setHeader('Content-Type', self.context.contentType)

        self.request.response.setHeader(
            'Last-Modified', util.httpTime(self.context.lastModified))

    def render(self):
        page = ICalendarWrapper(self.context, self.request)
        page.events = self.context.events
        page.now = self.now
        page.domain = urlparse.urlparse(self.application_url()).hostname
        return page().replace("\n", "\r\n")


class EventCalendarTraverser(grok.Traverser):
    grok.context(interfaces.IEventOwner)

    def traverse(self, name):
        if name.endswith('.vcs'):
            return EventOwnerWrapper(
                "text/x-vCalendar", self.context, self.request)
        elif name.endswith('.ics'):
            return EventOwnerWrapper(
                "text/calendar", self.context, self.request)
        return None


class ICalTimeView(grok.View):
    grok.context(datetime.datetime)
    grok.name("ical")

    def render(self):
        utcTime = self.context.utctimetuple()
        return time.strftime('%Y%m%dT%H%M%SZ', utcTime)


class ICalEncodedUnicode(grok.View):
    grok.context(unicode)
    grok.name("ical")

    def render(self):
        return util.icalEscape(self.context)
