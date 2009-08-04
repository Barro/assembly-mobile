import datetime
import re
import urlparse

_TIME_FACTORY = datetime.datetime(2000, 1, 1)

NAME_MAX_LENGTH = 60
NAME_SHORTEN_TO = 55
NON_WORD_CHARACTERS = "-#:,. "
CUT_POSTFIX = "..."

def shortenName(name):
    shortName = re.sub("ARTtech seminars - ", "", name)
    # Name is too long. Cut it so that the three dots (...) come directly after
    # the last full word.
    if len(shortName) > NAME_MAX_LENGTH:
        # Cut to maximum length of a name.
        newShortName = shortName[:NAME_SHORTEN_TO]
        # Reverse name to cut to last full word.
        reversedName = newShortName[::-1]
        firstNonAlpha = 0
        # Find the beginning of last partial word.
        while reversedName[firstNonAlpha] not in NON_WORD_CHARACTERS:
            firstNonAlpha += 1
        # Find the end of last full word
        while reversedName[firstNonAlpha] in NON_WORD_CHARACTERS:
            firstNonAlpha += 1
        # Cut the not wanted characters from the end of the name.
        reversedName = reversedName[firstNonAlpha:]
        # Reverse the name
        newShortName = reversedName[::-1]
        # Add dots to cut name to indicate cutting.
        shortName = newShortName + CUT_POSTFIX
    return shortName


class MobileView(object):

    def mobileUpdate(self):
        self.now = datetime.datetime(2009, 8, 7, 18, 3)

        self.request.response.setHeader("Content-Type", "text/html; charset=UTF-8")
        nextMinute = _TIME_FACTORY.utcnow()
        maxAge = 60 - nextMinute.second%60
        nextMinute += datetime.timedelta(seconds=(maxAge))
        self.request.response.setHeader(
            "Expires", nextMinute.strftime("%a, %d %b %Y %H:%M:%S +0000"))
        self.request.response.setHeader("Cache-Control", "max-age=%d" % maxAge)


    def getTime(self):
        timeFormat = "%Y-%m-%d %H:%M %z"
        return _(u"Current time: %s" % self.now.strftime(timeFormat))


    def getCss(self):
        fp = open("src/asmmobile/static/asmmobile.css", "r")
        compressed = fp.read()
        fp.close()
        newlinesMatch = re.compile(r" *\n *")
        compressed = newlinesMatch.sub("", compressed)
        separatorMatch = re.compile(r" *([,:\{;]) *")
        compressed = separatorMatch.sub(r"\1", compressed)
        return compressed

    def applicationRelativeUrl(self, name):
        targetUrl = self.application_url(name)
        myUrl = self.url()
        maxCommon = 0
        minLength = min(len(targetUrl), len(myUrl))
        while (maxCommon < minLength
               and targetUrl[maxCommon] == myUrl[maxCommon]):
            maxCommon += 1
        if "/" not in myUrl[maxCommon:]:
            return targetUrl[maxCommon:]
        else:
            return urlparse.urlparse(targetUrl)[2]


