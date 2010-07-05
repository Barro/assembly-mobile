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

decorators = {}
types = {}

def name(first, second):
    return cmp(first.id, second.id)


def startTime(first, second):
    result = cmp(first.start, second.start)
    return result


def locationPriority(first, second):
    result = cmp(second.majorLocation.priority, first.majorLocation.priority)
    return result


def major(first, second):
    if first.isMajor and not second.isMajor:
        return -1
    if second.isMajor and not first.isMajor:
        return 1
    return 0

def reverse(function, parameters=None):
    def compare(first, second):
        return function(second, first)

    return compare


def ifEquals(function, parameters=None):
    comparator = types[parameters]

    def compare(first, second):
        result = function(first, second)
        if result == 0:
            return comparator(first, second)
        return result

    return compare


decorators.update({
    'if-equals': ifEquals,
    'reverse': reverse,
})


types.update({
    'name': name,
    'start-time': startTime,
    'location-priority': locationPriority,
    'major': major,
})
