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

import cgi
import copy
import datetime
import dateutil.tz
import random

import asmmobile.util as util

parts = u"""a e i u o y
ca ce ci cu co cy
na ne ni nu no ny
za ze zi zu zo zy
gha ghe ghi ghu gho ghy
ta te ti tu to ty
ma me mi mu mo my
va ve vi vu vo vy
cä cö cå""".split()
parts.extend([" & ", " < "])

MAX_CONCURRENT_STARTS = 6
TIME_INCREASE_PROBABILITY = 0.4
CHANGED_START_TIME_PROBABILITY = 0.1
MAJOR_EVENT_PROBABILITY = 0.1
CANCELATION_PROBABILITY = 0.1

def generateWords(wordMin, wordMax, partMin, partMax):
    words = []
    for wid in xrange(0, random.randint(wordMin, wordMax)):
        word = ""
        for part in xrange(0, random.randint(partMin, partMax)):
            word += parts[random.randint(0, len(parts) - 1)]
        words.append(word)
    name = " ".join(words)
    return name[0].upper() + name[1:]

def generateIdLocations(amount):
    resultLocations = {}
    for locationId  in xrange(0, amount):
        name = generateWords(1, 3, 2, 4)
        idName = util.convertNameToKey(name.lower())
        resultLocations[idName] = {
            'name': name,
            'url': "http://www.example.com/location/%s" % idName,
            'description': cgi.escape(generateWords(20, 50, 2, 5)) + ".",
            }
    return resultLocations

def generateTranslatedLocations(existingNames):
    resultLocations = {}
    for idName in existingNames:
        name = generateWords(1, 3, 2, 4)
        resultLocations[idName] = {
            'name': name,
            'url': "http://www.example.com/location/%s" % idName,
            'description': cgi.escape(generateWords(20, 50, 2, 5)) + ".",
            }
    return resultLocations

def generateLanguageData(eventAmount, locations, startTime):
    locationNames = locations.keys()

    lengths = [datetime.timedelta(minutes=minutes) for minutes in
               [0, 15, 30, 30, 45, 60, 60, 60, 60, 60, 90, 90, 90, 120, 120]]

    increases = [datetime.timedelta(minutes=minutes) for minutes in
                 [15, 30, 30, 30, 30, 30, 30, 30, 60, 60, 60]]

    localOffset = util.tzOffsetString(
        datetime.datetime.now(dateutil.tz.tzlocal()).utcoffset())
    now = datetime.datetime.now(dateutil.tz.tzlocal())
    # Start from full hour.
    eventTime = now - datetime.timedelta(
        seconds=now.second, minutes=now.minute)

    resultEvents = {}
    currentEvents = 1
    for id in xrange(0, eventAmount):
        eventName = generateWords(1, 3, 2, 4)
        eventId = "test_%d" % id
        eventStart = eventTime.strftime("%Y-%m-%dT%H:%M:%S") + localOffset
        eventStartTimeOriginal = eventTime
        eventEndTime = eventTime + lengths[random.randint(0, len(lengths) - 1)]
        eventEnd = eventEndTime.strftime("%Y-%m-%dT%H:%M:%S") + localOffset

        # Event is probably going to be late from the original schedule.
        if random.random() < CHANGED_START_TIME_PROBABILITY:
            eventStartTimeOriginal = eventStartTimeOriginal - lengths[
                random.randint(0, len(lengths) - 1)]

        eventStartOriginal = eventStartTimeOriginal.strftime(
            "%Y-%m-%dT%H:%M:%S") + localOffset

        resultEvents[eventId] = {
            'name': eventName,
            'start': eventStart,
            'start-original': eventStartOriginal,
            'end': eventEnd,
            'location': locationNames[random.randint(0, len(locationNames) - 1)],
            'categories': [],
            'is-major': random.random() < MAJOR_EVENT_PROBABILITY,
            'description': cgi.escape(generateWords(20, 50, 2, 5)) + ".",
            'canceled': random.random() < CANCELATION_PROBABILITY,
            }

        if currentEvents >= MAX_CONCURRENT_STARTS:
            increaseTime = True
        else:
            increaseTime = random.random() < TIME_INCREASE_PROBABILITY

        if increaseTime:
            eventTime += increases[random.randint(0, len(increases) - 1)]
            currentEvents = 1
        else:
            currentEvents += 1
    return resultEvents

def translateEvents(baseEvents):
    translatedEvents = {}
    for key,data in baseEvents.items():
        translatedEvents[key] = copy.deepcopy(data)
        translatedEvents[key]['name'] = generateWords(1, 3, 2, 4)
        translatedEvents[key]['description'] = cgi.escape(generateWords(20, 50, 2, 5)) + "."
    return translatedEvents

def importer(
    eventCount,
    locationCount,
    languages=['en', 'fi'],
    startTime='now',
    ):
    resultLocations = {}
    resultEvents = {}

    baseLanguage = languages[0]
    restLanguages = []
    if len(languages) > 1:
        restLanguages = languages[1:]

    resultLocations[baseLanguage] = generateIdLocations(locationCount)
    resultEvents[baseLanguage] = generateLanguageData(eventCount, resultLocations[baseLanguage], startTime)

    for language in restLanguages:
        resultLocations[language] = generateTranslatedLocations(resultLocations[baseLanguage])
        resultEvents[language] = translateEvents(resultEvents[baseLanguage])

    return resultLocations, resultEvents
