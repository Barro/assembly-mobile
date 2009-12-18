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

from zope.app.appsetup.product import getProductConfiguration

config = getProductConfiguration('assembly-mobile')

if config is None:
    config = {}

def integerValue(name, default):
    value = config.get(name, None)
    if value == None:
        return default
    return int(value.strip())

def stringValue(name, default):
    return unicode(config.get(name, default).strip(), "utf-8")

def booleanValue(name, default):
    value = config.get(name, None)
    if value == None:
        return default
    if value.strip().lower() in ["true", "yes"]:
        return True
    return False


########################################################################
# General party-specific application configuration

siteName = stringValue("site-name", "Assembly Mobile")
partyName = stringValue("party-name", "Assembly")
mainSiteUrl = stringValue("main-site-url", "http://www.assembly.org/")

# As this is an AGPL application, source code must be publicly available even
# when application is not distributed.
sourceUrl = stringValue("source-url", "http://bitbucket.org/barro/assembly-mobile/")

########################################################################
# Options that affect the display of events

# Controls how many hours in past the ended events remain in the next events
# view.
nextEventsEndHours = integerValue('next-events-show-end-hours', 2)
# Controls how many hours to future we look for starting events in the next
# events view.
nextEventsStartHours = integerValue('next-events-show-start-hours', 10)

# Sort types:
#
# start-time
# location-priority
sortCurrentEvents = stringValue("sort-current-events", "start-time")
sortNextEvents = stringValue("sort-next-events", "start-time")

# Selector types for future events:
#
# one-per-location = One event per location. If there are more events than one
#     starting at the same location, this will choose only the ones that start
#     first.
# not-hidden = This shows only the events that are starting in less than the
#     location specific hiding time.
# maximum-amount = Limits the display of next events to some maximum number
#     that is specified as: maximum-amount:4
#
# Multiple selectors can be combined with "&".
#
# By default choose events that are not hidden and show only the first ones
# of those.
selectNextEvents = stringValue("select-next-events", "not-hidden&one-per-location")

# Default priority for locations.
defaultLocationPriority = integerValue("default-location-priority", 0)

# Default time objects are hidden before they are shown in "next events".
defaultHideTime = integerValue("default-hide-time", 7200)

# Enable internalization.
enableInternalization = booleanValue("enable-internalization", True)

# A comma separated list of enabled languages or a start to enable them all.
enabledLanguages = stringValue("enabled-languages", "*")

# Default language that is used when user with unknown language comes to site
# or if events or locations are not available with such language.
defaultLanguage = stringValue("default-language", "en")

########################################################################
# Importing options

# Names that are shorten that short-name-maximum-length are not shortened.
shortNameMaximumLength = integerValue("short-name-maximum-length", 60)

# Names are shortened to this length before starting to search for word
# boundary. Names are cut at word boundaries instead of coldly cutting them
# to short length.
shortNameShortenTo = integerValue("short-name-shorten-to", 57)

# Characters that we use to find word boundaries.
shortNameNonWordCharacters = stringValue("short-name-non-word-characters", "-_ #:,.?!/")

# Cut postfix is added to the end of shortened names.
#
# For example "This is a long event name" could be shortened to
# "This is a long..."
shortNameCutPostfix = stringValue("short-name-cut-postfix", "...")


########################################################################
# Options that affect internal workings of this application

# Controls that do we send headers indicating modified and cache times to
# clients. All caching related headers take a few hundred bytes so this
# might be good to take into account when trying to reduce sent data.
#
# Header removal can also be done in reverse proxy, so we can still benefit
# from server side caching and clients get less data per connection.
sendCachingHeaders = booleanValue("send-caching-headers", False)

# Time how long one event is considered to be valid.
# This affects caching of all other pages than the overview schedule and next
# events schedule, as those pages have data that is changed at least once
# every minute.
eventCacheMinutes = integerValue("event-cache-minutes", 15)

# For now this controls that do we shorten CSS class and ID names or not.
#
# Shortened CSS names are specified with "shorten" type in templates:
# <span tal:attributes="class shorten:classname">
#
# This can be either "true" or "false".
mobileMode = booleanValue('mobile-mode', True)

# This sets the source of application time as local time.
#
# Either "now" or time given in following format: year-month-day-hour-minute
#
# For example "2009-08-06-18-23" would set the application time to 2009-08-06
# 18:23:00 local time.
time = stringValue("time", "now")

# Container name for Location objects.
locations = stringValue("locations", "location")

# Container name for Event objects.
events = stringValue("events", "event")

# Name for language including cookie.
cookieLanguage = stringValue("cookie-language", "l")
