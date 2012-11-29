from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet
from twisted.web import server

from buildbot_forcebuild import BuildbotForcebuild, BuildbotForcebuildWait

class Options(usage.Options):
    optParameters = [['port',    'p', 4000, 'The port number to listen on.'],
                     ['pb-host', 'H', '127.0.0.1', 'The buildmaster PB host to connect to'],
                     ['pb-port', 'P', 9989, 'The buildmaster PB port to connect to'],
                     ['pb-user', 'user', 'change', 'The buildmaster PB username'],
                     ['pb-pass', 'pass', 'changepw', 'The buildmaster PB password'],
                     ['wait',    'w',  True, 'True = wait for buildnumber, False = get buildrequest number']
                     ]

class BuildbotForcebuildServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "buildbot-forcebuild"
    description = "This service runs the Buildbot Forcebuild service"
    options = Options

    def makeService(self, options):
        s = None
        
        if options['wait']:
            s = BuildbotForcebuild()
        else:
            s = BuildbotForcebuildWait()
        
        s.pb_host = options['pb-host']
        s.pb_port = int(options['pb-port'])
        s.pb_user = options['pb-user']
        s.pb_pass = options['pb-pass']

        site = server.Site(s)

        return internet.TCPServer(int(options["port"]), site)

serviceMaker = BuildbotForcebuildServiceMaker()
