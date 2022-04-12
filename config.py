import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)

with open('source.yaml') as f:
    source = yaml.safe_load(f)

with open('headers.yaml') as f:
    headers = yaml.safe_load(f)
