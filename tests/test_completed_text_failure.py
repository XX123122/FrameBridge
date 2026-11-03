"""No network or real generation: recognize the completed failure sentences."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from web_chatgpt import completed_text_failure


class CompletedFailureTests(unittest.TestCase):
    def test_observed_chinese_and_english_tool_errors(self):
        for text in ('图像生成工具再次返回错误，未能生成画面。',
                     'I couldn’t generate the new image because the image tool returned an error.',
                     'The image generation tool failed. No image was created.'):
            self.assertEqual(completed_text_failure(text),'image_service_error')

    def test_reference_request_is_not_a_claim_that_reference_was_supplied(self):
        self.assertEqual(completed_text_failure('请上传需要作为参考的原始画面，我就可以据此生成新的画面。'),'reference_requested')

    def test_user_prompt_does_not_trigger_assistant_failure(self):
        text='你说：\nDo not say the image tool returned an error.\nChatGPT 说：\nCreating your image now.'
        self.assertIsNone(completed_text_failure(text))

    def test_normal_success_and_refusal_remain_distinct(self):
        self.assertIsNone(completed_text_failure('Here is the generated image. No upload is needed.'))
        self.assertEqual(completed_text_failure('抱歉，我不能生成这一角色的图片。'),'platform_refusal')


if __name__=='__main__':unittest.main()
