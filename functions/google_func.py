# Standard list of parameters for items: title (subtitle is subsumed in title with :), link, author, publisher, description

import requests, json, feedparser, subprocess
from functions.utils_func import *

def gbooks(query, topN):
    resp = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={query.replace(' ', '+')}&filter=partial&maxResults={topN}") # https://developers.google.com/books/docs/v1/using#filtering
    if resp.status_code == 200:
        final_list = []
        resp = resp.json()
        if resp['totalItems'] > 0:
            for item in resp['items']:
                count = 0
                if 'volumeInfo' in item:
                    if count >= topN: break
                    item_dict = dict()
                    item_dict['title'] = item['volumeInfo']['title'] if 'title' in item['volumeInfo'] else ''
                    if 'subtitle' in item['volumeInfo']: item_dict['title'] += ': ' + item['volumeInfo']['subtitle']
                    item_dict['link'] = item['volumeInfo']['previewLink'] if 'previewLink' in item['volumeInfo'] else ''
                    item_dict['author'] = ', '.join(item['volumeInfo']['authors']) if 'authors' in item['volumeInfo'] else ''
                    item_dict['publisher'] = item['volumeInfo']['publisher'] if 'publisher' in item['volumeInfo'] else ''
                    item_dict['description'] = item['volumeInfo']['description'] if 'description' in item['volumeInfo'] else ''
                    final_list.append(item_dict)
                    count += 1
            print('Got more Google Books results')
            return final_list
        else: return []
    else: return []

def gnews(query, hrs, topN): # https://stackoverflow.com/a/51537262
    final_list = []
    gnews_feed = f"https://news.google.com/rss/search?q={query.replace(' ','+')}+when:{hrs}h&hl=en-IN&gl=IN&ceid=IN:en"
    items = feedparser.parse(gnews_feed)
    for i, item in enumerate(items['entries']):
        if i >= topN: break
        item_dict = dict()
        item_dict['title'] = item['title'] if 'title' in item else ''
        item_dict['link'] = item['link'] if 'link' in item else ''
        item_dict['publisher'] = item['source']['title'] if 'source' in item and 'title' in item['source'] else ''
        item_dict['description'] = cleanhtml(item['summary']) if 'summary' in item else ''
        final_list.append(item_dict)
    print('Got more Google News results')
    return final_list

def gsearch(query, topN):
    node_res = subprocess.Popen(f'node flet/googlethis/gthis.js "{query}"', shell=True, stdout=subprocess.PIPE).stdout.read() # Add double quotes so that node package googlethis sees the whole query as one argument
    #print(node_res)
    node_dict = eval(node_res.decode().replace(':false', ':False').replace(':true', ':True').replace(':null', ':None')) # Replace node specific syntax with python syntax
    #for r in node_dict['results']: print(r['title'], r['url'])
    #print(node_dict['people_also_search']) # List
    #print(node_dict['people_also_ask']) # List
    also_ask = [x for x in node_dict['people_also_ask'] if x.endswith('?')] # Only questions from also ask list. The package clubs both aslo ask and also search in one list
    also_search = [x for x in node_dict['people_also_ask'] if x not in also_ask] # Only search terms for also search list
    print('Got more Google results')
    return node_dict['results'], also_search, also_ask

def parse_serp(results, original_site):
    final_list = []
    original_site = original_site.replace('https://', '').replace('http://', '').replace('www.', '').replace('/amp/', '')
    for item in results: 
        url_check = item['url'].replace('https://', '').replace('http://', '').replace('www.', '').replace('/amp/', '')
        if not url_check.startswith(original_site):
            item_dict = dict()
            item_dict['title'] = item['title'] if 'title' in item else ''
            item_dict['link'] = item['url'] if 'url' in item else ''
            item_dict['publisher'] = item['source']['title'] if 'source' in item and 'title' in item['source'] else ''
            item_dict['description'] = cleanhtml(item['description']) if 'description' in item else ''
            final_list.append(item_dict)
    print('Serp parsed')
    return final_list
        