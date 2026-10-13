import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from PIL import Image
from framebridge import Ledger, TaskError, inspect_image, main
from web_chatgpt import checked_endpoint, checked_page, unique_visible, new_result, run, composer_matches


def png(color="white", size=(512, 288), fmt="PNG"):
    output = io.BytesIO()
    Image.new("RGB", size, color).save(output, format=fmt)
    return output.getvalue()


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ledger = Ledger(self.root)
        self.ledger.init()
        self.raw = b"\xef\xbb\xbf" + "保持参考人物身份。\r\n横向构图。\n".encode("utf-8")
        (self.root / "prompts/K01.md").write_bytes(self.raw)

    def add(self, task_id="K01", refs=()):
        return self.ledger.add(task_id, "prompts/K01.md", refs, f"outputs/{task_id}.png")

    def started(self, refs=()):
        task = self.add(refs=refs)
        self.ledger.start("K01", True)
        self.ledger.submitted("K01", True)
        return task

    def source(self, data=None, suffix=".png"):
        path = self.root / f"download{suffix}"
        path.write_bytes(data or png())
        return path

    def test_prompt_bytes_and_text_frozen(self):
        task = self.add()
        (self.root / "prompts/K01.md").write_text("changed", encoding="utf-8")
        packet = self.ledger.packet("K01")
        self.assertEqual((self.root / task["prompt_snapshot"]).read_bytes(), self.raw)
        self.assertEqual(packet["prompt_text"], self.raw.decode("utf-8-sig"))

    def test_edit_requires_reference_and_freezes_intent(self):
        with self.assertRaises(TaskError):
            self.ledger.add('EDIT','prompts/K01.md',[],'outputs/EDIT.png',operation='edit')
        self.assertFalse((self.root/'logs/EDIT').exists())
        (self.root/'references/cat.png').write_bytes(png('blue'))
        task=self.ledger.add('EDIT','prompts/K01.md',['references/cat.png'],'outputs/EDIT.png',operation='edit')
        self.assertEqual(self.ledger.packet('EDIT')['operation'],'edit')
        (self.root/'references/cat.png').write_bytes(png('green'))
        self.ledger.verify_inputs(task)
        self.assertEqual((self.root/task['references'][0]['snapshot_path']).read_bytes(),png('blue'))

    def test_legacy_tasks_without_operation_still_load(self):
        self.add()
        state=self.ledger.load()
        state['tasks'][0].pop('operation')
        self.ledger.save(state)
        self.assertEqual(self.ledger.packet('K01')['operation'],'generate')

    def test_confirmation_and_serial_queue(self):
        self.add()
        self.add("K02")
        with self.assertRaises(TaskError): self.ledger.start("K01")
        self.ledger.start("K01", True)
        with self.assertRaises(TaskError): self.ledger.start("K02", True)
        with self.assertRaises(TaskError): self.ledger.start("K01", True)
        self.ledger.stop("K01")
        with self.assertRaises(TaskError): self.ledger.start("K02", True)
        self.ledger.resolve("K01", True)
        self.ledger.start("K02", True)

    def test_reference_snapshot_and_identical_output_rejected(self):
        ref = self.root / "references/person.webp"
        data = png(fmt="WEBP")
        ref.write_bytes(data)
        self.started(["references/person.webp"])
        with self.assertRaises(TaskError):
            self.ledger.import_image("K01", self.source(data, ".webp"), True, True)
        ref.write_bytes(png("blue", fmt="WEBP"))
        self.ledger.verify_inputs(self.ledger.task(self.ledger.load(), "K01"))

    def test_valid_import_and_integrity(self):
        self.started()
        source = self.source()
        with self.assertRaises(TaskError): self.ledger.import_image("K01", source)
        task = self.ledger.import_image("K01", source, True)
        self.assertEqual(task["status"], "completed")
        self.assertTrue(source.exists())
        self.assertTrue(self.ledger.check("K01")["valid_output"])
        self.assertEqual(json.loads((self.root / task["log_path"]).read_text(encoding="utf-8"))["status"], "completed")
        (self.root / task["output_path"]).write_bytes(png("blue"))
        with self.assertRaises(TaskError): self.ledger.check("K01")

    def test_never_overwrites(self):
        self.started()
        target = self.root / "outputs/K01.png"
        target.write_bytes(b"existing")
        with self.assertRaises(TaskError): self.ledger.import_image("K01", self.source(), True)
        self.assertEqual(target.read_bytes(), b"existing")

    def test_stale_download_and_corrupt_images(self):
        self.started()
        source = self.source()
        os.utime(source, (1, 1))
        with self.assertRaises(TaskError): self.ledger.import_image("K01", source, True)
        with self.assertRaises(TaskError): inspect_image(png()[:100], ".png", output=True)
        with self.assertRaises(TaskError): inspect_image(b"<html>error</html>", ".png", output=True)
        with self.assertRaises(TaskError): inspect_image(png(size=(64, 64)), ".png", output=True)
        with self.assertRaises(TaskError): inspect_image(png(fmt="JPEG"), ".png", output=True)

    def test_explicit_format_conversion(self):
        self.started()
        source = self.source(png(fmt="JPEG"), ".jpg")
        with self.assertRaises(TaskError): self.ledger.import_image("K01", source, True)
        self.ledger.import_image("K01", source, True, True)
        self.assertEqual(self.ledger.check("K01")["format"], "PNG")
        self.assertTrue(source.exists())

    def test_recover_does_not_resubmit(self):
        self.started()
        self.ledger.recover()
        task = self.ledger.task(self.ledger.load(), "K01")
        self.assertEqual(task["status"], "failed")
        self.assertTrue(task["needs_confirmation"])
        with self.assertRaises(TaskError): self.ledger.start("K01", True)
        self.ledger.import_image("K01", self.source(), True)
        self.assertTrue(self.ledger.check("K01")["valid_output"])

    def test_crash_after_write_can_confirm_without_overwrite(self):
        self.started()
        original_save = self.ledger.save
        def fail_final(state):
            if state["tasks"][0]["status"] == "completed":
                raise OSError("simulated disk failure")
            return original_save(state)
        with patch.object(self.ledger, "save", side_effect=fail_final):
            with self.assertRaises(OSError): self.ledger.import_image("K01", self.source(), True)
        self.ledger.recover()
        self.ledger.import_image("K01", confirmed=True, existing=True)
        self.assertTrue(self.ledger.check("K01")["valid_output"])

    def test_paths_output_reservation_and_bad_ids(self):
        for bad in ("../escape", "CON", "k/1"):
            with self.assertRaises(TaskError): self.add(bad)
        with self.assertRaises(TaskError): self.ledger.add("K01", "../outside.md", [], "outputs/K01.png")
        with self.assertRaises(TaskError): self.ledger.add("K01", "prompts/K01.md", [], "../outside.png")
        self.add()
        with self.assertRaises(TaskError): self.add("k01")
        with self.assertRaises(TaskError): self.ledger.add("K02", "prompts/K01.md", [], "outputs/k01.png")

    def test_snapshot_tamper_and_ledger_corruption_stop(self):
        task = self.add()
        (self.root / task["prompt_snapshot"]).write_bytes(b"tampered")
        with self.assertRaises(TaskError): self.ledger.start("K01", True)
        (self.root / "tasks.json").write_bytes(b"broken")
        with self.assertRaises(TaskError): self.ledger.load()
        self.assertEqual((self.root / "tasks.json").read_bytes(), b"broken")

    def test_ledger_log_path_cannot_escape(self):
        self.add()
        state = self.ledger.load()
        state["tasks"][0]["log_path"] = "../outside.json"
        (self.root / "tasks.json").write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaises(TaskError): self.ledger.load()

    def test_process_lock_prevents_second_writer(self):
        with self.ledger.lock():
            with self.assertRaises(TaskError):
                Ledger(self.root).add("K01", "prompts/K01.md", [], "outputs/K01.png")

    def test_duplicate_output_file_not_reused(self):
        self.started()
        source = self.source()
        self.ledger.import_image("K01", source, True)
        self.add("K02")
        self.ledger.start("K02", True)
        source.write_bytes(png())
        with self.assertRaises(TaskError): self.ledger.import_image("K02", source, True)

    def test_cli_round_trip(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(main(["--root", str(self.root), "add", "K01", "--prompt", "prompts/K01.md", "--output", "outputs/K01.png"]), 0)
            self.assertEqual(main(["--root", str(self.root), "packet", "K01"]), 0)
        with patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(main(["--root", str(self.root), "start", "K01"]), 2)


class BrowserBoundaryTests(unittest.TestCase):
    def test_composer_rendering_keeps_meaningful_whitespace(self):
        self.assertTrue(composer_matches('line1\nline2\n\n\n', 'line1\r\nline2\n'))
        self.assertFalse(composer_matches('line1 line2', 'line1\nline2'))
        self.assertFalse(composer_matches('different\n', 'original\n'))
        self.assertFalse(composer_matches(' original\n', 'original\n'))

    def test_cdp_and_page_allowlist(self):
        self.assertEqual(checked_endpoint("http://127.0.0.1:9222/"), "http://127.0.0.1:9222")
        for value in ("https://evil.example:9222", "http://127.0.0.1:9222/?token=secret", "http://user:pass@localhost:9222", "http://localhost"):
            with self.assertRaises(TaskError): checked_endpoint(value)
        self.assertEqual(checked_page("https://chatgpt.com/c/test-id"), "https://chatgpt.com/c/test-id")
        for value in ("https://chatgpt.com.evil.example/", "https://chatgpt.com/?token=secret", "https://chatgpt.com/backend-api/conversation"):
            with self.assertRaises(TaskError): checked_page(value)

    def test_ambiguous_controls_stop(self):
        class Locator:
            def count(self): return 2
            def nth(self, index): return self
            def is_visible(self): return True
        with self.assertRaises(TaskError): unique_visible(Locator(), "send")

    def test_failed_submit_is_not_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Ledger(directory)
            ledger.init()
            Path(directory, "prompts/a.txt").write_text("one image", encoding="utf-8")
            ledger.add("A", "prompts/a.txt", [], "outputs/a.png")
            def failing(*args):
                ledger.start("A", True)
                ledger.submitted("A", True)
                raise TaskError("simulated click uncertainty")
            with patch("web_chatgpt.prepare_submission", side_effect=failing) as submit:
                with self.assertRaises(TaskError): run(ledger, "A", object(), "http://127.0.0.1:9222")
                self.assertEqual(submit.call_count, 1)
            task = ledger.task(ledger.load(), "A")
            self.assertTrue(task["needs_confirmation"])
            self.assertEqual(task["status"], "failed")


if __name__ == "__main__":
    unittest.main()
