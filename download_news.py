import scrapy
from newspaper import Article, Config, Source
import time
import sys
import os
import json
import datetime
import csv
import dateparser
import re
from time import gmtime, strftime
from bs4 import BeautifulSoup
from pathlib import Path

languages = ['es', 'pt', 'en']
done_url = []

config = Config()
config.follow_meta_refresh = True
config.memoize_articles = False
config.fetch_images = False
config.verbose = False


class DownloadNewsSpider(scrapy.Spider):
    name = 'download_news'

    def start_requests(self):
        download_medias = []

        with open("outlets_list.csv", newline='') as csvfile:
            outlets = csv.DictReader(csvfile)
            for outlet in outlets:
                download_medias.append(
                    scrapy.Request(
                        url=outlet['url'],
                        callback=self.downloadMediaOutlet,
                        meta={'outlet': outlet}
                    )
                )

            return download_medias

    def downloadMediaOutlet(self, response):
        outlet = response.meta.get('outlet')

        media_outlet = Source(outlet["url"], config)
        media_outlet.build()

        count_articles = len(media_outlet.articles)

        if(count_articles > 0):
            print("Building {} for {}".format(
                count_articles, outlet["outlet"]
            ))

            for article in media_outlet.articles:
                data = self.process_article(article.url, outlet)

                if data:
                    yield {
                        "title": data.title,
                        "excerpt": data.excerpt,
                        "body": data.text,
                        "country": outlet["country"],
                        "publish_date": data.publish_date,
                        "url": data.url,
                        "outlet": data.source_url
                    }

        else:
            print("No articles {} for {}".format(
                count_articles, outlet["outlet"]
            ))

    def process_article(self, url, outlet):

        article = Article(url, language='es')

        if(self.validate_exists(url)):
            print("Previous saved {} ".format(outlet["outlet"]))
            return False

        if(article.source_url != outlet['url']):
            print("Source not registered - {}".format(article.source_url))
            return False

        print("Downloading {} ...".format(url))
        article.download()
        time.sleep(0.2)

        if article.download_state == 2:
            article.parse()
            article = self.validate_content(article)

            if (article.title and article.publish_date and article.text):
                return article

            return False

        return False

    def validate_content(self, article):
        print("Validating {} ".format(article.url))

        article.excerpt = self.get_field_value("excerpt", article)
        article.text = self.get_field_value("text", article)
        article.publish_date = self.get_field_value("publish_date", article)

        return article

    def get_field_value(self, field, article):

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
                value = self.regex_date(article.html)
                if(value):
                    return self.date_format(value)

            for p in patterns[field]:
                value = doc.select_one(p)
                if(value):
                    value = value.get_text()
                    value = self.date_format(value)
                    return value

    def regex_date(self, doc):

        # 2019-01-24 00:00:42
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

    def date_format(self, date):
        try:
            return dateparser.parse(
                date,
                languages=languages,
                date_formats=["%Y-%m-%d %H:%M"]
            )
        except Exception:
            raise

    def validate_exists(self, url):
        url = url.replace("http://","")
        url = url.replace("https://","")

        if(url in done_url):
            return True

        done_url.append(url)
        return False