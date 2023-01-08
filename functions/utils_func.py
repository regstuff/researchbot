import re
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from trafilatura import fetch_url, extract
from trafilatura.settings import use_config
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('../vecsearch/multi-qa_v1-distilbert-mean_cos')
model.max_seq_length = 510 # Extend token limit # https://github.com/UKPLab/sentence-transformers/issues/364
print(model)

clubbed_wc = 50 # Clubbed sentence groups will be as close to (and above) this.
token_len = model.max_seq_length*0.7 # Transformer can handle this many words. Any para/cluster bigger than this must be segmented and embeddings averaged over segments
summ_percent = 0.25 # Summary length as percentage of original text
cluster_distance = 1.25 # Distance between clusters to be considered as separate clusters. Higher value means fewer clusters. Lower value means more clusters.

config = use_config() # Set trafilatura config to prevent SIgnal in main thread python error # https://github.com/adbar/trafilatura/issues/202
config.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")

def dict2txt(dict_list, xtra_params):
    final_str = ''
    for item in dict_list: 
        final_str += f"#### [{item['title']}]({item['link']})" # H4 heading for title with link
        for param in xtra_params: # Add the param value based on whether it is inline or newline
            final_str += f' | {param}: {item[param]}' if xtra_params[param] == 'inline' else f' \n\n {item[param]}'
        final_str += ' \n\n'
    return final_str

def cleanhtml(html):
    return re.sub('<.*?>', '', html).replace('&nbsp;', ' ').replace('&hellip;', '...').replace('&amp;', '&').replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>').replace('&apos;', "'").replace('&lsquo;', "'").replace('&rsquo;', "'").replace('&ldquo;', '"').replace('&rdquo;', '"').replace('&ndash;', '-').replace('&mdash;', '-').replace('&deg;', 'o') # replace html entities &nbsp; &hellip; etc

alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|Mt)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov|me|edu)"
digits = "([0-9])"

def split_into_sentences(text):
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text)
    if "..." in text: text = text.replace("...","<prd><prd><prd>")
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    sentences = [s.replace('"!', '!"').replace('"?', '?"').replace('".', '."') for s in sentences]
    return sentences

def get_page(url):
    print('Downloading', url)
    downloaded = fetch_url(url)
    if downloaded: 
        print('Extracting...')
        return extract(downloaded, config=config)
    else: return ''

def club_sents(all_sents, clubbed_wc):
  clubbed_sents = []
  clubbed_indexes = []
  i = 0
  while i < len(all_sents) - 1:
    start_index = i
    grouped_sent = all_sents[i]
    count = i
    while grouped_sent.count(' ') < clubbed_wc and count < len(all_sents) - 1:
      count += 1
      grouped_sent += ' ' + all_sents[count]
    i = count+1
    end_index = i
    clubbed_sents.append(grouped_sent.replace('-',' '))
    clubbed_indexes.append([start_index, end_index])
  return clubbed_sents, clubbed_indexes

def title_sent(para, max_true):
  sents = split_into_sentences(para)
  sents_embed = model.encode(sents)
  if para.count(' ') < token_len: para_embedding = model.encode(para) # If len of para is less than 350, then bert can handle as it has token limit of 510
  else: 
    split_para, split_para_index = club_sents(para, token_len) # Split the paras into sections of 350 words approx and average embeddings to get whole para's embeddings
    para_embedding = model.encode(split_para)
    para_embedding = sum(para_embedding)/len(para_embedding)
  cos_scores = []
  for i, sent in enumerate(sents): cos_scores.append(util.cos_sim(sents_embed[i], para_embedding))
  #cos_scores.sort(reverse=True)
  if cos_scores: 
    max_score = max(cos_scores)
    if max_true:
      return [max_score, sents[cos_scores.index(max_score)], sents, para_embedding]
    else:
      summ_len = summ_percent*para.count(' ')
      cos_scores = [[x, cos_scores.index(x)] for x in cos_scores]
      cos_scores.sort(reverse=True)
      count = 0
      sum_sent = []
      while ' '.join([x[1] for x in sum_sent]).count(' ') < summ_len:
        sum_sent.append([cos_scores[count][1], sents[cos_scores[count][1]]])
        count += 1
        #print(sum_sent)
      sum_sent.sort()
      sum_sent = ' '.join([x[1] for x in sum_sent])
      return [max_score, sum_sent, sents, para_embedding]
  else: return [-1, '', [], []]

def clean_text(txt):
  txt = [x for x in txt.split('\n') if x.strip() != '']
  txt = '\n'.join(txt)
  return txt

def create_clusters(all_sents):
  sents_embeddings = model.encode(all_sents)
  #sents_embeddings = sents_embeddings /  np.linalg.norm(sents_embeddings, axis=1, keepdims=True)
  clustering_model = AgglomerativeClustering(n_clusters=None, distance_threshold=cluster_distance) #, affinity='cosine', linkage='average', distance_threshold=0.4)
  #clustering_model = AgglomerativeClustering(n_clusters=None, affinity='cosine', linkage='average', distance_threshold=0.6)
  clustering_model.fit(sents_embeddings)
  cluster_assignment = clustering_model.labels_

  clustered_sentences = {}
  sentence_dict = dict()
  for sentence_id, cluster_id in enumerate(cluster_assignment):
      if cluster_id not in clustered_sentences:
          clustered_sentences[cluster_id] = []

      clustered_sentences[cluster_id].append(sentence_id)
      sentence_dict[sentence_id] = cluster_id

  cluster_list = [sentence_dict[id] for id in sentence_dict]
  fixed_list = cluster_list.copy()
  for i in range(len(all_sents)):
    if i > 1 and cluster_list[i] != cluster_list[i-1]: 
      if cluster_list[i] == cluster_list[i-2]: fixed_list[i-1] = fixed_list[i]
      elif cluster_list[i] == cluster_list[i-3]: 
        fixed_list[i-1] = fixed_list[i]
        fixed_list[i-2] = fixed_list[i]
  #print(fixed_list)

  # Club texts of the same group
  all_groups = []
  i = 0
  while i < len(all_sents):
    group = [all_sents[i]]
    count = i
    while count < len(all_sents)-1 and fixed_list[count] == fixed_list[count+1]:
      group.append(all_sents[count+1])
      count += 1
    i += len(group)
    all_groups.append(' '.join(group))
  return all_groups

def get_summary(txt):
    cleaned_text = clean_text(txt)
    all_sents = split_into_sentences(cleaned_text)
    #clubbed_sents, clubbed_indexes = club_sents(all_sents, clubbed_wc)
    #for c in clubbed_sents: print(c)
    #print('='*30)
    #all_clusters = create_clusters(clubbed_sents)
    all_clusters = create_clusters(all_sents)
    all_clusters = [x for x in all_clusters if x.count(' ') > 50]
    #for g in all_clusters: print(g)
    full_summary = ''
    for g in all_clusters: 
        [max_score, summary, sents, para_embedding] = title_sent(g, False)
        full_summary += summary + '\n'
    return full_summary