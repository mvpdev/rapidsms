from django.db.models.signals import post_save

from xml.sax.handler import ContentHandler
from xml.sax import parseString

from odk_dropbox.models import Submission

from rapidsms.webui import settings
import urllib2

class ODKHandler(ContentHandler):

    def __init__ (self):
        self._reports = []
        self._stack = []

    def get_reports(self):
        return self._reports

    def startElement(self, name, attrs):
        self._stack.append(name)
        if name=="Report":
            self._reports.append({"phone_number" : "+254733202155"})

    def characters(self, content):
        # ignore whitespace
        s = content.strip()
        current_field = self._stack[-1]
        if s and current_field in ["ID", "Muac", "Edema"]:
            self._reports[-1][current_field] = s

    def endElement(self, name):
        self._stack.pop()


def fake_messages(submission):
    handler = ODKHandler()
    byte_string = submission.xml.encode( "utf-8" )
    parseString(byte_string, handler)

    for report in handler.get_reports():
        number = report["phone_number"]
        message = "%(ID)s +m %(Muac)s %(Edema)s" % report

        # this is taken from httptester
        conf = settings.RAPIDSMS_APPS["httptester"]
        url = "http://%s:%s/%s/%s" % (
            conf["host"],
            conf["port"],
            urllib2.quote(number),
            urllib2.quote(message))

        print number, message
        print url
        f = urllib2.urlopen(url)
        print "I'm hanging on the above line."

def _fake_messages(sender, **kwargs):
    # if this is a new submission parse it an fake a bunch of sms messages
    if kwargs["created"]:
        fake_messages(kwargs["instance"])

post_save.connect(_fake_messages, sender=Submission)
