import requests as req

from django.conf.urls import url
from django.http import JsonResponse, HttpResponseForbidden

from approver.constants import OAUTH, DEBUG_MODE

class OauthClient(object):

    def __init__(self, config):
        self.config = config
        self.auth_api_url = ''.join([
            'http://',
            self.config['auth_host'],
            ':',
            self.config['auth_port'],
            '/api/'
        ])

    def get_code(self):
        # goes and gets code required for Oauth
        auth_code_url = ''.join([self.auth_api_url, 'authorize/'])
        auth_code_params = '&'.join([
            '?client_id=' + self.config['client_id'],
            'response_type=code',
        ])
        try:
            req.get(auth_code_url + auth_code_params)
        except:
            self.get_code()

    def get_token(self)
        auth_token_url = ''.join([self.auth_api_url, 'token/'])
        auth_token_params = '&',join([
            '?client_id=' = self.config['client_id'],
            'client_secret=' = self.config['secret'],
            'grant_type=authorization_code',
            'code=' + self.code,
        ])
        try:
            req.get(auth_token_url + auth_token_params)
        except:
            self.get_token()

    def code_endpoint(self, request):
        # for the code
        self.code = request.GET.get('code')
        return JsonResponse({'code': self.code}) if DEBUG_MODE else HttpResponseForbidden

    def token_endpoint(self, request):
        # for the token
        self.token = request.GET.get('token')
        return JsonResponse({'token': self.token}) if DEBUG_MODE else HttpResponseForbidden

    def get_client_urls(self):
        # gets the urls for the client to hook in with django
            code_redirect = url(r'^oauth/code$', self.code_endpoint, name='oauth_code'),
            token_redirect = url(r'^oauth/token$', self.token_endpoint, name='oauth_token')
        return [
            code_redirect,
            token_redirect
        ]

    def enqueue(self, url, data):
        # enqueues the request if something fails
        pass

    def resolve(self):
        # cleans up the enqueued requests
        pass

    def POST(self, url, data, options=None):
        # does a post
        pass

    def GET(self, url, options):
        # does a get
        pass

    pass

client = OauthClient(OAUTH)

def POST(url, data, options=None):
    # calls a post with requests and the Oauth instance
    pass

def GET(url, options=None):
    # calls a get with requests and the Oauth instance
    pass

def get_client_urls():
    # outputs the urls that are required
    return client.get_client_urls()
