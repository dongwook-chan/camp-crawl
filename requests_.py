import requests
import json

import yaml_
from bs4 import BeautifulSoup

import constants


class NextShoppingMall(Exception):
    pass


class NextProductList(Exception):
    pass


class NextProduct(Exception):
    pass


class NextOption(Exception):
    pass


def send_request(
    url: str, crawl_depth: constants.CrawlDepth
) -> requests.models.Response:
    for retries in range(yaml_.config['retries']):
        response = requests.get(url, headers=yaml_.request_headers)
        if response.status_code == 200:
            return response

    # print(f"'{url}'에 대한 get request 중 에러 발생:{response.status_code}")
    if crawl_depth == constants.CrawlDepth.PRODUCT_LIST:
        raise NextProductList
    elif crawl_depth == constants.CrawlDepth.PRODUCT:
        raise NextProduct
    elif crawl_depth == constants.CrawlDepth.OPTION:
        raise NextOption


def get_soup_for_url(
    url: str, crawl_depth: constants.CrawlDepth
) -> BeautifulSoup:
    html_doc = send_request(url, crawl_depth).text

    return BeautifulSoup(html_doc, 'html.parser')


def get_json_for_url(
    url: str, crawl_depth: constants.CrawlDepth
) -> BeautifulSoup:
    return json.loads(send_request(url, crawl_depth).text)
