#!/usr/bin/python

import sys
from twisted.web import server, resource
from twisted.internet import defer, reactor
from twisted.spread import pb
from twisted.cred import credentials
from twisted.python import log, failure, util
from twisted.internet.task import deferLater

try:
    import json
except ImportError:
    import simplejson as json

class BuildbotForcebuild(resource.Resource):
    isLeaf = True

    pb_host = None
    pb_port = None
    pb_user = None
    pb_pass = None

    def render_POST(self, request):
        """
        Reponds only to POST events and starts the build process

        :arguments:
            request
                the http request object
        """
        content = request.content.getvalue()
        p = json.loads(content)
        log.msg("payload: " + str(p))

        d = self.forceBuild(p['builder'],p['reason'],p['branch'],
                            p['revision'],p['properties'])

        def started(bnum):
            log.msg('pb force started')
            request.write(str(bnum))
            request.finish()

        d.addCallback(started)

        return server.NOT_DONE_YET

    def forceBuild(self, builder, reason, branch, revision, properties):
        factory = pb.PBClientFactory()
        reactor.connectTCP(self.pb_host, self.pb_port, factory)
        creds = credentials.UsernamePassword(self.pb_user, self.pb_pass)
        d = factory.login(creds)
        d.addErrback(log.err, "error while connecting")

        dr = defer.Deferred()

        def connected(remote):
            log.msg('connected to pb')
            d2 = remote.callRemote('force', builder, reason, branch,
                                   revision, properties)

            d2.addCallback(lambda bnum: dr.callback(bnum))

        d.addCallback(connected)

        return dr

class BuildbotForcebuildWait(resource.Resource):
    isLeaf = True

    pb_host = None
    pb_port = None
    pb_user = None
    pb_pass = None

    def render_POST(self, request):
        """
        Reponds only to POST events and starts the build process

        :arguments:
            request
                the http request object
        """
        content = request.content.getvalue()
        p = json.loads(content)
        log.msg("payload: " + str(p))

        d = self.forceBuild(p['builder'],p['reason'],p['branch'],
                            p['revision'],p['properties'])

        def started(bnum):
            log.msg('pb force wait started')
            request.write(str(bnum))
            request.finish()

        d.addCallback(started)

        return server.NOT_DONE_YET

    def forceBuild(self, builder, reason, branch, revision, properties):
        factory = pb.PBClientFactory()
        reactor.connectTCP(self.pb_host, self.pb_port, factory)
        creds = credentials.UsernamePassword(self.pb_user, self.pb_pass)
        d = factory.login(creds)
        d.addErrback(log.err, "error while connecting")

        dr = defer.Deferred()

        def connected(remote):
            log.msg('connected to pb')
            d2 = remote.callRemote('forcewait', builder, reason, branch,
                                   revision, properties)

            d2.addCallback(lambda bnum: dr.callback(bnum))

        d.addCallback(connected)

        return dr