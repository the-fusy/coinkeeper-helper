from typing import Tuple, List

import json
import requests

from uuid import uuid4
from dateutil import parser
from datetime import datetime, timedelta
from operator import itemgetter

from pprint import pprint


COOKIES = ''


def get_accounts_and_categories() -> Tuple[List, List]:
    res = requests.post(
        'https://coinkeeper.me/Exchange/Ping',
        headers={'cookie': COOKIES},
        json={'items': [{'key': 1, 'entityJson': None}]}
    )

    if res.status_code != 200:
        raise Exception('Check your cookies')

    data = res.json()
    entities = None
    for item in data['data']['items']:
        if item['key'] == 2:
            entities = json.loads(item['entityJson'])
            break

    if entities is None:
        raise Exception('Got unexpected data from coinkeeper')

    accounts, categories = [], []
    for item in entities:
        if item['deleted']:
            continue
        meta = {'id': item['id'], 'name': item['name']}
        category = item['categoryType']
        if category == 2:
            accounts.append(meta)
        elif category == 3:
            categories.append(meta)

    return accounts, categories


def calc_timestamp(date) -> int:
    return int(date.replace(year=date.year + 1969, hour=date.hour).timestamp()) * 10000000


def add_transaction(account, category, date, amount, tags, comment) -> bool:
    now = calc_timestamp(datetime.now())

    res = requests.post(
        'https://coinkeeper.me/api/transaction/create',
        headers={'cookie': COOKIES},
        json=[{
            "id": str(uuid4()),
            "tags": tags,
            "sourceId": account['id'],
            "sourceType": 2,
            "sourceAmount": amount,
            "sourceName": None,
            "sourceCurrencyId": None,
            "destinationId": category['id'],
            "destinationType": 3,
            "destinationAmount": amount,
            "destinationName": None,
            "destinationCurrencyId": None,
            "defaultAmount": amount,
            "comment": comment,
            "deleted": False,
            "dateTimestamp": calc_timestamp(date),
            "dateTimestampISO": date.strftime("%Y-%m-%dT00:00:00.000Z"),
            "createdTimestamp": now,
            "timestamp": now,
            "debtPaymentAmount": 0,
            "isComplete": True,
            "counter": 0,
            "repeatingParentId": None,
            "importedTransactionId": None,
        }],
    )

    return res.status_code == 200


def print_choices(title, items, item_name_getter=str):
    print(title + ':')
    for i, item in enumerate(items):
        print(f'{i} — {item_name_getter(item)}')
    print('')


def main():
    accounts, categories = get_accounts_and_categories()

    print_choices('Accounts', accounts, itemgetter('name'))
    print_choices('Categories', categories, itemgetter('name'))

    print("Enter transactions in format like: account category date ammount tag1,tag2 comment\\n")

    while True:
        data = input().split(' ', 5)

        account = accounts[int(data[0])]
        category = categories[int(data[1])]
        date = parser.parse(data[2]) + timedelta(hours=3)
        ammount = int(data[3])
        tags = data[4].split(',') if len(data) > 4 and data[4] != '-' else []
        comment = data[5] if len(data) > 5 else ''

        if add_transaction(account, category, date, ammount, tags, comment):
            print(f'Success: {account["name"]} -> {category["name"]}, {date}, {ammount}, {tags}, {comment}')
        else:
            print(f'Error: {account["name"]} -> {category["name"]}, {date}, {ammount}, {tags}, {comment}')


if __name__ == '__main__':
    main()
