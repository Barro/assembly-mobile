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
import string
import re

import grok

import asmmobile.util as util
import asmmobile.interfaces as interfaces
from asmmobile.components import MobileView
from asmmobile.util import getEventList

class EditDescription(grok.Permission):
    grok.name('asmmobile.Edit')


class LocationContainer(grok.Container):
    grok.implements(interfaces.ILocationContainer)

    def addLocation(self,
                    keyName,
                    name,
                    url=None,
                    priority=None,
                    hideUntil=None,
                    majorLocation=None):
        if keyName in self:
            location = self[keyName]
            if name != location.name:
                location.name = name
            if url is not None:
                location.url = url
            if priority is not None:
                location.priority = priority
            if hideUntil is not None:
                location.hideUntil = hideUntil
            if majorLocation is not None:
                location.majorLocation = majorLocation
        else:
            location = Location(name=name,
                                url=url,
                                priority=priority,
                                hideUntil=hideUntil,
                                majorLocation=majorLocation)
            self[keyName] = location

        return location


    def getLocation(self, name):
        return self[util.convertNameToKey(name)]

    def application(self):
        return self.__parent__


class Index(MobileView):
    grok.context(LocationContainer)
    grok.name("index")

    title = u"Locations"

    def locations(self):
        return self.context.values()


class Location(grok.Model):
    grok.implements(interfaces.ILocation, interfaces.IEventOwner)

    DEFAULT_PRIORITY = 0
    DEFAULT_HIDE_TIME = datetime.timedelta(hours=2)

    def __init__(self,
                 name,
                 url,
                 description=None,
                 priority=None,
                 hideUntil=None,
                 majorLocation=None):
        self.name = name
        self.url = url
        self.description = description

        if priority is None:
            self.priority = Location.DEFAULT_PRIORITY
        else:
            self.priority = priority

        if hideUntil is None:
            self.hideUntil = Location.DEFAULT_HIDE_TIME
        else:
            self.hideUntil = hideUntil

        if majorLocation is None:
            self.majorLocation = self
        else:
            self.majorLocation = majorLocation

    def getHideUntil(self):
        # Get parent hiding time to be hiding time of this location.
        return self.majorLocation.hideUntil

    def getEvents(self):
        return self.application().getLocationEvents(self)

    def application(self):
        return self.__parent__.application()

    @property
    def events(self):
        return self.getEvents()


class LocationIndex(MobileView):
    grok.name("index")
    grok.context(Location)

    cacheTime = util.AddTime(datetime.timedelta(minutes=15))

    zeroSeconds = datetime.timedelta(seconds=0)

    def getTitle(self):
        return self.context.name

    title = property(getTitle)

    def update(self):
        events = self.context.getEvents()
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


class Edit(grok.EditForm):
    grok.require("asmmobile.Edit")
    grok.context(Location)

    form_fields = grok.AutoFields(Location)
    form_fields['name'].custom_widget = util.LongTextWidget
    form_fields['url'].custom_widget = util.LongTextWidget


class ViewUrl(grok.View):
    grok.name("url")
    grok.context(Location)

    def render(self):
        return "%s/%s" % (util.applicationRelativeUrl(self, 'location'),
                          self.context.__name__)
