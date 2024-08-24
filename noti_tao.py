import bittensor as bt
import requests
import time
from io import StringIO
from prettytable import PrettyTable
import pandas as pd

burn_map = {}
my_netuids = [30]
cold_keys = [
    '5EM4easb1mQ7ff47KhnpGGCcKmRoYsE4cu9Bp8e1DrATP5mM',
]
tele_chat_id = '5024587446'
tele_report_token = '7416569989:AAFgPf0Yyvmrdi4HRfMAAq8CWXXxXpho89Q'
reward_map = {}

hotkeys = {
    '5DZzbwGtm1hjrr7LgndjUKCmo9ZDTaE6vgYuvoR1mmuwCVu5': 'hkey30(102)',
    '5H487UbWEjh7duwqJJp7mCNyihWQpQMwtqfGRMZA69bnNxzY': 'hkey30_2(69)',
    '5F1eiT1fSMhLJTETjMpt7S7GGbcDsFcPJevWTj1nE56BjqWJ': 'hkey6(147)',
    '5Dt4xxc6RZHABjUemhPoRKR6rqgMK5SAeitnPbiTeAnj7HfS': 'hhkey6_2(183)',
    '5FpTYpaqEARCiUKFiZfRNfsJ7ksDF7HRhEj7rqkTNwwL7VB6': 'hkey6_3(211)',
    '5D7yyvXTgmUugTh4P5p8XgsPhxejMg8TTgj2dwHmy8hh413m': 'hkey6_4(30)',
    '5GF8tB3arsbJwDPtGVySHYRhGmVY1uLP6EvzKVB3e8Gnv9J8': 'hkey6_5(222)'
}


def get_subnet_reward(netuid, cold_keys, rewards):
    x = PrettyTable()
    x.field_names = ["HOT", "INCENTIVE", "REWARDS", "RANK"]
    url = 'https://taostats.io/wp-admin/admin-ajax.php'
    data = {
        'action': 'metagraph_table',
        'this_netuid': netuid
    }

    response = requests.post(url, data=data)
    tables = pd.read_html(StringIO(response.text))
    df = tables[0].sort_values(by='INCENTIVE', ascending=True)
    incentives = df['INCENTIVE']

    has_change = False
    df = df[df['COLDKEY'].isin(cold_keys)]
    if df.empty:
        return '', has_change

    incentives = incentives[incentives > 0]

    for index, row in df.iterrows():
        key = f'{netuid}_{row["UID"]}'
        arrow = ''
        if key in reward_map:
            if (reward_map[key]['REWARDS'] != row['DAILY REWARDS'] or 
                reward_map[key]['INCENTIVE'] != row['INCENTIVE'] or
                reward_map[key]['RANK'] != incentives[incentives < row['INCENTIVE']].count() + 1):
                
                has_change = True
        else:
            has_change = True

        reward_map[key] = {
            'HOT': hotkeys.get(row['HOTKEY'], ''),
            'INCENTIVE': row['INCENTIVE'],
            'REWARDS': row['DAILY REWARDS'],
            'RANK': incentives[incentives < row['INCENTIVE']].count() + 1
        }

        x.add_row([
            reward_map[key]['HOT'], 
            reward_map[key]['INCENTIVE'], 
            '{0:.3f}'.format(reward_map[key]['REWARDS']) + arrow, 
            reward_map[key]['RANK']
        ])

        rewards.append(row['DAILY REWARDS'])

    return x.get_string(), has_change


def send_report():
    text = ''
    rewards = []
    need_send = False

    for netuid in my_netuids:
        string, has_change = get_subnet_reward(netuid, cold_keys, rewards)
        if has_change:
            need_send = True
        if string != '':
            text += f'\nNetuid: {netuid} <pre>{string}</pre>'

    if need_send:
        text += f'\nTotal: {sum(rewards)} {len(cold_keys)} coldkeys {len(rewards)} keys'
        data = {
            "chat_id": tele_chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        print(f"Sending report: {data}")
        requests.post(
            f'https://api.telegram.org/bot{tele_report_token}/sendMessage',
            json=data)


def run_script(subtensor):
    while True:
        send_report()
        time.sleep(60)


if __name__ == "__main__":
    run_script(None)



# pm2 start python3 --name tele_noti -- noti_tao.py
# pm2 restart tele_noti --update-env

