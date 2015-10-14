# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
import pickle
from support.abstract.proxylist import ProxyListException
from support.common import LocalizedError, lowercase, lang
from support.plugin import plugin
from support.xrequests import NoValidProxiesFound, Session
from util.timer import Timer
from requests import RequestException, Timeout
import logging


class ScraperError(LocalizedError):
    pass


class AbstractScraper(object):
    def __init__(self, xrequests_session, cookie_jar=None):
        """
        :type cookie_jar: str
        :type xrequests_session: Session
        """
        self.log = logging.getLogger(__name__)
        self.cookie_jar = cookie_jar
        self.session = xrequests_session
        if self.cookie_jar and os.path.exists(cookie_jar):
            self.session.cookies = load_cookies(cookie_jar)

    def save_cookies(self):
        if self.cookie_jar:
            save_cookies(self.session.cookies, self.cookie_jar)

    def fetch(self, url, params=None, data=None, **request_params):
        try:
            with Timer(logger=self.log, name='Fetching URL %s with params %r' % (url, params)):
                response = self.session.request('post' if data else 'get',
                                                url, params=params, data=data,
                                                **request_params)
                response.raise_for_status()
                self.save_cookies()
                return response
        except Timeout as e:
            raise ScraperError(32000, "Timeout while fetching URL: %s" % url, lang(30000), cause=e)
        except NoValidProxiesFound as e:
            raise ScraperError(32005, "Can't find anonymous proxy", cause=e)
        except RequestException as e:
            raise ScraperError(32001, "Can't fetch URL: %s" % url, lang(30000), cause=e)
        except ProxyListException as e:
            plugin.set_setting('use-proxy', 0)
            raise ScraperError(32004, "Can't load anonymous proxy list", cause=e)


def load_cookies(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)


def save_cookies(cookie_jar, filename):
    with open(filename, 'wb') as f:
        pickle.dump(cookie_jar, f)


def parse_duration(duration):
    duration = duration.strip(" \t\xa0")
    parts = duration.split(":")
    if len(parts) == 1:
        return int(duration)
    elif len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    elif len(parts) == 4:
        return int(parts[0]) * 86400 + int(parts[1]) * 3600 + int(parts[2]) * 60 + int(parts[3])


def parse_size(size):
    size = size.strip(" \t\xa0")
    if size.isdigit():
        return long(size)
    else:
        num, qua = size[:-2].rstrip(), lowercase(size[-2:])
        if qua == 'mb' or qua == 'мб':
            return long(float(num) * 1024 * 1024)
        elif qua == 'gb' or qua == 'гб':
            return long(float(num) * 1024 * 1024 * 1024)
        elif qua == 'tb' or qua == 'тб':
            return long(float(num) * 1024 * 1024 * 1024 * 1024)
