from enum import IntEnum


class CrawlDepth(IntEnum):
    SHOPPING_MALL = 1
    PRODUCT_LIST = 2
    PRODUCT = 3
    OPTION = 4
