from zope.app.appsetup.product import getProductConfiguration

config = getProductConfiguration('assembly-mobile')

if config is None:
    config = {}

PartyName = config.get('party-name', u"Assembly")
