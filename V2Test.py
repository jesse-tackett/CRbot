import requests
import os
import json
import asyncio
from datetime import datetime
from pymongo import MongoClient
from twitchCheck import checkUser

# --------------------------------
# Static Variables
# --------------------------------
todayTime = str(datetime.now())[:19]
hour = 3600
minute = 60
user = 'nugiyen'
bearer_token = os.environ.get("BEARER_TOKEN")

# To set your enviornment variables in your terminal run the following line:


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r


def get_rules():
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))
    return response.json()


def delete_all_rules(rules):
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    print(json.dumps(response.json()))


def set_rules(delete):
    # You can adjust the rules if needed
    sample_rules = [
        {"value": "#Criticalrole", "tag": "Critical Role"}
    ]
    payload = {"add": sample_rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))


def get_stream(set):
    client = MongoClient('localhost', 27017)
    db = client['TwitterDump']
    collection = db['V2tweetAPI']
    try:
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/stream", auth=bearer_oauth, stream=True,
        )
        print(response.status_code)
        if response.status_code != 200:
            raise Exception(
                "Cannot get stream (HTTP {}): {}".format(
                    response.status_code, response.text
                )
            )

        for response_line in response.iter_lines():
            if response_line:
                json_response = json.loads(response_line)
                print(json.dumps(json_response, indent=4, sort_keys=True))
                collection.insert_one(json_response)
            '''if not checkUser(user):
                break'''
        client.close()
    except requests.exceptions.RequestException as e:
        print(e)
        print("Closing client")
        client.close()


def get_timestamp():
    return str(datetime.now())[:16]


async def wait_for_stream_start(retryTime=60):
    while True:
        if checkUser(user):
            print('****Stream Started****')
            break
        else:
            t = int(retryTime / 60)
            print('Not going Live again in {0} minute{1}: {2}'.format(t, "s" if t > 1 else "", get_timestamp()))
            await asyncio.sleep(retryTime)


async def main():
    rules = get_rules()
    delete = delete_all_rules(rules)
    set = set_rules(delete)
    #await wait_for_stream_start()
    get_stream(set)


if __name__ == "__main__":
    asyncio.run(main())