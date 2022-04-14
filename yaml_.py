import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)

with open('source.yaml') as f:
    source = yaml.safe_load(f)

with open('request_headers.yaml') as f:
    request_headers = yaml.safe_load(f)

with open('sheet_headers.yaml') as f:
    sheet_headers = yaml.safe_load(f)
