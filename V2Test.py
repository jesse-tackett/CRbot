import requests
import os
import json
import time
import asyncio
from datetime import datetime
from pymongo import MongoClient
from twitchCheck import checkUser

#--------------------------------
#Static Variables
#--------------------------------
todayTime = str(datetime.now())[:19]
hour = 3600
minute = 60
user = 'nugiyen'

# To set your enviornment variables in your terminal run the following line:


def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers


def get_rules(headers, bearer_token):
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", headers=headers
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))
    return response.json()


def delete_all_rules(headers, bearer_token, rules):
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        headers=headers,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    print(json.dumps(response.json()))


def set_rules(headers, delete, bearer_token):
    # You can adjust the rules if needed
    sample_rules = [
        {"value": "#Criticalrole", "tag": "Critical Role"}
    ]
    payload = {"add": sample_rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        headers=headers,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))


def get_stream(headers, set, bearer_token):
    client = MongoClient('localhost', 27017)
    db = client['TwitterDump']
    collection = db['V2tweetAPI']
    try:
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/stream", headers=headers, stream=True,
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
            if not checkUser(user):
                break
        client.close()
    except requests.exceptions.RequestException as e:
        print(e)
        print("Closing client")
        client.close()

def get_timestamp():
    return str(datetime.now())[:16]

async def wait_for_stream_start(retryTime = 60):
    while True:
        if checkUser(user):
            print('****Stream Started****')
            break
        else:
            t = int(retryTime / 60)
            print('Not going Live again in {0} minute{1}: {2}'.format(t, "s" if t > 1 else "", get_timestamp()))
            await asyncio.sleep(retryTime)

async def main():
    bearer_token = os.getenv("BEARER_TOKEN")
    headers = create_headers(bearer_token)
    rules = get_rules(headers, bearer_token)
    delete = delete_all_rules(headers, bearer_token, rules)
    set = set_rules(headers, delete, bearer_token)
    await wait_for_stream_start()
    get_stream(headers, set, bearer_token)


if __name__ == "__main__":
    asyncio.run(main())