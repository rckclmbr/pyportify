import requests

from . import google


# The key is distirbuted with Google Play Services.
# This one is from version 7.3.29.
b64_key_7_3_29 = (b"AAAAgMom/1a/v0lblO2Ubrt60J2gcuXSljGFQXgcyZWveWLEwo6prwgi3"
                  b"iJIZdodyhKZQrNWp5nKJ3srRXcUW+F1BD3baEVGcmEgqaLZUNBjm057pK"
                  b"RI16kB0YppeGx5qIQ5QjKzsR8ETQbKLNWgRY0QRNVz34kMJR3P/LgHax/"
                  b"6rmf5AAAAAwEAAQ==")

android_key_7_3_29 = google.key_from_b64(b64_key_7_3_29)

auth_url = 'https://android.clients.google.com/auth'
useragent = 'gpsoauth-portify/1.0'


def _perform_auth_request(data):
    res = requests.post(auth_url, data,
                        headers={'User-Agent': useragent})

    return google.parse_auth_response(res.text)


def perform_master_login(email, password, android_id,
                         service='ac2dm', device_country='us', operatorCountry='us',
                         lang='en', sdk_version=17):
    """
    Perform a master login, which is what Android does when you first add a Google account.

    Return a dict, eg::

        {
            'Auth': '...',
            'Email': 'email@gmail.com',
            'GooglePlusUpgrade': '1',
            'LSID': '...',
            'PicasaUser': 'My Name',
            'RopRevision': '1',
            'RopText': ' ',
            'SID': '...',
            'Token': 'oauth2rt_1/...',
            'firstName': 'My',
            'lastName': 'Name',
            'services': 'hist,mail,googleme,...'
        }
    """

    data = {
        'accountType': 'HOSTED_OR_GOOGLE',
        'Email':   email,
        'has_permission':  1,
        'add_account': 1,
        'EncryptedPasswd': google.signature(email, password, android_key_7_3_29),
        'service': service,
        'source':  'android',
        'androidId':   android_id,
        'device_country':  device_country,
        'operatorCountry': device_country,
        'lang':    lang,
        'sdk_version': sdk_version
    }

    return _perform_auth_request(data)


def perform_oauth(email, master_token, android_id, service, app, client_sig,
                  device_country='us', operatorCountry='us', lang='en', sdk_version=17):
    """
    Use a master token from master_login to perform OAuth to a specific Google service.

    Return a dict, eg::

        {
            'Auth': '...',
            'LSID': '...',
            'SID': '..',
            'issueAdvice': 'auto',
            'services': 'hist,mail,googleme,...'
        }

    To authenticate requests to this service, include a header
    ``Authorization: GoogleLogin auth=res['Auth']``.
    """

    data = {
        'accountType': 'HOSTED_OR_GOOGLE',
        'Email':   email,
        'has_permission':  1,
        'EncryptedPasswd': master_token,
        'service': service,
        'source':  'android',
        'androidId':   android_id,
        'app': app,
        'client_sig': client_sig,
        'device_country':  device_country,
        'operatorCountry': device_country,
        'lang':    lang,
        'sdk_version': sdk_version
    }

    return _perform_auth_request(data)
