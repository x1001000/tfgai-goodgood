import time
import json
from hashlib import md5

import requests


class Error(Exception):
    """Base error"""


class NliStatusError(Exception):
    """The NLI result status is not 'ok'"""


class OlamiNliService(object):
    BASE_URL = 'https://tw.olami.ai/cloudservice/api'

    def __init__(self, app_key, app_secret, cusid=None, input_type=1, nli_config=None):
        self.app_key = app_key
        self.app_secret = app_secret
        self.cusid = cusid
        if input_type not in (0, 1):
            raise ValueError('Invalid input_type: {}'.format(input_type))
        self.input_type = input_type
        # TO BE Implemented
        if nli_config is not None:
            raise NotImplementedError('nli_config has not finished yet')
        self.nli_config = nli_config

    def __call__(self, text):
        resp = requests.post(self.BASE_URL,
                             params=self._gen_parameters(text))
        resp.raise_for_status()

        resp_json = resp.json()
        if resp_json['status'] != 'ok':
            raise NliStatusError(
                    "NLI responded status != 'ok': {}".format(resp_json['status']))
        else:
            return resp_json['data']['nli']

    def _gen_sign(self, api_parameter, timestamp=None):
        timestamp_ms = int(timestamp*1000) if timestamp else int(time.time()*1000)

        data = self.app_secret + 'api=' + api_parameter + 'appkey=' + self.app_key +\
            'timestamp=' + str(timestamp_ms) + self.app_secret

        return md5(data.encode('ascii')).hexdigest()

    def _gen_rq(self, text, as_text=False):
        obj = {'data_type': 'stt',
               'data': {
                   'input_type': self.input_type,
                   'text': text}}

        return obj if not as_text else json.dumps(obj)

    def _gen_parameters(self, text, timestamp=None):
        ts = timestamp if timestamp else time.time()
        ts_ms = int(ts*1000)
        params = {'appkey': self.app_key,
                  'api': 'nli',
                  'timestamp': ts_ms,
                  'sign': self._gen_sign('nli', timestamp=ts),
                  'rq': self._gen_rq(text, as_text=True)}
        if self.cusid is not None:
            params.update(cusid=self.cusid)

        return params


class Intent(object):

    def __init__(self, input, response, action, parameters):
        self.input = input
        self.response = response
        self.action = action
        self.parameters = parameters

    def __repr__(self):
        return ("<Intent object: input: '{}', "
                "response: '{}', action: '{}', parameters: '{}'").format(
                        self.input,
                        self.response,
                        self.action,
                        self.parameters)

    @classmethod
    def from_olami_result(cls, olami_result):
        # Take the first semantic object
        input = olami_result['semantic'][0]['input']
        response = olami_result['desc_obj'].get('result', '')
        action = olami_result['semantic'][0]['modifier'][0]
        parameters = {slot['name']: slot['value']
                      for slot in olami_result['semantic'][0]['slots']}
        return cls(input, response, action, parameters)
