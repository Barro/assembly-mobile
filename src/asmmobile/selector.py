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

class EventSelector(object):
    _now = None
    utcNow = None

    def reset(self, now):
        return self.setNow(now)

    def setNow(self, now):
        self._now = now
        if now is not None:
            self.utcNow = now.utctimetuple()
        else:
            self.utcNow = None
        return self


class AndSelector(EventSelector):
    def __init__(self, subSelectors):
        self.subSelectors = subSelectors

    def __call__(self, event):
        for selector in self.subSelectors:
            if not selector(event):
                return False
        return True


class OrSelector(EventSelector):
    def __init__(self, subSelectors):
        self.subSelectors = subSelectors

    def __call__(self, event):
        for selector in self.subSelectors:
            if selector(event):
                return True
        return False


class CurrentEvents(EventSelector):
    def __call__(self, event):
        return event.utcStart <= self.utcNow and self.utcNow < event.utcEnd


class FutureEvents(EventSelector):
    def __call__(self, event):
        return self.utcNow < event.utcStart


class LocationEvents(EventSelector):
    def __init__(self):
        self.reset(None)

    def reset(self, now):
        self.locationizedEvents = {}
        return super(LocationEvents, self).reset(now)

    def construct(self, arguments):
        return LocationEvents()

    def __call__(self, event):
        location = event.majorLocation
        # XXX WTF?
        if location in self.locationizedEvents:
            if event == self.locationizedEvents[location]:
                return True
            else:
                return False
        else:
            self.locationizedEvents[location] = event
            return True


class NotEndedEvents(EventSelector):
    def construct(self, arguments):
        return NotEndedEvents()

    def __call__(self, event):
        return self.utcNow < event.utcEnd


class NotHiddenEvents(EventSelector):
    """Shows events that according to current start time are supposed start
    in a short while."""

    def construct(self, arguments):
        return NotHiddenEvents()

    def __call__(self, event):
        utcHide = (self._now + event.majorLocation.hideUntil).utctimetuple()
        if utcHide < event.utcStart:
            return False
        return True


class NotHiddenOriginalEvents(EventSelector):
    """Shows events that according to original start time are supposed start
    in a short while."""

    def construct(self, arguments):
        return NotHiddenOriginalEvents()

    def __call__(self, event):
        if event.startOriginal is not None:
            utcHide = (self._now + event.majorLocation.hideUntil).utctimetuple()
            if utcHide < event.utcStartOriginal:
                return False
            return True
        else:
            return False


class StartTimeChangedEvents(EventSelector):
    def construct(self, arguments):
        return StartTimeChangedEvents()

    def __call__(self, event):
        return event.utcStart != event.utcStartOriginal


class CanceledEvents(EventSelector):
    def construct(self, arguments):
        return CanceledEvents()

    def __call__(self, event):
        return event.canceled


class MaximumEvents(EventSelector):
    def __init__(self, maximumEvents):
        self.maximumEvents = maximumEvents
        self.reset(None)

    def reset(self, now):
        self.selected = 0
        self.lastSelected = None
        return super(MaximumEvents, self).reset(now)

    def construct(self, arguments):
        return MaximumEvents(int(arguments))

    def __call__(self, event):
        if self.selected < self.maximumEvents:
            self.lastSelected = event
            self.selected += 1
            return True

        # Make sure that we select all events that are starting at certain
        # time.
        if self.lastSelected.utcStart == event.utcStart:
            return True

        return False


class StartedEvents(EventSelector):
    def __call__(self, event):
        return event.utcStart <= self.utcNow


types = {
    "one-per-location": LocationEvents(),
    "not-hidden": NotHiddenEvents(),
    "maximum-amount": MaximumEvents(0),
    }
