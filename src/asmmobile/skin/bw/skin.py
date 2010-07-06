#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Assembly mobile - mobile content for visitors of Assembly computer festival.
# Copyright (C) 2010  Assembly Organizing
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

import asmmobile
import asmmobile.components
import asmmobile.interfaces
import asmmobile.skin.traverser

import grok
import zope.interface

_ = asmmobile.AsmMobileMessageFactory

class BwSkin(grok.IDefaultBrowserLayer):
    grok.skin("bw")

asmmobile.skin.traverser.addSkin('bw', _(u"B/W"), BwSkin)


class LayoutStyle(grok.Viewlet):
    grok.viewletmanager(asmmobile.components.StylesheetManager)
    grok.context(zope.interface.Interface)
    grok.layer(BwSkin)


# XXX: This should be not needed and used alternative skin names should be found
# automatically.
class AlternativeSkin(grok.Viewlet):
    grok.viewletmanager(asmmobile.skin.traverser.SkinManager)
    grok.context(zope.interface.Interface)
    grok.layer(BwSkin)

    name = "none"

    def render(self):
        import asmmobile.config as config
        return config.skinNameDefault
