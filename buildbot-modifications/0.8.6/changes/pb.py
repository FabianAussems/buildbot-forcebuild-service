# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members


from twisted.python import log
from twisted.internet import defer

from buildbot.pbutil import NewCredPerspective
from buildbot.changes import base
from buildbot.util import epoch2datetime
from buildbot import config

from buildbot import interfaces
from buildbot.sourcestamp import SourceStamp
from buildbot.process.properties import Properties

class ChangePerspective(NewCredPerspective):

    def __init__(self, master, prefix):
        self.master = master
        self.prefix = prefix

    def attached(self, mind):
        return self
    def detached(self, mind):
        pass

    def perspective_force(self, builder='build', reason='',
                          branch='', revision='',
                          pdict={}):
        log.msg('force called')

        branch_validate = self.master.config.validation['branch']
        revision_validate = self.master.config.validation['revision']
        pname_validate = self.master.config.validation['property_name']
        pval_validate = self.master.config.validation['property_value']
        if not branch_validate.match(branch):
            log.msg("bad branch '%s'" % branch)
            return
        if not revision_validate.match(revision):
            log.msg("bad revision '%s'" % revision)
            return

        properties = Properties()
        if pdict:
            for prop in pdict:
                pname = prop
                pvalue = pdict[prop]
                if not pname_validate.match(pname) or \
                        not pval_validate.match(pvalue):
                    log.msg("bad property name='%s', value='%s'"
                            % (pname, pvalue))
                    return
                log.msg('set property %s %s' % (pname, pvalue))
                properties.setProperty(pname, pvalue, "Force Build PB")

        c = interfaces.IControl(self.master)
        b = c.getBuilder(builder)

        ss = SourceStamp(branch=branch, revision=revision)

        dr = defer.Deferred()

        def requested(breq):
            log.msg('force requested')
            dr.callback(breq.getId())

        d2 = b.submitBuildRequest(ss, reason, props=properties.asDict())
        d2.addCallback(requested)
        d2.addErrback(log.err, "while forcing a build")

        return dr

    def perspective_forcewait(self, builder='build', reason='',
                              branch='', revision='',
                              pdict={}):
        log.msg('forcewait called')

        branch_validate = self.master.config.validation['branch']
        revision_validate = self.master.config.validation['revision']
        pname_validate = self.master.config.validation['property_name']
        pval_validate = self.master.config.validation['property_value']
        if not branch_validate.match(branch):
            log.msg("bad branch '%s'" % branch)
            return
        if not revision_validate.match(revision):
            log.msg("bad revision '%s'" % revision)
            return

        properties = Properties()
        if pdict:
            for prop in pdict:
                pname = prop
                pvalue = pdict[prop]
                if not pname_validate.match(pname) or \
                        not pval_validate.match(pvalue):
                    log.msg("bad property name='%s', value='%s'"
                            % (pname, pvalue))
                    return
                log.msg('set property %s %s' % (pname, pvalue))
                properties.setProperty(pname, pvalue, "Force Build PB")

        c = interfaces.IControl(self.master)
        b = c.getBuilder(builder)

        ss = SourceStamp(branch=branch, revision=revision)

        dr = defer.Deferred()

        def started(s):
            log.msg('force started')
            dr.callback(s.getNumber())

        def requested(breq):
            log.msg('force requested')
            breq.subscribe(started)

        d2 = b.submitBuildRequest(ss, reason, props=properties.asDict())
        d2.addCallback(requested)
        d2.addErrback(log.err, "while forcing a build")

        return dr

    def perspective_addChange(self, changedict):
        log.msg("perspective_addChange called")

        if 'revlink' in changedict and not changedict['revlink']:
            changedict['revlink'] = ''
        if 'repository' in changedict and not changedict['repository']:
            changedict['repository'] = ''
        if 'project' in changedict and not changedict['project']:
            changedict['project'] = ''
        if 'files' not in changedict or not changedict['files']:
            changedict['files'] = []

        # rename arguments to new names.  Note that the client still uses the
        # "old" names (who, when, and isdir), as they are not deprecated yet,
        # although the master will accept the new names (author,
        # when_timestamp, and is_dir).  After a few revisions have passed, we
        # can switch the client to use the new names.
        if 'isdir' in changedict:
            changedict['is_dir'] = changedict['isdir']
            del changedict['isdir']
        if 'who' in changedict:
            changedict['author'] = changedict['who']
            del changedict['who']
        if 'when' in changedict:
            when = None
            if changedict['when'] is not None:
                when = epoch2datetime(changedict['when'])
            changedict['when_timestamp'] = when
            del changedict['when']

        # turn any bytestring keys into unicode, assuming utf8 but just
        # replacing unknown characters.  Ideally client would send us unicode
        # in the first place, but older clients do not, so this fallback is
        # useful.
        for key in changedict:
            if type(changedict[key]) == str:
                changedict[key] = changedict[key].decode('utf8', 'replace')
        changedict['files'] = list(changedict['files'])
        for i, file in enumerate(changedict.get('files', [])):
            if type(file) == str:
                changedict['files'][i] = file.decode('utf8', 'replace')

        files = []
        for path in changedict['files']:
            if self.prefix:
                if not path.startswith(self.prefix):
                    # this file does not start with the prefix, so ignore it
                    continue
                path = path[len(self.prefix):]
            files.append(path)
        changedict['files'] = files

        if not files:
            log.msg("No files listed in change... bit strange, but not fatal.")
        d = self.master.addChange(**changedict)
        # since this is a remote method, we can't return a Change instance, so
        # this just sets the return value to None:
        d.addCallback(lambda _ : None)
        return d

class PBChangeSource(config.ReconfigurableServiceMixin, base.ChangeSource):
    compare_attrs = ["user", "passwd", "port", "prefix", "port"]

    def __init__(self, user="change", passwd="changepw", port=None,
            prefix=None):

        self.user = user
        self.passwd = passwd
        self.port = port
        self.prefix = prefix
        self.registration = None
        self.registered_port = None

    def describe(self):
        portname = self.registered_port
        d = "PBChangeSource listener on " + str(portname)
        if self.prefix is not None:
            d += " (prefix '%s')" % self.prefix
        return d

    @defer.deferredGenerator
    def reconfigService(self, new_config):
        # calculate the new port
        port = self.port
        if port is None:
            port = new_config.slavePortnum

        # and, if it's changed, re-register
        if port != self.registered_port:
            wfd = defer.waitForDeferred(
                self._unregister())
            yield wfd
            wfd.getResult()
            self._register(port)

        wfd = defer.waitForDeferred(
            config.ReconfigurableServiceMixin.reconfigService(self,
                                                    new_config))
        yield wfd
        wfd.getResult()

    def stopService(self):
        d = defer.maybeDeferred(base.ChangeSource.stopService, self)
        d.addCallback(lambda _ : self._unregister())
        return d

    def _register(self, port):
        if not port:
            log.msg("PBChangeSource has no port to listen on")
            return
        self.registered_port = port
        self.registration = self.master.pbmanager.register(
                port, self.user, self.passwd,
                self.getPerspective)

    def _unregister(self):
        self.registered_port = None
        if self.registration:
            return self.registration.unregister()
        else:
            return defer.succeed(None)

    def getPerspective(self, mind, username):
        assert username == self.user
        return ChangePerspective(self.master, self.prefix)
