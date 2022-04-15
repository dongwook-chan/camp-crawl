import logging
from typing import Dict, DefaultDict, List, Tuple
from collections import defaultdict
import json

from bs4 import BeautifulSoup
from bs4 import NavigableString

# wrapper for existing modules
import logging_
import constants
import yaml_
import requests_
import openpyxl_


logging_.init_root_logger()
logger = logging.getLogger(__name__)


def search_tag_recursively(
    tag_tree: BeautifulSoup, tag_selector: Dict
) -> None:
    for this_tag_selector, children_tag_selector in tag_selector.items():
        children_tag_tree = tag_tree(this_tag_selector)
        search_tag_recursively(children_tag_tree, children_tag_selector)


def normalize_url(
    abnormal_url: str
) -> str:
    normal_url = abnormal_url[2:].replace('small', 'big')
    return normal_url


def append_to_sheet_row(
    cell_value: Tuple[str, Dict, DefaultDict, List]
) -> None:
    if isinstance(cell_value, (dict, defaultdict, list)):
        if len(cell_value) == 0:
            cell_value = ''
        else:
            cell_value = json.dumps(cell_value, ensure_ascii=False)
    sheet_row.append(cell_value)


def end_node(tag):
    if tag.name in ("img"):
        return True
    if tag.name not in ("div", "span"):
        return False
    # if str return
    if isinstance(tag, NavigableString):
        return False
    # if no text return false
    if not tag.text:
        return False
    # no other tags inside other than text
    elif len(tag.find_all(text=False)) > 0:
        return False
    return True


def get_either_attrs(
    tag: BeautifulSoup, attr_name_list: List[str]
) -> Tuple[str, int]:
    for attr_name in attr_name_list:
        if attr_name in tag.attrs:
            return tag[attr_name]


if __name__ == '__main__':
    openpyxl_.init_sheet()

    for source_name, source_detail in yaml_.source.items():
        for page_no in range(1, 1000):
            logger.debug(f"product_list no: {page_no}")
            # [상품 목록 페이지]
            try:
                product_list_soup = requests_.get_soup_for_url(
                    product_list_url :=
                    source_detail['product_list_url'].format(page_no=page_no),
                    constants.CrawlDepth.PRODUCT_LIST
                )

                try:
                    product_list_tag = product_list_soup.select(
                        'ul.prdList.grid4'
                    )[0]
                except IndexError:
                    # 이미 모든 상품을 조회했기 때문에 더 이상 조회할 상품 없음 -> 다음 쇼핑몰로
                    break

            except requests_.NextShoppingMall:
                break
            except requests_.NextProductList:
                continue

            for product_tag in product_list_tag.select(
                'a[name^=anchorBoxName]'
            ):
                # [상품 페이지]
                try:
                    product_soup = requests_.get_soup_for_url(
                        product_url :=
                        source_detail['domain_name'] + product_tag['href'],
                        constants.CrawlDepth.PRODUCT
                    )
                except requests_.NextProductList:
                    break
                except requests_.NextProduct:
                    continue

                product_id = product_soup.select(
                    'meta[property="product:productId"]'
                )[0]['content']

                global sheet_row
                sheet_row = []

                # [상품 페이지 > 우측 상단 상품 요약]
                product_summary_area = product_soup.select('div.infoArea')[0]

                # 1. 상품 페이지 링크
                logger.debug("#1")
                append_to_sheet_row(product_url)

                # 2. 상품 이름
                logger.debug("#2")
                product_name_tag = product_summary_area.select(
                    'div.headingArea > h2'
                )[0]
                append_to_sheet_row(product_name_tag.get_text())

                # 3. 상품 브랜드
                logger.debug("#3")
                brand_name_tag = product_summary_area.select(
                    'div.cu_brand'
                )[0]
                append_to_sheet_row(brand_name_tag.get_text())

                # 4. 상품 정가, 5. 상품 할인가
                logger.debug("#4, 5")
                product_price_tag = product_summary_area.select(
                    'div.detail_price'
                )[0]

                custom = int(product_price_tag['ec-data-custom'].split('.')[0])
                price = int(product_price_tag['ec-data-price'])
                if int(product_price_tag['ec-data-custom'].split('.')[0]) == 0:
                    # 할인 없음 -> 정가와 할인가 동일
                    append_to_sheet_row(price)
                    append_to_sheet_row(price)
                else:
                    # 할인 있음
                    append_to_sheet_row(custom)
                    append_to_sheet_row(price)

                # 6. 본품 옵션 7. 추가상품 옵션
                logger.debug("#6, 7")
                option_table_tag = product_summary_area.select(
                    'table.xans-product-option'
                )[0]

                option_tbody_tag_list = option_table_tag.select(
                    'tbody.xans-product-option'
                )

                option_dict1 = defaultdict(dict)
                option_dict2 = defaultdict(dict)
                option_type_ctr = defaultdict(int)

                for option_tbody_tag in option_tbody_tag_list:
                    option_tag = option_tbody_tag.tr.td.contents[0]
                    option_type = option_tag['option_title']

                    option_value_tag_list = option_tag.select(
                        '[value], [option_value]'
                    )
                    for option_value_tag in option_value_tag_list:
                        if 'value' in option_value_tag.attrs:
                            option_id = option_value_tag['value']
                        elif 'option_value' in option_value_tag.attrs:
                            option_id = option_value_tag['option_value']

                        if option_id[0] == '*':
                            continue

                        try:
                            option_response = requests_.get_json_for_url(
                                option_url :=
                                source_detail['domain_name'] +
                                "/exec/front/shop/" +
                                "CalculatorProduct?product_no=" +
                                str(product_id) +
                                "&is_subscription=F&product%5B" +
                                option_id +
                                "%5D=1",
                                constants.CrawlDepth.OPTION
                            )
                        except requests_.NextProduct:
                            break
                        except requests_.NextOption:
                            continue

                        option_type_ctr[option_type] += 1
                        option_key = (
                            option_type + str(option_type_ctr[option_type])
                        )
                        option_title = option_value_tag.attrs.get(
                            'title', option_value_tag.get_text()
                        )
                        option_price = (
                            option_response[option_id]['ori_item_price']
                        )
                        if option_type != '옵션':
                            option_dict = option_dict1
                        else:
                            option_dict = option_dict2
                        option_dict[option_key]['품명'] = option_title
                        option_dict[option_key]['가격'] = option_price
                append_to_sheet_row(option_dict1)
                append_to_sheet_row(option_dict2)

                # 8. 상품 썸네일 이미지 링크
                logger.debug("#8")
                img_area = product_soup.select(
                    'div.imgArea'
                )[0]

                thumbnail_tag = img_area.select(
                    'div.thumbnail img'
                )[0]

                thumbnail_url_list = [thumbnail_tag['src'][2:]]

                img_list_area = img_area.select(
                    'div.listImg > ul'
                )[0]

                img_tag_list = img_list_area.select(
                    'img'
                )

                for i in range(1, len(img_tag_list)):
                    img_tag = img_tag_list[i]
                    thumbnail_url = img_tag['src'][2:].replace(
                        'small', 'big'
                    )
                    thumbnail_url_list.append(thumbnail_url)
                append_to_sheet_row(thumbnail_url_list)

                # 9. 상세페이지 내 모든 컨텐츠
                logger.debug("#9")
                product_detail_area = product_soup.select(
                    'div.cont'
                )[0]

                product_detail_tag_list = product_detail_area.find_all(
                    end_node
                )

                product_detail_list = []
                visited_text = {}
                for product_detail_tag in product_detail_tag_list:
                    if product_detail_tag.name in ('img'):
                        product_detail_list.append(
                            source_detail['domain_name'] +
                            get_either_attrs(
                                product_detail_tag, ['ec-data-src', 'src']
                            )
                        )
                    elif product_detail_tag.name in ('span', 'div'):
                        product_detail_text = product_detail_tag.get_text()
                        if product_detail_text:
                            product_detail_list.append(
                                product_detail_text
                            )

                # print(product_detail_list)
                append_to_sheet_row(product_detail_list)

                openpyxl_.append_to_sheet(sheet_row)

    openpyxl_.save_sheet()
