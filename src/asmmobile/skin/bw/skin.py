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
