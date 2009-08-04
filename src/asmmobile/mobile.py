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


def strip_filter_factory(global_conf, **local_conf):
    def filter(app):
        return StripFilter(app)
    return filter

class StripFilter(object):
    """This filter strips white space characters from resulting XHTML output
    document.
    """

    def __init__(self, app, www_path=None):
        self.app = app
        self.www_path = www_path
        self.status      = '200 OK'
        self.exc_info    = None
        self.headers_out = []


    def start_response(self, status, headers_out, exc_info=None):
        """Intercept the response start from the filtered app."""
        self.status      = status
        self.headers_out = headers_out
        self.exc_info    = exc_info

    def __call__(self, env, start_response):
        self.env = env
        self.real_start = start_response
        return self.__iter__()

    def getHeader(self, headerName):
        for key,value in self.headers_out:
            if key.lower() == headerName:
                return value
        return None


    def __iter__(self):
        result = self.app(self.env, self.start_response)
        resultIter  = result.__iter__()

        filterContent = True
        contentType = self.getHeader('content-type')
        # If result is not text/html, return immediately
        if (contentType is None \
                or not contentType.lower().startswith("text/html")):
            self.real_start(self.status, self.headers_out, self.exc_info)
            return resultIter

        resultStr = "".join(resultIter)

        # Filter out white space and comments.
        resultStr = re.sub("<!--.*?-->", "", resultStr)
        resultStr = re.sub("( *\n *)+", " ", resultStr)
        resultStr = re.sub(" +/>", "/>", resultStr)

        headers_out = []
        for key,value in self.headers_out:
            if key.lower() == 'content-length':
                value = len(resultStr)
            headers_out.append((key,value))

        self.real_start(self.status, headers_out, self.exc_info)

        return [resultStr].__iter__()
