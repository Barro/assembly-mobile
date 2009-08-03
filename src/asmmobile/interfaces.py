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

import zope.interface

class IAsmMobile(zope.interface.Interface):
    """Marker interface for the application object."""

    def addLocation(name, url, priority, hideUntil, majorLocationName):
        pass

    def getCurrentEvents(currentTime):
        """Returns all events that are currently going on.

        @param currentTime Time that represents current time.
        """

    def getNextEvents(currentTime):
        """Returns all events that are going to happen next in some area.

        @param currentTime Time that represents current time.
        """


class IEventContainer(zope.interface.Interface):
    def updateEvents(values):
        pass

    def getEvents(eventFilter):
        """Returns a list of events filtered through eventFilter function.

        Events are given for filter function in ascending start time order.
        """

class IEvent(zope.interface.Interface):

    name = zope.interface.Attribute("")
    url = zope.interface.Attribute("")
    start = zope.interface.Attribute("")
    end = zope.interface.Attribute("")

    location = zope.interface.Attribute("")
    majorLocation = zope.interface.Attribute("")


class ILocationContainer(zope.interface.Interface):
    def addLocation(name, url, priority, hideUntil, majorLocation):
        pass

    def getLocation(name):
        pass


class ILocation(zope.interface.Interface):

    name = zope.interface.Attribute("")
    url = zope.interface.Attribute("")

    majorLocation = zope.interface.Attribute("")
    priority = zope.interface.Attribute("")
    hideUntil = zope.interface.Attribute("")
