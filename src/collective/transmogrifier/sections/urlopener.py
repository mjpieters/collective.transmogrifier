import os
import io
import logging
import urlparse
import urllib2
import mimetools
import ConfigParser
import contextlib

from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import Expression
from collective.transmogrifier.utils import defaultMatcher
from collective.transmogrifier.utils import resolvePackageReferenceOrFile


class HTTPDefaultErrorHandler(urllib2.HTTPDefaultErrorHandler):

    def http_error_default(self, req, fp, code, msg, hdrs):
        try:
            return urllib2.HTTPDefaultErrorHandler.http_error_default(
                self, req, fp, code, msg, hdrs)
        except urllib2.URLError as error:
            if not self.section.ignore_error(self.item, error=error):
                raise
            self.section.logger.warn(
                'Ignoring error opening URL: %s', error)
            if not isinstance(msg, mimetools.Message):
                msg = mimetools.Message(io.StringIO())
                for key, value in vars(error).iteritems():
                    if key in ('code', 'msg', 'reason'):
                        msg[key] = str(value)
            return urllib2.addinfourl(fp, msg, req.get_full_url())


class URLOpenerSection(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous

        self.logger = logging.getLogger(options.get(
            'name', transmogrifier.configuration_id + '.' + name))

        self.key = defaultMatcher(options, 'url-key', name, 'url')
        self.cachekey = Expression(
            options.get('cache-key', 'string:_cache'),
            transmogrifier, name, options)
        self.headerskey = Expression(
            options.get('headers-key', 'string:_headers'),
            transmogrifier, name, options)

        self.cachedir = resolvePackageReferenceOrFile(
            options.get('cache-directory', 'var/urlopener.cache.d'))
        if not os.path.isdir(self.cachedir):
            os.makedirs(self.cachedir)

        handlers = Expression(
            options.get('handlers', 'python:[]'),
            transmogrifier, name, options)(options)
        if 'ignore-error' in options:
            self.ignore_error = Expression(
                options['ignore-error'], transmogrifier, name, options)
            self.ignore_handler = HTTPDefaultErrorHandler()
            self.ignore_handler.section = self
            handlers.append(self.ignore_handler)
        self.opener = urllib2.build_opener(*handlers)

    def __iter__(self):
        for item in self.previous:
            key = self.key(*item)[0]
            if key not in item:
                yield item
                continue

            url = item[key]
            if not isinstance(url, urlparse.SplitResult):
                url = urlparse.urlsplit(url)

            cache = os.path.join(
                self.cachedir, url.scheme, url.netloc,
                os.path.dirname(url.path.lstrip('/')),
                os.path.basename(url.path.lstrip('/')) or 'index.html')

            cachekey = self.cachekey(item, key=key)
            headerskey = self.headerskey(item, key=key)
            item[cachekey] = cache

            if os.path.isfile(cache):
                self.logger.info('Using cache: %s', cache)
                headers = ConfigParser.SafeConfigParser()
                headers.read(cache + '.metadata')
            else:
                if not os.path.isdir(os.path.dirname(cache)):
                    os.makedirs(os.path.dirname(cache))

                self.logger.info('Requesting URL: %s', url.geturl())
                if hasattr(self, 'ignore_handler'):
                    self.ignore_handler.item = item
                try:
                    response = self.opener.open(url.geturl())
                finally:
                    if hasattr(self, 'ignore_handler'):
                        del self.ignore_handler.item

                with contextlib.closing(response) as response:
                    open(cache, 'w').writelines(response)
                    headers = ConfigParser.SafeConfigParser(dict(
                        response.info(), url=response.geturl(), **dict(
                            (name, response.headers.getparam(name)) for name in
                            response.headers.getparamnames())))
                headers.write(open(cache + '.metadata', 'w'))

            item[headerskey] = dict(headers.defaults())

            yield item
