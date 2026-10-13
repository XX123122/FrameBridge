"""Opt-in local DOM/download integration tests. Every HTTPS request is intercepted.

Set FRAMEBRIDGE_FIXTURE_BROWSER=msedge (or chrome) to use an installed browser in
an isolated headless test context; no user profile and no real ChatGPT request.
"""
import base64
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import contextmanager

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from PIL import Image
from framebridge import Ledger, TaskError
from web_chatgpt import run, probe, collect, new_result, prepare_submission, record_web, normal_download, prepare_image_page, main, composer_text, composer_matches, resume_draft
from conversation_batch import run_batch, close_preview, history


@unittest.skipUnless(os.environ.get("FRAMEBRIDGE_FIXTURE_BROWSER"), "opt-in isolated browser fixture")
class BrowserFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.runtime = sync_playwright().start()
        cls.addClassCleanup(cls.runtime.stop)
        cls.browser = cls.runtime.chromium.launch(channel=os.environ['FRAMEBRIDGE_FIXTURE_BROWSER'], headless=True)
        cls.addClassCleanup(cls.browser.close)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.ledger = Ledger(self.temporary.name)
        self.ledger.init()
        Path(self.temporary.name, "prompts/a.txt").write_text("a cat, one image", encoding="utf-8")
        self.ledger.add("A", "prompts/a.txt", [], "outputs/A.png")
        self.context = self.browser.new_context(accept_downloads=True, service_workers="block")
        self.addCleanup(self.context.close)
        output = io.BytesIO()
        Image.new("RGB", (512, 288), "white").save(output, format="PNG")
        self.url = "data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii")
        self.html = '''<!doctype html><html><body>
        <div contenteditable="true" id="prompt-textarea"></div>
        <input type="file" accept="image/*" multiple>
        <button data-testid="send-button" onclick="submitOnce()">Send</button>
        <script>
        window.sendCount=0;
        function submitOnce() {
          window.sendCount++;
          const u=document.createElement('div'); u.dataset.messageAuthorRole='user';
          u.textContent=document.querySelector('#prompt-textarea').innerText; document.body.append(u);
          document.querySelector('#prompt-textarea').textContent='';
          const a=document.createElement('div'); a.dataset.messageAuthorRole='assistant';
          const img=document.createElement('img'); img.src='IMAGE_URL'; a.append(img);
          const button=document.createElement('button'); button.textContent='Download';
          button.onclick=()=>{ const link=document.createElement('a'); link.download='generated.png'; link.href=img.src; link.click(); };
          a.append(button); document.body.append(a); history.pushState({}, '', '/c/fixture-A');
        }
        </script></body></html>'''.replace("IMAGE_URL", self.url)
        self.request_count = 0
        def intercepted(route):
            self.request_count += 1
            if route.request.url == "https://chatgpt.com/":
                route.fulfill(status=200, content_type="text/html", body=self.html)
            else:
                route.abort()  # Fail closed: absolutely no external request is allowed.
        self.context.route("**/*", intercepted)
        self.page = self.context.new_page()
        self.page.goto("https://chatgpt.com/")

    def test_one_submit_normal_button_download_verified(self):
        self.assertFalse(probe(self.page)["request_submitted"])
        task = run(self.ledger, "A", self.page, "http://127.0.0.1:9222", timeout=10)
        self.assertEqual(self.page.evaluate("window.sendCount"), 1)
        self.assertEqual(task["status"], "completed")
        self.assertTrue(self.ledger.check("A")["valid_output"])
        self.assertEqual(self.request_count, 1)  # Fulfilled fixture; no server received it.
        self.assertEqual(collect(self.ledger, "A", self.page, "http://127.0.0.1:9222" )["status"], "completed")
        self.assertEqual(self.page.evaluate("window.sendCount"), 1)

    def test_verification_stops_before_submit(self):
        self.page.evaluate("document.title = 'Just a moment'")
        with self.assertRaises(TaskError):
            run(self.ledger, "A", self.page, "http://127.0.0.1:9222", timeout=10)
        self.assertEqual(self.page.evaluate("window.sendCount"), 0)
        self.assertEqual(self.ledger.task(self.ledger.load(), "A")["status"], "pending")

    def test_logged_out_with_two_controls_stops_before_submit(self):
        self.page.evaluate("document.body.insertAdjacentHTML('beforeend', '<button>Log in</button><button>Sign up</button>')")
        with self.assertRaisesRegex(TaskError, "login_required"):
            run(self.ledger, "A", self.page, "http://127.0.0.1:9222", timeout=10)
        self.assertEqual(self.page.evaluate("window.sendCount"), 0)
        self.assertEqual(self.ledger.task(self.ledger.load(), "A")["status"], "pending")

    def test_current_composer_role_and_image_entry_label(self):
        self.page.evaluate("const composer=document.querySelector('#prompt-textarea'); composer.removeAttribute('id'); composer.setAttribute('role','textbox'); document.body.insertAdjacentHTML('beforeend', '<button>创建图像 可视化呈现任何内容</button>')")
        result = probe(self.page)
        self.assertTrue(result["composer_editable"])
        self.assertTrue(result["image_entry_visible"])
        self.assertEqual(self.page.evaluate("window.sendCount"), 0)

    def test_matching_staged_draft_uses_normal_send(self):
        self.page.locator('#prompt-textarea').fill('a cat, one image')
        self.page.locator('[data-testid="send-button"]').evaluate("el => {el.removeAttribute('data-testid'); el.setAttribute('aria-label','发送')}")
        task = run(self.ledger, "A", self.page, "http://127.0.0.1:9222", timeout=10)
        self.assertEqual(task["status"], "completed")
        self.assertEqual(self.page.evaluate("window.sendCount"), 1)

    def test_different_draft_is_preserved_without_submit(self):
        self.page.locator('#prompt-textarea').fill('my unfinished draft')
        with self.assertRaises(TaskError):
            run(self.ledger, "A", self.page, "http://127.0.0.1:9222", timeout=10)
        self.assertEqual(self.page.locator('#prompt-textarea').inner_text(), 'my unfinished draft')
        self.assertEqual(self.page.evaluate("window.sendCount"), 0)

    def modern_result(self, state='complete'):
        prepare_submission(self.ledger, "A", self.page, "http://127.0.0.1:9222")
        record_web(self.ledger, "A", page_url=self.page.url)
        self.page.evaluate("""state => {
            const user = document.querySelector('[data-message-author-role="user"]');
            const response = document.querySelector('[data-message-author-role="assistant"]');
            user.removeAttribute('data-message-author-role');
            response.removeAttribute('data-message-author-role');
            response.setAttribute('data-talvt-turn-state', state);
            const image = response.querySelector('img');
            const download = response.querySelector('button');
            const gallery = document.createElement('div');
            gallery.dataset.testid = 'generated-image-gallery';
            const preview = document.createElement('button');
            preview.dataset.testid = 'generated-image-preview';
            preview.append(image); gallery.append(preview); response.replaceChildren(gallery);
            const main = document.createElement('main');
            const userHeading = document.createElement('h2'); userHeading.textContent = '你说：';
            const assistantHeading = document.createElement('h2'); assistantHeading.textContent = 'ChatGPT 说：';
            main.append(userHeading, user, assistantHeading, response); document.body.append(main);
            preview.onclick = () => {
                const dialog = document.createElement('div'); dialog.setAttribute('role', 'dialog');
                dialog.setAttribute('aria-modal', 'true'); main.setAttribute('aria-hidden', 'true');
                dialog.append(download); document.body.append(dialog);
            };
        }""", state)

    def test_current_gallery_preview_download_completes_without_resubmit(self):
        self.modern_result()
        result = collect(self.ledger, "A", self.page, "http://127.0.0.1:9222", timeout=10)
        self.assertEqual(result['status'], 'completed')
        self.assertTrue(self.ledger.check('A')['valid_output'])
        self.assertEqual(self.page.evaluate('window.sendCount'), 1)
        self.assertTrue(Path(self.temporary.name, 'logs/A/timing.md').exists())
        self.assertTrue(Path(self.temporary.name, 'logs/A/timing.json').exists())

    def test_async_preview_and_download_button_wait_without_resubmit(self):
        self.modern_result()
        self.page.evaluate("""() => {
            window.previewCount = 0;
            document.querySelector('[data-testid="generated-image-preview"]').onclick = () => {
                window.previewCount++;
                setTimeout(() => {
                    const dialog = document.createElement('div'); dialog.setAttribute('role','dialog');
                    document.body.append(dialog);
                    setTimeout(() => {
                        const button = document.createElement('button'); button.textContent='Download'; button.disabled=true;
                        button.onclick = () => {
                            const a=document.createElement('a'); a.download='generated.png';
                            a.href=document.querySelector('[data-testid="generated-image-preview"] img').src; a.click();
                        };
                        dialog.append(button); setTimeout(() => button.disabled=false, 200);
                    }, 200);
                }, 200);
            };
        }""")
        progress = []
        result = collect(self.ledger, 'A', self.page, 'http://127.0.0.1:9222', timeout=10,
                         progress=lambda phase, **metrics: progress.append(phase))
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(self.page.evaluate('window.previewCount'), 1)
        self.assertEqual(self.page.evaluate('window.sendCount'), 1)
        self.assertIn('opening_preview', progress)
        self.assertEqual(progress[-1], 'saved')

    def test_missing_preview_timeout_does_not_click_twice(self):
        self.modern_result()
        self.page.evaluate("() => {window.previewCount=0; document.querySelector('[data-testid=generated-image-preview]').onclick=()=>window.previewCount++;}")
        task = self.ledger.task(self.ledger.load(), 'A')
        result, image = new_result(self.page, task)
        with self.assertRaises(TaskError):
            normal_download(self.page, result, image, self.temporary.name, preview_timeout_ms=250)
        self.assertEqual(self.page.evaluate('window.previewCount'), 1)
        self.assertEqual(self.page.evaluate('window.sendCount'), 1)

    def test_verification_during_preview_wait_stops_without_download(self):
        self.modern_result()
        self.page.evaluate("() => {document.querySelector('[data-testid=generated-image-preview]').onclick=()=>document.title='Just a moment';}")
        task = self.ledger.task(self.ledger.load(), 'A')
        result, image = new_result(self.page, task)
        with self.assertRaisesRegex(TaskError, 'verification'):
            normal_download(self.page, result, image, self.temporary.name, preview_timeout_ms=250)
        self.assertFalse(Path(self.temporary.name, 'generated.png').exists())

    def test_image_mode_preparation_waits_default_text_without_submit(self):
        self.page.evaluate("""() => {
            const add=document.createElement('button'); add.setAttribute('aria-label','添加文件等内容');
            add.onclick=()=>{
                const entry=document.createElement('button'); entry.textContent='创建图像 可视化呈现任何内容';
                entry.onclick=()=>setTimeout(()=>document.querySelector('#prompt-textarea').textContent='创建图像 ',200);
                document.body.append(entry);
            };
            document.body.append(add);
        }""")
        page = prepare_image_page(self.context)
        self.assertEqual(page.locator('#prompt-textarea').inner_text().strip(), '')
        self.assertEqual(page.evaluate('window.sendCount'), 0)

    def test_generate_rejects_completed_before_connecting_browser(self):
        task = run(self.ledger, 'A', self.page, 'http://127.0.0.1:9222', timeout=10)
        self.assertEqual(task['status'], 'completed')
        with patch('web_chatgpt.connected_image_page') as connect, patch('sys.stdout', new_callable=io.StringIO):
            result = main(['--root', self.temporary.name, '--cdp','http://127.0.0.1:9222','generate','A','--confirmed'])
        self.assertEqual(result, 2)
        connect.assert_not_called()

    def test_generate_requires_confirmation_before_browser_connect(self):
        with patch('web_chatgpt.connected_image_page') as connect, patch('sys.stdout', new_callable=io.StringIO):
            result = main(['--root', self.temporary.name, '--cdp','http://127.0.0.1:9222','generate','A'])
        self.assertEqual(result, 2)
        connect.assert_not_called()

    def test_generate_connects_once_and_submits_once(self):
        @contextmanager
        def prepared(endpoint):
            yield self.page
        with patch('web_chatgpt.connected_image_page', side_effect=prepared) as connect:
            with patch('sys.stdout', new_callable=io.StringIO), patch('sys.stderr', new_callable=io.StringIO):
                result = main(['--root', self.temporary.name, '--cdp', 'http://127.0.0.1:9222',
                               'generate', 'A', '--confirmed', '--timeout', '10'])
        self.assertEqual(result, 0)
        self.assertEqual(connect.call_count, 1)
        self.assertEqual(self.page.evaluate('window.sendCount'), 1)
        self.assertTrue(self.ledger.check('A')['valid_output'])

    def batch_fixture(self, refusal=False):
        output = io.BytesIO()
        Image.new('RGB', (512, 288), 'blue').save(output, format='PNG')
        self.second_url = 'data:image/png;base64,' + base64.b64encode(output.getvalue()).decode('ascii')
        Path(self.temporary.name, 'prompts/b.txt').write_text('the cat stretches, one image', encoding='utf-8')
        self.ledger.add('B', 'prompts/b.txt', [], 'outputs/B.png')
        self.page.evaluate('''([first,second,refusal]) => {
            const main=document.createElement('main'); document.body.append(main);
            window.submitOnce=()=>{
                window.sendCount++;
                const turn=document.createElement('div'); turn.dataset.talvtTurnState='complete';
                const uh=document.createElement('h4'); uh.textContent='你说：';
                const user=document.createElement('div'); user.textContent=document.querySelector('#prompt-textarea').innerText;
                const ah=document.createElement('h4'); ah.textContent='ChatGPT 说：';
                turn.append(uh,user,ah); main.append(turn);
                document.querySelector('#prompt-textarea').textContent='';
                if(refusal && window.sendCount===2){
                    const text=document.createElement('p'); text.textContent='抱歉，我不能生成这张图片。'; turn.append(text);
                }else{
                    const gallery=document.createElement('div'); gallery.dataset.testid='generated-image-gallery';
                    const preview=document.createElement('button'); preview.dataset.testid='generated-image-preview';
                    const image=document.createElement('img'); image.src=window.sendCount===1?first:second;
                    preview.append(image); gallery.append(preview); turn.append(gallery);
                    preview.onclick=()=>{
                        const dialog=document.createElement('div'); dialog.setAttribute('role','dialog');
                        main.setAttribute('aria-hidden','true');
                        const download=document.createElement('button'); download.textContent='Download';
                        download.onclick=()=>{ const a=document.createElement('a');a.download='generated.png';a.href=image.src;a.click(); };
                        const close=document.createElement('button');close.setAttribute('aria-label','关闭查看器');
                        close.onclick=()=>{dialog.remove();main.removeAttribute('aria-hidden');};
                        dialog.append(download,close);document.body.append(dialog);
                    };
                }
                history.pushState({},'','/c/fixture-A');
            };
        }''', [self.url, self.second_url, refusal])

    @contextmanager
    def batch_page(self, endpoint):
        yield self.page

    def test_same_chat_batch_two_unique_downloads_one_connection(self):
        self.batch_fixture()
        with patch('conversation_batch.connected_image_page', side_effect=self.batch_page) as connect:
            result = run_batch(self.ledger, ['A','B'], 'http://127.0.0.1:9222', 10, confirmed=True)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(connect.call_count, 1)
        self.assertEqual(self.page.evaluate('window.sendCount'), 2)
        self.assertEqual(len(result['completed']), 2)
        a=self.ledger.task(self.ledger.load(),'A'); b=self.ledger.task(self.ledger.load(),'B')
        self.assertEqual(a['web']['page_url'], b['web']['page_url'])
        self.assertNotEqual(a['artifact']['sha256'], b['artifact']['sha256'])
        self.assertEqual(b['web']['previous_task_id'], 'A')
        self.assertEqual(len(b['web']['baseline_history']['prefix']), 1)
        self.assertTrue(self.ledger.check('B')['valid_output'])
        self.assertEqual(self.page.get_by_role('dialog').count(), 0)

    def test_batch_refusal_stops_and_leaves_third_pending(self):
        self.batch_fixture(refusal=True)
        self.ledger.add('C','prompts/b.txt',[],'outputs/C.png')
        with patch('conversation_batch.connected_image_page', side_effect=self.batch_page):
            with self.assertRaisesRegex(TaskError,'platform_refusal'):
                run_batch(self.ledger,['A','B','C'],'http://127.0.0.1:9222',10,confirmed=True)
        self.assertEqual(self.page.evaluate('window.sendCount'),2)
        self.assertEqual(self.ledger.task(self.ledger.load(),'C')['status'],'pending')
        self.assertTrue(self.ledger.task(self.ledger.load(),'B')['needs_confirmation'])
        self.assertFalse(Path(self.temporary.name,'outputs/B.png').exists())

    def test_batch_preflight_no_authority_duplicate_and_existing_output(self):
        self.batch_fixture()
        with patch('conversation_batch.connected_image_page') as connect:
            with self.assertRaises(TaskError): run_batch(self.ledger,['A','B'],'http://127.0.0.1:9222')
            with self.assertRaises(TaskError): run_batch(self.ledger,['A','A'],'http://127.0.0.1:9222',confirmed=True)
            Path(self.temporary.name,'outputs/B.png').write_bytes(b'keep')
            with self.assertRaises(TaskError): run_batch(self.ledger,['A','B'],'http://127.0.0.1:9222',confirmed=True)
            connect.assert_not_called()
        self.assertEqual(self.page.evaluate('window.sendCount'),0)

    def test_batch_does_not_download_old_gallery_while_new_turn_streams(self):
        self.batch_fixture()
        run(self.ledger,'A',self.page,'http://127.0.0.1:9222',10)
        close_preview(self.page)
        record_web(self.ledger,'A',conversation_history=history(self.page))
        prepare_submission(self.ledger,'B',self.page,'http://127.0.0.1:9222',previous_task_id='A')
        self.page.locator('main [data-talvt-turn-state]').nth(1).evaluate("el=>{el.dataset.talvtTurnState='streaming';el.querySelector('[data-testid=generated-image-gallery]').remove();}")
        self.assertIsNone(new_result(self.page,self.ledger.task(self.ledger.load(),'B')))
        self.assertFalse(Path(self.temporary.name,'outputs/B.png').exists())

    def test_batch_history_change_stops_before_second_send(self):
        self.batch_fixture()
        run(self.ledger,'A',self.page,'http://127.0.0.1:9222',10)
        close_preview(self.page)
        record_web(self.ledger,'A',conversation_history=history(self.page))
        self.page.locator('main h4').nth(0).evaluate("el=>el.nextElementSibling.textContent='changed prompt'")
        with self.assertRaisesRegex(TaskError,'Conversation changed'):
            run(self.ledger,'B',self.page,'http://127.0.0.1:9222',10,previous_task_id='A')
        self.assertEqual(self.page.evaluate('window.sendCount'),1)
        self.assertEqual(self.ledger.task(self.ledger.load(),'B')['status'],'pending')

    def test_batch_old_preview_and_extra_turn_refused(self):
        self.batch_fixture()
        run(self.ledger,'A',self.page,'http://127.0.0.1:9222',10)
        close_preview(self.page)
        record_web(self.ledger,'A',conversation_history=history(self.page))
        prepare_submission(self.ledger,'B',self.page,'http://127.0.0.1:9222',previous_task_id='A')
        result,image=new_result(self.page,self.ledger.task(self.ledger.load(),'B'))
        self.page.get_by_test_id('generated-image-preview').nth(0).click()
        with self.assertRaisesRegex(TaskError,'earlier image'):
            normal_download(self.page,result,image,self.temporary.name,allow_active_preview=False)
        close_preview(self.page)
        self.page.locator('main [data-talvt-turn-state]').nth(1).evaluate('el=>el.after(el.cloneNode(true))')
        with self.assertRaisesRegex(TaskError,'Extra conversation turns'):
            new_result(self.page,self.ledger.task(self.ledger.load(),'B'))

    def test_navigation_after_submit_preserves_original_recovery_url(self):
        def navigated(ledger, task_id, page, endpoint, timeout, **kwargs):
            page.evaluate("history.pushState({},'','/c/unrelated')")
            return new_result(page, ledger.task(ledger.load(), task_id))
        with patch('web_chatgpt.collect', side_effect=navigated):
            with self.assertRaisesRegex(TaskError,'Conversation changed'):
                run(self.ledger,'A',self.page,'http://127.0.0.1:9222',10)
        task = self.ledger.task(self.ledger.load(),'A')
        self.assertEqual(task['web']['page_url'],'https://chatgpt.com/c/fixture-A')
        self.assertEqual(self.page.evaluate('window.sendCount'),1)
        self.assertTrue(task['needs_confirmation'])

    def test_legacy_same_chat_batch_downloads_latest_response(self):
        Path(self.temporary.name,'prompts/b.txt').write_text('the cat stretches, one image',encoding='utf-8')
        self.ledger.add('B','prompts/b.txt',[],'outputs/B.png')
        output=io.BytesIO()
        Image.new('RGB',(512,288),'blue').save(output,format='PNG')
        second='data:image/png;base64,'+base64.b64encode(output.getvalue()).decode('ascii')
        self.page.evaluate('''second=>{
            const original=window.submitOnce;
            window.submitOnce=()=>{original();if(window.sendCount===2){
                const all=document.querySelectorAll('[data-message-author-role=assistant] img');
                all[all.length-1].src=second;
            }};
        }''',second)
        with patch('conversation_batch.connected_image_page',side_effect=self.batch_page):
            run_batch(self.ledger,['A','B'],'http://127.0.0.1:9222',10,confirmed=True)
        a=self.ledger.task(self.ledger.load(),'A');b=self.ledger.task(self.ledger.load(),'B')
        self.assertEqual(self.page.evaluate('window.sendCount'),2)
        self.assertEqual(b['web']['baseline_history']['style'],'legacy')
        self.assertNotEqual(a['artifact']['sha256'],b['artifact']['sha256'])

    def test_batch_second_download_recovery_does_not_resubmit(self):
        self.batch_fixture()
        calls=[]
        def interrupted(*args,**kwargs):
            calls.append(1)
            if len(calls)==2: raise TaskError('simulated second download interruption')
            return normal_download(*args,**kwargs)
        with patch('conversation_batch.connected_image_page',side_effect=self.batch_page), \
             patch('web_chatgpt.normal_download',side_effect=interrupted):
            with self.assertRaisesRegex(TaskError,'second download interruption'):
                run_batch(self.ledger,['A','B'],'http://127.0.0.1:9222',10,confirmed=True)
        first=Path(self.temporary.name,'outputs/A.png').read_bytes()
        recovered=collect(self.ledger,'B',self.page,'http://127.0.0.1:9222',10)
        self.assertEqual(recovered['status'],'completed')
        self.assertEqual(self.page.evaluate('window.sendCount'),2)
        self.assertEqual(Path(self.temporary.name,'outputs/A.png').read_bytes(),first)
        self.assertNotEqual(self.ledger.task(self.ledger.load(),'A')['artifact']['sha256'],recovered['artifact']['sha256'])

    def test_current_gallery_streaming_is_not_complete(self):
        self.modern_result('streaming')
        task = self.ledger.task(self.ledger.load(), 'A')
        self.assertIsNone(new_result(self.page, task))
        self.assertEqual(self.page.evaluate('window.sendCount'), 1)
        self.assertFalse(Path(self.temporary.name, 'outputs/A.png').exists())

    def test_completed_text_refusal_stops_without_resubmit(self):
        self.modern_result()
        self.page.locator('[data-talvt-turn-state]').evaluate("el => {el.replaceChildren(); el.textContent='抱歉，我不能生成这一角色的图片。'}")
        task = self.ledger.task(self.ledger.load(), 'A')
        with self.assertRaisesRegex(TaskError, 'platform_refusal'):
            new_result(self.page, task)
        self.assertEqual(self.page.evaluate('window.sendCount'), 1)
        self.assertFalse(Path(self.temporary.name, 'outputs/A.png').exists())

    def test_current_gallery_multiple_images_stop(self):
        self.modern_result()
        self.page.get_by_test_id('generated-image-preview').evaluate('el => el.after(el.cloneNode(true))')
        task = self.ledger.task(self.ledger.load(), 'A')
        with self.assertRaises(TaskError): new_result(self.page, task)
        self.assertEqual(self.page.evaluate('window.sendCount'), 1)

    def test_current_gallery_prompt_mismatch_stop(self):
        self.modern_result()
        self.page.locator('main h2').nth(0).evaluate("el => el.nextElementSibling.textContent='different request'")
        task = self.ledger.task(self.ledger.load(), 'A')
        with self.assertRaises(TaskError): new_result(self.page, task)
        self.assertEqual(self.page.evaluate('window.sendCount'), 1)

    def test_existing_current_conversation_cannot_start_new_job(self):
        self.modern_result()
        self.ledger.stop('A')
        self.ledger.resolve('A', True)
        self.ledger.add('B', 'prompts/a.txt', [], 'outputs/B.png')
        with self.assertRaises(TaskError):
            run(self.ledger, 'B', self.page, 'http://127.0.0.1:9222', timeout=10)
        self.assertEqual(self.page.evaluate('window.sendCount'), 1)
        self.assertEqual(self.ledger.task(self.ledger.load(), 'B')['status'], 'pending')

    def test_download_recovery_preserves_first_generation_timestamp(self):
        with patch('web_chatgpt.normal_download', side_effect=TaskError('simulated preview delay')):
            with self.assertRaises(TaskError):
                run(self.ledger, 'A', self.page, 'http://127.0.0.1:9222', timeout=10)
        first = self.ledger.task(self.ledger.load(), 'A')['web']['generation_complete_observed_at']
        recovered = collect(self.ledger, 'A', self.page, 'http://127.0.0.1:9222', timeout=10)
        timing = recovered['web']['timing']
        self.assertEqual(timing['generation_complete_observed_at'], first)
        self.assertGreater(timing['total_to_saved_seconds'], timing['generation_seconds'])
        self.assertGreaterEqual(timing['download_and_verify_seconds'], 0)
        self.assertEqual(self.page.evaluate('window.sendCount'), 1)
        self.assertTrue(self.ledger.check('A')['valid_output'])

    def test_no_overwrite_no_submit(self):
        Path(self.temporary.name, "outputs/A.png").write_bytes(b"existing")
        with self.assertRaises(TaskError):
            run(self.ledger, "A", self.page, "http://127.0.0.1:9222", timeout=10)
        self.assertEqual(self.page.evaluate("window.sendCount"), 0)

    def test_collect_timeout_never_sends_again(self):
        prepare_submission(self.ledger, "A", self.page, "http://127.0.0.1:9222")
        record_web(self.ledger, "A", page_url=self.page.url)
        self.page.locator('[data-message-author-role="assistant"] img').evaluate("el => el.remove()")
        with self.assertRaises(TaskError):
            collect(self.ledger, "A", self.page, "http://127.0.0.1:9222", timeout=1)
        self.assertEqual(self.page.evaluate("window.sendCount"), 1)
        self.assertFalse(Path(self.temporary.name, "outputs/A.png").exists())

    def test_multiple_images_need_confirmation(self):
        prepare_submission(self.ledger, "A", self.page, "http://127.0.0.1:9222")
        self.page.locator('[data-message-author-role="assistant"] img').evaluate("el => el.after(el.cloneNode())")
        self.page.wait_for_timeout(100)
        task = self.ledger.task(self.ledger.load(), "A")
        with self.assertRaises(TaskError): new_result(self.page, task)
        self.assertEqual(self.page.evaluate("window.sendCount"), 1)

    def test_missing_conversation_identity_refuses_collection(self):
        prepare_submission(self.ledger, "A", self.page, "http://127.0.0.1:9222")
        with self.assertRaises(TaskError):
            collect(self.ledger, "A", self.page, "http://127.0.0.1:9222", timeout=1)
        self.assertEqual(self.page.evaluate("window.sendCount"), 1)

    def test_only_explicit_reference_is_uploaded(self):
        path = Path(self.temporary.name, "references/person.png")
        output = io.BytesIO()
        Image.new("RGB", (512, 288), "blue").save(output, format="PNG")
        path.write_bytes(output.getvalue())
        Path(self.temporary.name, "prompts/ref.md").write_text("keep this person's identity", encoding="utf-8")
        self.ledger.add("REF", "prompts/ref.md", ["references/person.png"], "outputs/REF.png")
        task = run(self.ledger, "REF", self.page, "http://127.0.0.1:9222", timeout=10)
        uploaded = self.page.locator('input[type="file"]').evaluate("el => Array.from(el.files).map(f => f.name)")
        self.assertEqual(uploaded, ["reference-01.png"])
        self.assertEqual(task["status"], "completed")
        self.assertTrue(path.exists())

    def reference_fixture(self, *, reset_input=True, failed=False, count=1):
        from reference_upload import upload_references
        refs=[]
        for i in range(count):
            path=Path(self.temporary.name,f'references/cat-{i}.png')
            stream=io.BytesIO();Image.new('RGB',(512,288),'blue' if i==0 else 'green').save(stream,format='PNG')
            path.write_bytes(stream.getvalue());refs.append(f'references/cat-{i}.png')
        self.ledger.add('EDIT','prompts/a.txt',refs,'outputs/EDIT.png',operation='edit')
        self.page.evaluate('''([image,reset,failed])=>{
            const form=document.createElement('form');
            const composer=document.querySelector('#prompt-textarea');
            document.querySelector('[data-testid=send-button]').type='button';
            composer.before(form);form.append(composer,document.querySelector('input[type=file]'),document.querySelector('[data-testid=send-button]'));
            const correct=document.createElement('input');correct.type='file';correct.multiple=true;correct.id='actual-upload';form.append(correct);
            const decoy=document.createElement('input');decoy.type='file';decoy.accept='image/*';decoy.id='decoy';form.append(decoy);
            window.uploadedNames=[];
            correct.onchange=()=>{
                window.uploadedNames=Array.from(correct.files).map(f=>f.name);
                const send=document.querySelector('[data-testid=send-button]');send.disabled=true;
                const progress=document.createElement('div');progress.setAttribute('role','progressbar');form.append(progress);
                for(const file of correct.files){const img=document.createElement('img');img.src=image;img.alt=file.name;form.append(img);}
                if(reset)correct.value='';
                setTimeout(()=>{progress.remove();send.disabled=false;if(failed){const alert=document.createElement('div');alert.textContent='上传失败';form.append(alert);}},200);
            };
            const add=document.createElement('button');add.type='button';add.textContent='添加文件等内容';form.append(add);
            add.onclick=()=>{const upload=document.createElement('button');upload.type='button';upload.textContent='添加照片和文件 从计算机上传';
                upload.onclick=()=>{correct.click();upload.remove();};form.append(upload);};
        }''',[self.url,reset_input,failed])

    def test_edit_normal_file_chooser_with_reset_input_and_decoy_controls(self):
        self.reference_fixture()
        @contextmanager
        def prepared(endpoint): yield self.page
        with patch('web_chatgpt.connected_image_page',side_effect=prepared), \
             patch('sys.stdout',new_callable=io.StringIO),patch('sys.stderr',new_callable=io.StringIO):
            code=main(['--root',self.temporary.name,'--cdp','http://127.0.0.1:9222','edit','EDIT','--confirmed','--timeout','10'])
        self.assertEqual(code,0)
        task=self.ledger.task(self.ledger.load(),'EDIT')
        self.assertEqual(task['operation'],'edit')
        self.assertEqual(task['web']['reference_upload']['method'],'normal_file_chooser')
        self.assertEqual(task['web']['reference_upload']['evidence'],'decoded_draft_previews')
        self.assertEqual(self.page.evaluate('window.uploadedNames'),['reference-01.png'])
        self.assertEqual(self.page.locator('#decoy').evaluate('el=>el.files.length'),0)
        self.assertEqual(self.page.evaluate('window.sendCount'),1)
        self.assertTrue(self.ledger.check('EDIT')['valid_output'])

    def test_reference_upload_failure_never_sends(self):
        self.reference_fixture(failed=True)
        with self.assertRaisesRegex(TaskError,'upload failed'):
            run(self.ledger,'EDIT',self.page,'http://127.0.0.1:9222',10)
        self.assertEqual(self.page.evaluate('window.sendCount'),0)
        self.assertFalse(Path(self.temporary.name,'outputs/EDIT.png').exists())

    def test_two_named_references_use_only_the_normal_chooser(self):
        self.reference_fixture(count=2)
        task=run(self.ledger,'EDIT',self.page,'http://127.0.0.1:9222',10)
        self.assertEqual(self.page.evaluate('window.uploadedNames'),['reference-01.png','reference-02.png'])
        self.assertEqual(task['web']['reference_upload']['count'],2)
        self.assertEqual(self.page.evaluate('window.sendCount'),1)

    def test_edit_missing_reference_or_authority_never_connects(self):
        with patch('web_chatgpt.connected_image_page') as connect,patch('sys.stdout',new_callable=io.StringIO):
            self.assertEqual(main(['--root',self.temporary.name,'--cdp','http://127.0.0.1:9222','edit','A','--confirmed']),2)
            self.reference_fixture()
            self.assertEqual(main(['--root',self.temporary.name,'--cdp','http://127.0.0.1:9222','edit','EDIT']),2)
            self.assertEqual(main(['--root',self.temporary.name,'--cdp','http://127.0.0.1:9222','generate','EDIT','--confirmed']),2)
            connect.assert_not_called()

    def test_unapproved_staged_attachment_is_not_replaced(self):
        self.reference_fixture()
        self.page.locator('#decoy').set_input_files(str(Path(self.temporary.name,'references/cat-0.png')))
        with self.assertRaisesRegex(TaskError,'Existing selected attachments'):
            run(self.ledger,'EDIT',self.page,'http://127.0.0.1:9222',10)
        self.assertEqual(self.page.evaluate('window.sendCount'),0)
        self.assertEqual(self.page.evaluate('window.uploadedNames'),[])

    def test_paragraph_dom_preserves_internal_blank_lines_and_spaces(self):
        c=self.page.locator('#prompt-textarea')
        c.evaluate('''el=>el.innerHTML='<p>line A</p><p data-empty-paragraph="true"><br class="ProseMirror-trailingBreak"></p><p>line B</p><p><br class="ProseMirror-trailingBreak"></p>' ''')
        self.assertTrue(composer_matches(composer_text(c),'line A\n\nline B\n'))
        c.evaluate("el=>el.children[0].textContent='line A '")
        self.assertFalse(composer_matches(composer_text(c),'line A\n\nline B\n'))
        c.evaluate("el=>el.innerHTML='<p>a<br>b</p>'")
        self.assertEqual(composer_text(c),'a\nb')

    def interrupted_edit_draft(self):
        self.reference_fixture()
        with patch('web_chatgpt.send_prepared',side_effect=TaskError('simulated pre-Send interruption')):
            with self.assertRaisesRegex(TaskError,'pre-Send interruption'):
                run(self.ledger,'EDIT',self.page,'http://127.0.0.1:9222',10)
        self.assertEqual(self.page.evaluate('window.sendCount'),0)
        self.assertFalse(self.ledger.task(self.ledger.load(),'EDIT')['web'].get('submission_intent',False))

    def test_resume_unsubmitted_edit_keeps_upload_and_sends_once(self):
        self.interrupted_edit_draft()
        before=self.page.evaluate('window.uploadedNames')
        result=resume_draft(self.ledger,'EDIT',self.page,'http://127.0.0.1:9222',10)
        self.assertEqual(result['status'],'completed')
        self.assertEqual(self.page.evaluate('window.uploadedNames'),before)
        self.assertEqual(self.page.evaluate('window.sendCount'),1)
        self.assertEqual(sum(e['event']=='submission_recorded' for e in result['events']),1)

    def test_resume_draft_rejects_changed_prompt_or_reference_preview(self):
        self.interrupted_edit_draft()
        composer=self.page.locator('#prompt-textarea')
        composer.fill('different edit')
        with self.assertRaisesRegex(TaskError,'original prompt'):
            resume_draft(self.ledger,'EDIT',self.page,'http://127.0.0.1:9222',10)
        composer.fill('a cat, one image')
        self.page.locator('form img').evaluate("el=>el.alt='unknown.png'")
        with self.assertRaisesRegex(TaskError,'Retained references'):
            resume_draft(self.ledger,'EDIT',self.page,'http://127.0.0.1:9222',10)
        self.assertEqual(self.page.evaluate('window.sendCount'),0)

    def test_resume_draft_never_repeats_submitted_edit(self):
        self.reference_fixture()
        with patch('web_chatgpt.normal_download',side_effect=TaskError('interrupted download')):
            with self.assertRaises(TaskError):
                run(self.ledger,'EDIT',self.page,'http://127.0.0.1:9222',10)
        with self.assertRaisesRegex(TaskError,'proven unsubmitted'):
            resume_draft(self.ledger,'EDIT',self.page,'http://127.0.0.1:9222',10)
        self.assertEqual(self.page.evaluate('window.sendCount'),1)


if __name__ == "__main__":
    unittest.main()
