# Standard list of parameters for items: title (subtitle is subsumed in title with :), link, author, publisher, description
import feedparser, time, re, openai
from functions.utils_func import *

with open('keys.venv', 'r') as f: keys = eval(f.read())
openai.api_key = keys['openai_api_key']

def webnews(query, hrs, sitelist, topN): # to get news from specific sites, which may be buried deep in google news
    for site in sitelist:
        final_list = []
        gnews_feed = f"https://news.google.com/rss/search?q=intext:{query.replace(' ','+')}+when:{hrs}h+inurl:{site}&hl=en-IN&gl=IN&ceid=IN:en"
        items = feedparser.parse(gnews_feed)
        for i, item in enumerate(items['entries']):
            if i >= topN: break
            item_dict = dict()
            item_dict['title'] = item['title'] if 'title' in item else ''
            item_dict['link'] = item['link'] if 'link' in item else ''
            item_dict['publisher'] = item['source']['title'] if 'source' in item and 'title' in item['source'] else ''
            item_dict['description'] = cleanhtml(item['summary']) if 'summary' in item else ''
            final_list.append(item_dict)
    print('Got more Web News results')
    return final_list



def get_summarize_page(url):
    tima = time.time()
    result = get_page(url)
    print('Page downloaded in ', time.time() - tima, ' seconds')
    tima = time.time()
    page_paras = [x for x in result.split('\n') if x.strip().count(' ') > 25]
    #summary = ''
    #for para in page_paras:
        #summary_sent = get_summary(para)
        #if summary_sent: summary += summary_sent + '\n\n'
    summary = get_summary(result)
    print('Page summarized in ', time.time() - tima, ' seconds')
    return summary, result


def openai_summary(txt):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt='Summarize the text in 150 words and list 5 topic tags in csv format. The topics should be no longer than 2 or 3 words.\n' + txt + '\nSummary:',
        temperature=0.7,
        max_tokens=1500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    print('Got davinci summary')
    davinci = response.choices[0].text

    curie_tokens = 2048-txt.count(' ')/0.7
    if curie_tokens > 0: 
        response = openai.Completion.create(
            engine="text-curie-001",
            prompt=txt + '\nList 5 tags for the text. Tags should be utmost 2-3 words long.\n-',
            temperature=0.7,
            max_tokens=300,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        curie = response.choices[0].text
        print('Got curie summary')
    else: curie = 'The article was too long for Curie to summarize.'
    davinci_lower = davinci.lower()
    tags = davinci_lower.split('tags:')[1].strip() if 'tags:' in davinci_lower else ''
    return davinci, curie, tags