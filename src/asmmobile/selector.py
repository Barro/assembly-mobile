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

class EventSelector(object):
    now = None

    def construct(self, arguments):
        return type(self)()

    def setNow(self, now):
        self.now = now
        return self


class AndSelector(EventSelector):
    def __init__(self, subSelectors):
        self.subSelectors = subSelectors

    def __call__(self, event):
        for selector in self.subSelectors:
            if not selector(event):
                return False
        return True


class CurrentEvents(EventSelector):
    def __call__(self, event):
        return event.start <= self.now and self.now < event.end


class FutureEvents(EventSelector):
    def __call__(self, event):
        return self.now < event.start


class LocationEvents(EventSelector):
    def __init__(self):
        self.locationizedEvents = {}

    def __call__(self, event):
        location = event.majorLocation
        if location in self.locationizedEvents:
            if event.start == self.locationizedEvents[location]:
                return True
            else:
                return False
        else:
            self.locationizedEvents[location] = event
            return True


class NotEndedEvents(EventSelector):
    def __call__(self, event):
        return self.now < event.end


class NotHiddenEvents(EventSelector):
    def __call__(self, event):
        if self.now + event.majorLocation.hideUntil < event.start:
            return False
        return True


class MaximumEvents(EventSelector):
    def __init__(self, maximumEvents):
        self.maximumEvents = maximumEvents
        self.selected = 0
        self.lastSelected = None

    def construct(self, arguments):
        return type(self)(int(arguments))

    def __call__(self, event):
        if self.selected < self.maximumEvents:
            self.lastSelected = event
            self.selected += 1
            return True

        # Make sure that we select all events that are starting at certain
        # time.
        if self.lastSelected.start == event.start:
            return True

        return False


class StartedEvents(EventSelector):
    def __call__(self, event):
        return event.start <= self.now


types = {
    "one-per-location": LocationEvents(),
    "not-hidden": NotHiddenEvents(),
    "maximum-amount": MaximumEvents(0),
    }
