import json
import requests
import re
import sys
import random
from concurrent.futures import ThreadPoolExecutor
from . import *
from .util import *
from .config import config

proxy_rgx = re.compile(r'\d+\.\d+\.\d+\.\d+:\d+')

def get_proxies(html):
    return proxy_rgx.findall(html)

def click_with_pr(url, pr):
    pr_dict = { 'http': pr, 'https': pr }
    try:
        request_retry(
            'GET', url, 
            proxies=pr_dict, 
            timeout=config['timeout'],
            headers=config['headers'],
            retry=config['retry'],
        )
        return [True, '']
    except Exception as ex:
        return [False, str(ex)]

def tr_click(url, pr):
    succ, msg = click_with_pr(url, pr)
    if succ:
        print(f'url: {url}, pr: {pr} 点击成功')
    else:
        print(f'url: {url}, pr: {pr} 点击失败：{msg}')

def click():
    pr_list = open(config['proxyFile']).read().split('\n')
    pr_list = list(filter(None, map(lambda x: x.strip(), pr_list)))
    pool = ThreadPoolExecutor(config['threads'])
    hdls = []
    
    for _ in range(config['tasks']):
        url = random.choice(config['urls'])
        pr = random.choice(pr_list)
        hdl = pool.submit(tr_click, url, pr)
        hdls.append(hdl)
        
    for h in hdls: h.result()

def fetch():
    
    ofile = open(config['proxyFile'], 'a')
    
    for url in config['urls']:
        print(url)
        html = request_retry(
            'GET', url,
            timeout=config['timeout'],
            headers=config['headers'],
            retry=config['retry'],
        ).text
        proxies = get_proxies(html)
        for pr in proxies:
            succ, msg = click_with_pr(config['testUrl'], pr)
            if succ:
                print(f'{pr} 验证成功')
                ofile.write(pr + '\n')
            else:
                print(f'{pr} 验证失败：{msg}')
    ofile.close()
    print('done...')
    
def main():
    global get_proxies
    cmd = sys.argv[1]
    config_fname = sys.argv[2] if len(sys.argv) > 2 else 'config.json'
    if not config_fname.endswith('json'):
        print('请提供 JSON 文件')
        return
    user_config = json.loads(open(config_fname, encoding='utf-8').read())
    config.update(user_config)
    if config['external']:
        mod = load_module(config['external'])
        get_proxies = getattr(mod, 'get_proxies', get_proxies)
        
    if cmd == 'fetch':
        fetch()
    elif cmd == 'click':
        click()
    
if __name__ == '__main__': main()