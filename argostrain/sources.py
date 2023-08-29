import os
import json
from argostrain.dataset import NetworkDataset
import urllib.parse

sources = {}

def get_source(from_code, to_code):
    global sources
    if len(sources) == 0:
        with open(os.path.join(os.path.dirname(__file__), "..", "sources.json")) as f:
            sources = json.loads(f.read())
    
    for i in range(len(sources)):
        if sources[i]['from_code'].lower() == from_code.lower() and sources[i]['to_code'].lower() == to_code.lower():
            return {
                'from_code': sources[i]['from_code'],
                'to_code': sources[i]['to_code'],
                'from_name': sources[i]['from_name'],
                'to_name': sources[i]['to_name'],
                'data': sources[i]['data'],
                'reverse': False,
            }
        elif sources[i]['to_code'].lower() == from_code.lower() and sources[i]['from_code'].lower() == to_code.lower():
            return {
                'to_code': sources[i]['from_code'],
                'from_code': sources[i]['to_code'],
                'to_name': sources[i]['from_name'],
                'from_name': sources[i]['to_name'],
                'data': sources[i]['data'],
                'reverse': True,
            }

    raise Exception(f"No sources found for {from_code}-{to_code}")

def get_network_dataset(source, link):
    filename = urllib.parse.urlparse(link).path.split("/")[-1]
    return NetworkDataset({
        'name': filename,
        'type': 'data',
        'from_code': source['from_code'],
        'to_code': source['to_code'],
        'size': -1,
        'links': [link],
        'reference': ''
    })