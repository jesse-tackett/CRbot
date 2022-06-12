import requests, os

def checkUser(user):
    url = "https://api.twitch.tv/helix/streams?user_login={}".format(user)
    API_HEADERS = {
        'Client-ID': os.getenv('TWITCH_CLIENT'),
        'Authorization': os.getenv('TWITCH_BEARER')
    }

    try:
        s = requests.Session()
        req = s.get(url, headers=API_HEADERS)
        jsondata = req.json()
        print(jsondata)
        if [i['type'] for i in jsondata['data']] == ['live']: #stream is online
            return True
        else:
            return False
    except Exception as e:
        print("Error checking: ", e)
        return False