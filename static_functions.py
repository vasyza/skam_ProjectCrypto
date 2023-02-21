import datetime
import json
import random


def generate_referral_code():
    json_decoder = json.JSONDecoder()
    with open('./db/fsm_storage.json', 'r') as json_file:
        all_codes = json_decoder.decode(json_file.read())
    already_referral = [all_codes[key][key]['data'] for key in all_codes if key.isdigit() and
                        int(key) > 0 and "referral_code" in all_codes[key][key]['data'].keys()]
    while (referral_code := random.getrandbits(32)) in already_referral:
        pass

    return "%x" % referral_code


def get_timestamp_now():
    now_datetime = int(datetime.datetime.now().timestamp())
    return now_datetime


def parse_timestamp(timestamp_register):
    timestamp_now = datetime.date.fromtimestamp(get_timestamp_now())
    timestamp_register = datetime.date.fromtimestamp(timestamp_register)
    return (timestamp_now - timestamp_register).days


def calculate_worker_profit(profit):
    if profit < 100:
        profit *= 0.5
    elif profit < 500:
        profit *= 0.6
    else:
        profit *= 0.7
    return int(profit)
