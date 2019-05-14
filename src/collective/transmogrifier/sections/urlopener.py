# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import defaultMatcher
from collective.transmogrifier.utils import Expression
from collective.transmogrifier.utils import resolvePackageReferenceOrFile
from zope.interface import provider
from zope.interface import implementer

import contextlib
import io
import logging
import mimetools
import mimetypes
import os
import urllib2
import urlparse


class URLOpenerSection(object):
    provider(ISectionBlueprint)
    implementer(ISection)

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
        self.headersext = options.get(
            'headers-extension', mimetypes.guess_extension('message/rfc822'))

        self.cachedir = resolvePackageReferenceOrFile(
            options.get('cache-directory',
                        os.path.join(os.environ.get('PWD', os.getcwd()),
                                     'var/urlopener.cache.d')))
        if not os.path.isdir(self.cachedir):
            os.makedirs(self.cachedir)
        self.defaultpagename = options.get(
            'default-page-name', '.{0}.cache'.format(options['blueprint']))

        handlers = Expression(
            options.get('handlers', 'python:[]'),
            transmogrifier, name, options)(options)
        if 'ignore-error' in options:
            self.ignore_error = Expression(
                options['ignore-error'], transmogrifier, name, options)
            self.ignore_handler = HTTPDefaultErrorHandler()
            self.ignore_handler.section = self
            handlers.append(self.ignore_handler)
        if not [handler for handler in handlers
                if isinstance(handler, urllib2.HTTPRedirectHandler)]:
            handlers.append(HTTPRedirectHandler())
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
                os.path.basename(url.path.lstrip('/')) or self.defaultpagename)
            if os.path.isdir(cache):
                cache = os.path.join(cache, self.defaultpagename)
            headers_cache = cache + self.headersext

            cachekey = self.cachekey(item, key=key)
            headerskey = self.headerskey(item, key=key)
            item[cachekey] = cache

            if os.path.isfile(cache) and os.path.isfile(headers_cache):
                self.logger.debug('Using cache: %s', cache)
                headers = mimetools.Message(open(headers_cache))
            else:
                if not os.path.isdir(os.path.dirname(cache)):
                    os.makedirs(os.path.dirname(cache))

                self.logger.debug('Requesting URL: %s', url.geturl())
                if hasattr(self, 'ignore_handler'):
                    self.ignore_handler.item = item
                try:
                    response = self.opener.open(url.geturl())
                finally:
                    if hasattr(self, 'ignore_handler'):
                        del self.ignore_handler.item

                with contextlib.closing(response) as response:
                    open(cache, 'w').writelines(response)
                    headers = response.info()
                    headers.setdefault('Url', response.geturl())
                    code = response.getcode()
                    if code:
                        headers.setdefault(
                            'Status', str(code) + (
                                hasattr(response, 'msg') and
                                (' ' + response.msg) or ''))
                    open(headers_cache, 'w').write(str(headers))

            item[headerskey] = headers

            yield item


class HTTPDefaultErrorHandler(urllib2.HTTPDefaultErrorHandler):

    def http_error_default(self, req, fp, code, msg, hdrs):
        if not isinstance(hdrs, mimetools.Message):
            hdrs = mimetools.Message(io.StringIO(hdrs.decode()))
        hdrs.setdefault('Status', str(code) + ' ' + msg)
        try:
            return urllib2.HTTPDefaultErrorHandler.http_error_default(
                self, req, fp, code, msg, hdrs)
        except urllib2.URLError as error:
            if not self.section.ignore_error(self.item, error=error):
                raise
            self.section.logger.warn(
                'Ignoring error opening URL: %s', error)
            return error


class HTTPRedirectHandler(urllib2.HTTPRedirectHandler):

    def http_error_302(self, req, fp, code, msg, headers):
        resp = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        resp.headers.setdefault(
            'Redirect-Status',
            headers.get('Redirect-Status', fp.headers.get(
                'Redirect-Status', str(code) + ' ' + msg)))
        return resp

    http_error_301 = http_error_303 = http_error_307 = http_error_302
