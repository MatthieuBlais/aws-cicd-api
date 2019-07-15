import json
import urllib

APPLICATION=""
ENV=""
REGION_NAME=""

USERPOOL_ID = "" if "USERPOOL_ID" in os.environ.keys() else None
APP_CLIENT_ID = "" if "APP_CLIENT_ID" in os.environ.keys() else None
if USERPOOL_ID:
	KEYS_URL = 'https://cognito-idp.{}.amazonaws.com/{}/.well-known/jwks.json'.format(REGION_NAME, USERPOOL_ID)
	response = urllib.request.urlopen(KEYS_URL)
	COGNITO_KEYS = json.loads(response.read())['keys']


