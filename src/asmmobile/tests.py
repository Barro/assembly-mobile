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

import unittest
import doctest
import asmmobile

from zope.fanstatic.testing import ZopeFanstaticBrowserLayer

browser_layer = ZopeFanstaticBrowserLayer(asmmobile)

def test_suite():
    suite = unittest.TestSuite()

    app_test = doctest.DocFileSuite('test-full-app.txt', # Add more doctest files here.
        optionflags = (
            doctest.ELLIPSIS +
            doctest.NORMALIZE_WHITESPACE +
            doctest.REPORT_NDIFF),
        globs={'getRootFolder': browser_layer.getRootFolder})
    app_test.layer = browser_layer

    suite.addTest(app_test)
    return suite
