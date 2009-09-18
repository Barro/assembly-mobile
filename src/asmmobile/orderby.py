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

def name(first, second):
    return cmp(first.__name__, second.__name__)


def startTime(first, second):
    result = cmp(first.start, second.start)
    if result == 0:
        return name(first, second)
    return result


def locationPriority(first, second):
    result = cmp(second.majorLocation.priority, first.majorLocation.priority)
    if result == 0:
        return name(first, second)
    return result
