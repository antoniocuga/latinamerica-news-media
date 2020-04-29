#Latin America media outlets crawler

This script allows to download a newsfeed from different news media in Latin America. The data downloaded is in JSON Format.

Python3
Scrapy (https://docs.scrapy.org)
Newspaper (https://newspaper.readthedocs.io)
BeautifulSoup (https://www.crummy.com)

## Install

python3 -m venv venv

souce venv/bin/activate

pip install -r requirements.txt

## List of medias

outlets_list.csv

## Run spider

scrapy runspider download_news.py -o download_news.json





