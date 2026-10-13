"""Read only visible composer/control metadata; never input values or auth storage."""
import argparse
import json
import re
from pathlib import Path
from web_chatgpt import connected_page, guard

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--cdp", required=True)
parser.add_argument("--page", required=True)
parser.add_argument("--result", action="store_true", help="检查当前对话结果的 UI 结构，不读取图片 URL")
parser.add_argument('--include-conversation-text', action='store_true', help='Sensitive: explicitly include private conversation text; do not post it publicly')
parser.add_argument('--screenshot', action='store_true', help='Sensitive: explicitly save a local screenshot, which may contain account/history information')
args = parser.parse_args()
with connected_page(args.cdp, args.page) as page:
    guard(page)
    fields = page.locator('textarea, [contenteditable="true"], [role="textbox"]').evaluate_all("""els =>
        els.filter(el => el.getBoundingClientRect().width && el.getBoundingClientRect().height)
        .map(el => ({tag:el.tagName, id:el.id, role:el.getAttribute('role'),
                    testid:el.getAttribute('data-testid'), placeholder:el.getAttribute('placeholder'),
                    editable:el.getAttribute('contenteditable'),
                    form_buttons: Array.from(el.closest('form')?.querySelectorAll('button') || [])
                        .map(button => ({aria:button.getAttribute('aria-label'), testid:button.getAttribute('data-testid'), text:button.innerText}))}))""")
    controls = page.get_by_role('button').evaluate_all("""els =>
        els.filter(el => el.getBoundingClientRect().width && el.getBoundingClientRect().height)
        .map(el => ({text:el.innerText, aria:el.getAttribute('aria-label'), testid:el.getAttribute('data-testid')}))
        .filter(el => /image|send|skip|continue|more|start|创建|图片|图像|生成|跳过|继续|开始|上传|更多|添加|照片|文件|工具|附件/i.test(el.text + ' ' + el.aria))
        .slice(0,30)""")
    image_links = page.get_by_role('link', name=re.compile(r'^(Images|图片|图像)$', re.I))
    print(json.dumps({"title": page.title(), "fields": fields, "controls": controls,
                      "image_navigation_visible": any(image_links.nth(i).is_visible() for i in range(image_links.count())),
                      "request_submitted": False}, ensure_ascii=False, indent=2))
    if args.result:
        images = page.locator('main img, main canvas').evaluate_all("""els => els.map(el => ({
            tag:el.tagName, width:el.naturalWidth || el.width, height:el.naturalHeight || el.height,
            parents:Array.from((function*(n){for(let i=0;n&&i<14;i++,n=n.parentElement)yield n})(el))
                .map(n=>({tag:n.tagName, role:n.getAttribute('role'), id:n.id,
                          classes:String(n.className), testid:n.getAttribute('data-testid'),
                          turn_state:n.getAttribute('data-talvt-turn-state'),
                          attribute_names:Array.from(n.attributes).map(a=>a.name)}))
        }))""")
        main = page.locator('main')
        result = {'images': images, 'headings':main.get_by_role('heading').all_text_contents()}
        if args.include_conversation_text:
            result['current_conversation_text'] = main.inner_text()[:3000]
        print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.screenshot:
        screenshot = Path(__file__).resolve().parents[1] / 'logs/web-result-check.png'
        screenshot.parent.mkdir(exist_ok=True)
        page.screenshot(path=str(screenshot))
