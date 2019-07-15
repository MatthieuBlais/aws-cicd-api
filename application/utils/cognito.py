import boto3
import logging
import json
import traceback
from chalicelib.config import REGION_NAME, COGNITO_KEYS, APP_CLIENT_ID
import os
import urllib
import json
import time
from jose import jwk, jwt
from jose.utils import base64url_decode

class Cognito(object):
	"""docstring for Cognito"""


	@classmethod
	def get_email(cls, app):
		token = app.current_request.headers["Authorization"].replace("Bearer ", "")
		headers = jwt.get_unverified_headers(token)
		kid = headers['kid']
		key_index = -1
		for i in range(len(COGNITO_KEYS)):
			if kid == COGNITO_KEYS[i]['kid']:
				key_index = i
				break
		if key_index == -1:
			logging.error('Public key not found in jwks.json')
			return False

		# construct the public key
		public_key = jwk.construct(COGNITO_KEYS[key_index])
		# get the last two sections of the token,
		# message and signature (encoded in base64)
		message, encoded_signature = str(token).rsplit('.', 1)
		# decode the signature
		decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
		# verify the signature
		if not public_key.verify(message.encode("utf8"), decoded_signature):
			logging.error('Signature verification failed')
			return False
		logging.info('Signature successfully verified')
		# since we passed the verification, we can now safely
		# use the unverified claims
		claims = jwt.get_unverified_claims(token)
		# additionally we can verify the token expiration
		if time.time() > claims['exp']:
			logging.info('Token is expired')
			return False
		# and the Audience  (use claims['client_id'] if verifying an access token)
		if claims['aud'] != APP_CLIENT_ID:
			logging.info('Token was not issued for this audience')
			return False
		# now we can use the claims
		return claims["email"]


