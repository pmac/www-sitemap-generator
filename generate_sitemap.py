#!/usr/bin/env python

# import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
# from aiohttp import ClientSession


CANONICAL_DOMAIN = 'https://www.mozilla.org'
SITEMAP_JSON_URL = CANONICAL_DOMAIN + '/sitemap.json'
OUTPUT_FILE = Path('./etags.json')
REQUEST_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Macintosh Intel Mac OS X 10.13 rv: 62.0) Gecko/20100101 Firefox/62.0'
}


def get_current_etags():
    with OUTPUT_FILE.open() as fh:
        etags = json.load(fh)

    return etags


def write_new_etags():
    with OUTPUT_FILE.open('w') as fh:
        json.dump(etags, fh, sort_keys=True, indent=2)


def get_sitemap_data():
    resp = requests.get(SITEMAP_JSON_URL)
    resp.raise_for_status()
    return resp.json()


def generate_all_urls(data):
    all_urls = []
    for url, locales in data.items():
        if locales:
            for locale in locales:
                all_urls.append('{}/{}{}'.format(CANONICAL_DOMAIN, locale, url))
        else:
            all_urls.append('{}{}'.format(CANONICAL_DOMAIN, url))

    return all_urls


def get_etags(urls):
    current_etags = get_current_etags()
    etags = {}
    for url in urls:
        headers = REQUEST_HEADERS.copy()
        curr_etag = current_etags.get(url)
        if curr_etag:
            headers['if-none-match'] = curr_etag['etag']
        resp = requests.head(url, headers=headers)
        etag = resp.headers.get('etag')
        if etag and resp.status_code == 200:
            etags[url] = {
                'etag': resp.headers['etag'],
                'date': datetime.now(timezone.utc).isoformat(),
            }
            print('.', end='', flush=True, file=sys.stderr)
        else:
            if curr_etag:
                etags[url] = curr_etag

            if resp.status_code == 304:
                print('-', end='', flush=True, file=sys.stderr)
            else:
                # print(url, resp.headers, file=sys.stderr)
                print('x', end='', flush=True, file=sys.stderr)

    if etags == current_etags:
        return None

    return etags


def main():
    urls = generate_all_urls(get_sitemap_data())
    etags = get_etags(urls)
    if etags:
        write_new_etags(etags)


if __name__ == '__main__':
    main()
