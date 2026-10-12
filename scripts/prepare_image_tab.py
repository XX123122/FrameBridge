"""Prepare one blank image-mode tab in the user's existing Edge CDP session.

Does not submit, upload files, read credentials, or create a browser profile.
"""
import argparse
import json
from web_chatgpt import connected_browser, prepare_image_page, TaskError


def prepare(endpoint):
    with connected_browser(endpoint) as browser:
        if len(browser.contexts) != 1:
            raise TaskError('需要唯一的已授权浏览器会话，不能猜测其它登录档')
        page = prepare_image_page(browser.contexts[0])
        return {'page': page.url, 'image_mode_selected': True, 'request_submitted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cdp', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.cdp), ensure_ascii=False, indent=2))
