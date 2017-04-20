# !/usr/bin/evn python3
# coding:utf-8
#
# 视频地址 https://edu.hellobi.com/course/156/play/lesson/2452
import os
import re
from hashlib import md5
from multiprocessing import Pool

import pymongo as pymongo
import requests
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
import json
import pymongo
# from splider_toutiao import config
# import *把config里的所有变量导进来
# from config import *

MONGO_URL= 'localhost'
MONGO_DB= 'toutiao'
MONGO_TABLE = 'toutiao'

GROUP_START= 1
GROUP_END= 20

KEYWORD= '街拍'

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

def get_page_index(offset,keyword):
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': '20',
        'cur_tab': 1
    }
    url = 'http://www.toutiao.com/search_content/?' + urlencode(data)

    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException as e:
        print('请求街拍首页数据出错')
        return None

def parse_page_index(html):
    data = json.loads(html)
    if data and 'data' in data.keys():
        for item in data.get('data'):
            yield item.get('article_url')

def get_page_detail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException as e:
        print('请求详情页出错',e)
        return None

def parse_page_detail(html,url):
    soup = BeautifulSoup(html,'lxml')
    title = soup.select('title')[0].get_text()
    # re.S 正则匹配模式
    images_pattern = re.compile('var gallery = (.*?);',re.S);
    result = re.search(images_pattern,html)
    if result:
        data = json.loads(result.group(1))
        if data and 'sub_images' in data.keys():
            sub_images = data.get('sub_images')
            images = [item.get('url') for item in sub_images]
            for image in images: download_image(image)
            # print(images)
            return {
                'title':title,
                'images':images,
                'url':url
            }

def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('存储到MONGODB',result)
        return True
    return False

def download_image(url):
    print('当前正在下载 ',url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            save_image(response.content)
            return response.text
        return None
    except RequestException:
        print('请求图片出错',url)
        return None

def save_image(content):
    file_path = '{0}/{1}.{2}'.format(os.getcwd(),md5(content).hexdigest(),'jpg')
    if not os.path.exists(file_path):
        with open(file_path,'wb') as f:
            f.write(content)
            f.close()

def main(offset):
    html = get_page_index(offset,KEYWORD)
    for url in parse_page_index(html):
        html_detail = get_page_detail(url)
        if html_detail:
            result = parse_page_detail(html_detail,url)
            # save_to_mongo(result)
            # print(result)

if __name__ == '__main__':
    group = [x*20 for x in range(GROUP_START,GROUP_END + 1)]
    pool = Pool()
    pool.map(main,group)