# -*- coding: utf-8 -*-
__author__ = "Bernd Zeimetz"
__contact__ = "bzed@debian.org"
__license__ = """
Copyright (C) 2010-2013 Bernd Zeimetz <bzed@debian.org>

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

   1. Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
   2. Redistributions in binary form must reproduce the above
      copyright notice, this list of conditions and the following
      disclaimer in the documentation and/or other materials provided
      with the distribution.

THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from .urlencoder import encode_url, decode_url
from .cache import MemCache
from .config import UrlencoderConfig
from . import db

import re
import urlparse

_key_validator_re = re.compile(r'^([' + UrlencoderConfig.alphabet + ']+)$')
def _key_valid(key):
    if _key_validator_re.match(key) is None:
        return False
    return True

def _url_valid(url):
    spliturl = urlparse.urlsplit(url)
    if spliturl.scheme and spliturl.netloc:
        return True
    return False

class ManagementException(Exception):
    pass

class AddStaticUrlException(ManagementException):
    def __init__(self, alternate_key):
        self.alternate_key = alternate_key

    def __str__(self):
        return "The custom alias you've chosen is not available or too long. We've created a random one for you instead, but you can try assigning a different custom alias again.\n\n%s" %(self.alternate_key,)

    def get_alternate_key(self):
        return self.alternate_key

class UpdateStaticUrlException(ManagementException):
    def __str__(self):
        return "The custom alias you've chosen does not exist or the update failed for other reasons.\n"

class InvalidUrlException(ManagementException):
    def __init__(self, url):
        self.url = url

    def __str__(self):
        return "%s is not a valid url." %(self.url, )


def add_url(url, log=None):
    if not _url_valid(url):
        raise InvalidUrlException(url)
    id = db.add_url(url, log=log)
    key = encode_url(id)
    MemCache.set(key, url)
    return key

def add_static_url(url, key, log=None):
    if not _url_valid(url):
        raise InvalidUrlException(url)
    if not _key_valid(key):
        key = add_url(url, log=log)
        raise AddStaticUrlException(key)
    id = decode_url(key)
    try:
        db.add_url(url, id, log=log)
    except db.DbException:
        key = add_url(url, log=log)
        raise AddStaticUrlException(key)
    MemCache.set(key, url)
    return key

def update_static_url(url, key, log=None):
    if not _url_valid(url):
        raise InvalidUrlException(url)
    if not _key_valid(key):
        raise AddStaticUrlException(key)
    id = decode_url(key)
    try:
        db.update_url(url, id, log=log)
    except db.DbException:
        raise UpdateStaticUrlException(key)
    MemCache.set(key, url)
    return key

def get_url(key):
    if not _key_valid(key):
        return None
    url = MemCache.get(key)
    if url:
        if url == '__none__':
            return None
        return url
    id = decode_url(key)
    url = db.get_url(id)
    if url:
        MemCache.set(key, url)
        return url
    else:
        MemCache.set(key, '__none__')
    return None

def count(is_static=False):
    return db.count(is_static)

