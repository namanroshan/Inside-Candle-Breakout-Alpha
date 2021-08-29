import fyers_api
from fyers_api import accessToken
from fyers_api import fyersModel 

app_id = ""                 #Enter your own app id
app_secret = ""             #Enter your secret key
app_session = accessToken.SessionModel(app_id, app_secret)
response = app_session.auth()
authorization_code = response['data']['authorization_code']
app_session.set_token(authorization_code)
print(app_session.generate_token())