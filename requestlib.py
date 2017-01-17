from __future__ import absolute_import, division, print_function, unicode_literals

import decimal
import datetime
import json
import logging
from time import time
from urlparse import urljoin

import requests

logger = logging.getLogger(__name__)

class APIResponseFormatter(json.JSONEncoder):
    def default(self, o):
        # http://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15
        if isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]  # truncate millis from 6 to 3 digits
            if r.endswith('+00:00'):
                r = r[:-6] + 'Z'  # replace +00:00 with Z
            return r
        if isinstance(o, datetime.date):
            return o.isoformat()
        if isinstance(o, datetime.time):
            if o.utcoffset() is not None:
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r
        if isinstance(o, decimal.Decimal):
            return str(o)

        return super(APIResponseFormatter, self).default(o)


class ServiceAPI(object):
    API_URL = 'http://api_endpoint:<port>'

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': '???-Python/0.1.0',
        }
        self.params = {
            'token': self.api_key,
        }
        self.session = requests.session()
        self.test = Listings(self)
        
    def __repr__(self):
        return '<ServiceAPI {}>'.format(self.params['key'])

    def call(self, method, url, params=None, data=None):
        if params is None:
            params = {}
        else:
            encoder = APIResponseFormatter()
            params = {p: encoder.default(v) if isinstance(v, (datetime.datetime, datetime.date, datetime.time, decimal.Decimal)) else v for p, v in params.iteritems() if v is not None}
        self.params.update(params)

        if data is not None:
            data = json.dumps(data, cls=APIResponseFormatter)

        url = urljoin(self.API_URL, url)
        logger.debug('{} to {}: {} {}'.format(method, url, params, data))
        start = time()

        response = None
        try:
            response = self.session.request(method, url, params=self.params, data=data, headers=self.headers)
            duration = (time() - start) * 1000
        except Exception as e:
            duration = (time() - start) * 1000
            logger.exception('Received {} in {:.2f}ms: {}'.format(e.__class__.__name__, duration, e))
            # raise

        logger.debug('Received {} in {:.2f}ms: {}'.format(response.status_code, duration, response.text))

        return response


class Listings(object):
    def __init__(self, service):
        self.service = service

    def listings(self, method='GET', property_id='', params=None):
        return self.service.call(method, '<endpoint>/{}'.format(id), params=params)
