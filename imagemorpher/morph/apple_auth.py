from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt  # You'll need to install PyJWT: `pip install pyjwt[crypto]`
import requests
import json
from dotenv import load_dotenv
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from jwt import PyJWKClient

# load root .env file
load_dotenv(dotenv_path='../../.env')

class AppleSignInAuthentication(BaseAuthentication):

    def exchange_auth_code_for_token(self, auth_code):
        client_secret = os.environ.get('APPLE_CLIENT_SECRET')
        client_id = os.environ.get('APPLE_CLIENT_ID')
        redirect_uri = os.environ.get('APPLE_REDIRECT_URI')
        url = 'https://appleid.apple.com/auth/token'
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            raise Exception("Failed to exchange auth code for token. HTTP Status: {}, Response: {}".format(response.status_code, response.text))

    def exchange_refresh_token_for_id_token(self, refresh_token):
        client_secret = os.environ.get('APPLE_CLIENT_SECRET')
        client_id = os.environ.get('APPLE_CLIENT_ID')
        url = 'https://appleid.apple.com/auth/token'
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            raise Exception("Failed to exchange refresh token for ID token. HTTP Status: {}, Response: {}".format(response.status_code, response.text))

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        id_token = auth_header.split('Bearer ')[1]

        # Verify the access token and get the user's information
        user_info = self.verify_apple_id_token(id_token)

        if not user_info:
            raise AuthenticationFailed("Invalid Apple access token")

        # Your logic to get or create the user in your Django app
        user = self.get_or_create_user(user_info)
        return user, None

    def verify_apple_id_token(self, id_token):
        # Your Apple Team ID and Apple Services ID (Client ID)
        client_id = os.environ.get('APPLE_CLIENT_ID')

        try:
            # Fetch Apple's public keys
            jwk_client = PyJWKClient('https://appleid.apple.com/auth/keys')
            signing_key = jwk_client.get_signing_key_from_jwt(id_token)

            # Decode and verify the id token
            decoded_token = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=['RS256'],
                audience=client_id,
                issuer='https://appleid.apple.com',
                options={'verify_exp': True},
            )

            return decoded_token
        except Exception as e:
            print(f"Error verifying Apple ID token: {e}")
            return None

    # Get the public key from Apple to verify the JWT signature
    def get_apple_public_key(self, kid):
        apple_public_keys = requests.get('https://appleid.apple.com/auth/keys').json()
        for key in apple_public_keys['keys']:
            if key['kid'] == kid:
                return key
        return None

    def get_or_create_user(self, user_info):
        User = get_user_model()
        user, created = User.objects.get_or_create(username=user_info['sub'], defaults={'email': user_info['email']})
        return user
