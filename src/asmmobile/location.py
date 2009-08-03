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

class LocationContainer(grok.Container):
    grok.implements(asmmobile.interfaces.ILocationContainer)

    def addLocation(self,
                    name,
                    url=None,
                    priority=None,
                    hideUntil=None,
                    majorLocation=None):
        keyName = name.lower()

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
        return self[name.lower()]


class Location(grok.Model):
    grok.implements(asmmobile.interfaces.ILocation)

    DEFAULT_PRIORITY = 0
    DEFAULT_HIDE_TIME = datetime.timedelta(hours=2)

    def __init__(self,
                 name,
                 url,
                 priority=None,
                 hideUntil=None,
                 majorLocation=None):
        self.name = name
        self.url = url

        if priority is None:
            self.priority = Location.DEFAULT_PRIORITY
        else:
            self.priority = priority

        if hideUntil is None:
            self.hideUntil = Location.DEFAULT_HIDE_TIME
        else:
            self.hideUntil = hideUntil

        if not majorLocation:
            self.majorLocation = self
        else:
            self.majorLocation = majorLocation

    def getHideUntil(self):
        # Get parent hiding time to be hiding time of this location.
        return self.majorLocation.hideUntil
