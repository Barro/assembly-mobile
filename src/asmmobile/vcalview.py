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
import StringIO

from asmmobile.components import MobileView
import asmmobile.interfaces as interfaces
import asmmobile.util as util
import asmmobile.config as config

class EventOwnerWrapper(object):
    def __init__(self, contentType, events):
        self.contentType = contentType
        self.events = events


class ICalendarWrapper(grok.View):
    """The view that contains the iCalendar events."""
    grok.context(EventOwnerWrapper)


class ICalendar(MobileView):
    """The view that contains the iCalendar events."""

    template = None

    grok.context(EventOwnerWrapper)
    grok.name("index.html")

    cacheTime = util.AddTime(
        datetime.timedelta(minutes=config.eventCacheMinutes))

    def update(self):
        self.response.setHeader('Content-Type', self.context.contentType)

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
            return EventOwnerWrapper("text/x-vCalendar", self.context.events)
        elif name.endswith('.ics'):
            return EventOwnerWrapper("text/calendar", self.context.events)


class ICalTimeView(grok.View):
    grok.context(datetime.datetime)
    grok.name("ical")

    def render(self):
        # Render times in local time
        return self.context.strftime('%Y%m%dT%H%M%S')


class ICalEncodedString(grok.View):
    grok.context(unicode)
    grok.name("ical")

    escapeChars = {
        "\\": u"\\\\",
        ";": u"\\;",
        ",": u"\\,",
        "\n": u"\\n",
        }

    def render(self):
        buffer = StringIO.StringIO()
        for char in self.context:
            if char in self.escapeChars:
                buffer.write(self.escapeChars[char])
            else:
                buffer.write(char)
        return buffer.getvalue()
