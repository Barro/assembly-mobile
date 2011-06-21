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
import icalendar
import xml.etree.ElementTree as etree

#from zope.testbrowser.testing import Browser
class Browser(object):
    pass

from asmmobile.app import AsmMobile
import asmmobile.util as util

def assertXml(browser):
    etree.fromstring(browser.contents) and None

def initializeApplicationTestEnv(root, appname='app'):
    """Initializes standard test environment with application and browser.

    Application resides in root['app'] by default.

    @return tuple (root, app, browser)
    """

    app = AsmMobile()
    root[appname] = app
    browser = Browser()
    browser.handleErrors = False

    return (root, app, browser)

def getCalendarEvents(browser, url):
    browser.open(url)
    assert(browser.headers.get('Status').upper() == '200 OK')
    cal = icalendar.Calendar.from_string(browser.contents)
    eventIds = [event.decoded('uid') for event in cal.walk('vevent')]
    eventIds.sort()
    return eventIds

def assertEqual(expected, result):
    if expected != result:
        raise AssertionError(
            "Expected '%s' does not match '%s'" % (expected, result))

def assertIsIn(element, container, message=None):
    if element not in container:
        additionalMessage = ''
        if message is not None:
            additionalMessage = ": %s" % message
        raise AssertionError(
            "Element '%s' could not be found in '%s'%s" % (
                element, container, additionalMessage))

def checkStandardPages(
    app,
    browser,
    events=[],
    locations=[],
    lists=['/', '/all', '/location'],
    calendars=['/all-events.vcs', '/all-events.ics']
    ):

    def assertIsInBrowserContents(text, browser, message=None):
        assertIsIn(text, unicode(browser.contents, 'utf-8'), message)

    baseUrl = 'http://localhost/%s' % app.__name__

    # Save all events from visited locations for later investigation.
    locationEvents = set()
    for location in locations:
        # Check that page is OK and includes basic location information.
        locationBaseUrl = baseUrl + "/location/%s" % location.id
        browser.open(locationBaseUrl)
        assertXml(browser)
        assertIsInBrowserContents(cgi.escape(location.name), browser)

        # Check that location calendar data is OK and includes location name
        # in events.
        calendarUrl = locationBaseUrl + "/somename.vcs"
        for uid in getCalendarEvents(browser, calendarUrl):
            locationEvents.add(uid)
        assertIsInBrowserContents(
            util.icalEscape(location.name),
            browser,
            "Location was not found in calendar."
            )

    for event in events:
        # Check that event page is OK and includes basic event information.
        eventBaseUrl = baseUrl + "/event/%s" % event.id
        browser.open(eventBaseUrl)
        assertXml(browser)
        assertIsInBrowserContents(cgi.escape(event.name), browser)

        # Check that there links to location are found, if location exists.
        if event.location is not None:
            assertIsInBrowserContents(cgi.escape(event.location.id), browser)
            assertIsInBrowserContents(cgi.escape(event.location.name), browser)

        calendarUrl = eventBaseUrl + "/somename.vcs"
        uid = getCalendarEvents(browser, calendarUrl)[0]
        assertEqual(event.id + "@localhost", uid)
        assertIsIn(event.id + "@localhost", locationEvents)
        assertIsInBrowserContents(
            util.icalEscape(event.name),
            browser,
            "Event was not found in calendar."
            )

        if event.location is not None:
            assertIsInBrowserContents(util.icalEscape(event.location.name), browser)

    for listPage in lists:
        listUrl = baseUrl + listPage
        browser.open(listUrl)
        assertXml(browser)

    for calendarPage in calendars:
        calendarUrl = baseUrl + calendarPage
        browser.open(calendarUrl)
        getCalendarEvents(browser, calendarUrl)
