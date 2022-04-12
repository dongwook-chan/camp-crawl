from typing import Dict, Tuple
import sys

import requests
from bs4 import BeautifulSoup

import config


def search_tag_recursively(
    tag_tree: BeautifulSoup, tag_selector: Dict
) -> None:
    for this_tag_selector, children_tag_selector in tag_selector.items():
        children_tag_tree = tag_tree(this_tag_selector)
        search_tag_recursively(children_tag_tree, children_tag_selector)


def get_request(url: str) -> Tuple[str, bool]:
    for retries in range(config.config['retries']):
        response = requests.get(url, headers=config.headers)
        if response.status_code == 200:
            return response.text, False

    print(f"'{url}'에 대한 get request 중 에러 발생:{response.status_code}")
    return None, True


if __name__ == '__main__':

    for source_name, source_detail in config.source.items():
        for page_no in range(1, 1000):
            url = source_detail['product_list_url'].format(page_no=page_no)
            html_doc, err = get_request(url)
            if err:
                continue    # TODO: 어떤 behavior?

            soup = BeautifulSoup(html_doc, 'html.parser')

            product_list = soup.select('ul.prdList.grid4')

            if len(product_list) == 0:
                # 이미 모든 상품을 조회했기 때문에 더 이상 조회할 상품 없음 -> 다음 쇼핑몰로
                break

            for product in product_list[0].select('a[name^=anchorBoxName]'):
                url = source_detail['domain_name'] + product['href']
                html_doc, err = get_request(url)
                if err:
                    continue

                # 1. 상품 페이지 링크

                # 2. 상품 이름

                print(html_doc)
                sys.exit()

            sys.exit()

            for product in product_list('a[name^=anchorBoxName]'):
                product['href']
    sys.exit()
