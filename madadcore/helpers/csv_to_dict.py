import csv
import os
from secrets import token_hex


def csv_to_dict():

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mydir = os.path.join(BASE_DIR, 'helpers/daroo.csv')
    drugs_list = []

    with open(mydir, 'rt', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=',')
        num = 0
        for row in reader:
            if row:
                num += 1
                safe_id = token_hex(8)
                while any(d['safe_id'] == safe_id for d in drugs_list):
                    safe_id = token_hex(8)
                drug_dict = {'name': row[0], 'safe_id': safe_id, 'num': num}
                drugs_list.append(drug_dict)
    return drugs_list
