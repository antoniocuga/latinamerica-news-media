#!/usr/bin/env python
# -*- coding: utf-8 -*-

import newspaper, time, sys, os, django
import json
import datetime
import concurrent.futures
import csv
import dateparser
import re
from time import gmtime, strftime
from newspaper import Config, Article, Source
from nltk.tokenize import word_tokenize
from bs4 import BeautifulSoup
from pathlib import Path
import os
 
feed_news = []
feed_logs = []
done_url = []
languages = ['es', 'pt', 'en']
base_path ="/opt/dailycorruption/news_crawler"
outlets_file = "outlets_list.csv"
lexicon_values = "lexicon_values.csv"
django_path = "/opt/dailycorruption"

config = Config()
config.follow_meta_refresh = True
config.memoize_articles = True
config.fetch_images=False
config.verbose = False

sys.path.append(django_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dc_platform.settings")
django.setup()

from newsfeed.models import News

lexicon_list = []

def download_outlets(dataset):  
  with open('{}/{}'.format(base_path, dataset)) as csvfile:
    outlets = csv.DictReader(csvfile)
    create_process(outlets)
  return False

def create_process(outlets):
  with concurrent.futures.ProcessPoolExecutor() as executor:
    for outlet in outlets:
      donwload_mediaOutlet(outlet)
      #future = executor.submit(donwload_mediaOutlet, outlet)
  return False


def donwload_mediaOutlet(outlet):
  #newspaper
  media_outlet = Source(outlet["url"], config)
  media_outlet.build()
  # media_outlet.categories_to_articles()
  # media_outlet.generate_articles()
  count_articles = len(media_outlet.articles)
  if(count_articles > 0):
    print("Building {} for {}".format(count_articles, outlet["outlet"]))
    for article in media_outlet.articles:
      url = article.url
      process_article(url, outlet)
    return media_outlet
  print("No articles {} for {}".format(count_articles, outlet["outlet"]))
  return False

def custom_building(outlet):

  return articles

def process_article(url, outlet):

  if(validate_exists(url)):
    print("Previous saved {} ".format(outlet["outlet"]))
    pass

  article = newspaper.Article(url, language='es')
  
  if(article.source_url != outlet['url']):
    print("Source not registered - {}".format(article.source_url))
    return False
  
  print("Downloading {} ...".format(url))
  article.download()
  time.sleep(0.2)

  if article.download_state == 2:
    article.parse()
    article = validate_content(article)

    if (article.publish_date and article.text):
      save_news(article, outlet["country"])
      print("Saved {} ".format(url))
  
  return False

def validate_content(article):  
  print("Validating {} ".format(article.url))
  article.excerpt = get_field_value("excerpt", article)
  article.text = get_field_value("text", article)
  article.publish_date = get_field_value("publish_date", article)

  return article

def get_field_value(field, article):

  doc = BeautifulSoup(article.html, 'html.parser')  

  patterns = {
    "publish_date": [
      "span.meta-datestamp",
      "#article > h3",
      'div.td-post-header > header > div > span > time',
      '#date',
      'div.breadcrumb.col-lg-6.col-md-12.col-sm-12.col-xs-12 > span',
      'head > meta:nth-child(60)',
      '#barra-agencias-info > div.info-notaemol-porfecha',
      'div.col-sm-6.col-md-5.text-right.text-left-xs > h4 > small > span'
    ],
    "text": [
      "#content div.tx.mce.m-blk"
    ],
    "excerpt": [
      "meta[name='description']",
      "meta[property='og:description']",
      "meta[name='twitter:description']"
    ]
  }

  if(field == "excerpt"):
    
    if(article.meta_description):
      return article.meta_description

    for p in patterns[field]:
      value = \
        article.extractor.get_meta_content(article.clean_doc, p)
      if(value):
        return value
      return article.text[:150]
  
  if(field == "text"):
    if(article.text):
      return article.text

    for p in patterns[field]:
      value = doc.select_one(p)
      if(value):
        value = value.get_text()
        return value      


  if(field == "publish_date"):

    if(article.publish_date):
      return article.publish_date
    
    if(article.html):
      value = regex_date(article.html)
      if(value):
        return date_format(value)

    for p in patterns[field]:
      value = doc.select_one(p)
      if(value):
        value = value.get_text()
        value = date_format(value)
        return value

  return None

def regex_date(doc):

  #2019-01-24 00:00:42
  pattern = r'(\d+-\d+-\d+ \d+:\d+:\d+)'
  date_matches = re.search(pattern, doc)
  if(date_matches):
    return date_matches.group(0)

  pattern = r'(\d+-\d+-\d+T\d+:\d+:\d+-\d+:\d+)'
  date_matches = re.search(pattern, doc)
  if(date_matches):
    return date_matches.group(0)

  pattern = r'(\d+-\d+-\d+T\d+:\d+:\d+.\d+Z)'
  date_matches = re.search(pattern, doc)
  if(date_matches):
    return date_matches.group(0)

  pattern = r'(\d+-\d+-\d+T\d+:\d+:\d+Z)'
  date_matches = re.search(pattern, doc)
  if(date_matches):
    return date_matches.group(0)

  return None


def date_format(date):
  try: 
    return dateparser.parse(date,
      languages=languages,
      date_formats=["%Y-%m-%d %H:%M"])
  except: return None

def validate_exists(url):
  url = url.replace("http://","")
  url = url.replace("https://","")
  
  if(url in done_url):
    return True
  else:
    done_url.append(url)

  return News.objects.exist_url(url)

def save_news(data, country):
  news_object = News.objects.save_news(data, country)  
  return news_object

if __name__ == "__main__":

  download_outlets(outlets_file)
  
  # url = "https://www.latercera.com/politica/noticia/gobierno-busca-fortalecer-ley-zamudio-convocara-una-consulta-ciudadana/505252/"
  # process_article(url, 
  #   {
  #     "url": "https://www.latercera.com",
  #     "country": "chile",
  #     "outlet": "laterceracom"
  #   }
  # )

  
