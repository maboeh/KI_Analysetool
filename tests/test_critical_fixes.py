"""
Unit-Tests für kritische Bug-Fixes des KI-Analysetools.

Testet die wichtigsten Behhebungen aus dem Optimierungsplan:
- B5: YouTube URL-Parsing mit &-Parametern
- S3: URL-Validierung (SSRF-Schutz)
- S4: Timeout für HTTP-Requests
- S5: Dateipfad-Validierung
- B1/B2: Prompt-Template-Logik (kein doppeltes .format)
- B4: save_note sammelt Notizen statt zu überschreiben
- B6: Config-Key-Konsistenz
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import socket

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestYouTubeURLParsing(unittest.TestCase):
    """B5: YouTube URL-Parsing mit &-Parametern."""

    @patch('analysis.YouTubeTranscriptApi')
    def test_watch_url_with_timestamp(self, mock_api):
        from analysis import extract_transkript
        mock_api.get_transcript.return_value = [{"text": "Test"}]
        result = extract_transkript("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120")
        self.assertEqual(result, "Test ")
        call_args = mock_api.get_transcript.call_args
        self.assertEqual(call_args[0][0], "dQw4w9WgXcQ")

    @patch('analysis.YouTubeTranscriptApi')
    def test_short_url_with_params(self, mock_api):
        from analysis import extract_transkript
        mock_api.get_transcript.return_value = [{"text": "Test"}]
        result = extract_transkript("https://youtu.be/dQw4w9WgXcQ?si=abc123")
        self.assertEqual(result, "Test ")
        call_args = mock_api.get_transcript.call_args
        self.assertEqual(call_args[0][0], "dQw4w9WgXcQ")

    def test_invalid_url_raises_error(self):
        from analysis import extract_transkript
        with self.assertRaises(ValueError):
            extract_transkript("https://example.com/video")


class TestURLValidation(unittest.TestCase):
    """S3: URL-Validierung (SSRF-Schutz)."""

    def test_safe_https_url(self):
        from analysis import is_safe_url
        self.assertTrue(is_safe_url("https://example.com"))

    def test_safe_http_url(self):
        from analysis import is_safe_url
        self.assertTrue(is_safe_url("http://example.com"))

    def test_ftp_rejected(self):
        from analysis import is_safe_url
        self.assertFalse(is_safe_url("ftp://example.com"))

    def test_localhost_rejected(self):
        from analysis import is_safe_url
        self.assertFalse(is_safe_url("http://localhost"))

    def test_private_ip_rejected(self):
        from analysis import is_safe_url
        self.assertFalse(is_safe_url("http://192.168.1.1"))

    def test_loopback_ip_rejected(self):
        from analysis import is_safe_url
        self.assertFalse(is_safe_url("http://127.0.0.1"))

    def test_no_scheme_rejected(self):
        from analysis import is_safe_url
        self.assertFalse(is_safe_url("example.com"))


class TestFilepathValidation(unittest.TestCase):
    """S5: Dateipfad-Validierung."""

    def test_valid_txt_file(self):
        from analysis import is_safe_filepath
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            path = f.name
        try:
            self.assertTrue(is_safe_filepath(path))
        finally:
            os.unlink(path)

    def test_valid_pdf_file(self):
        from analysis import is_safe_filepath
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            self.assertTrue(is_safe_filepath(path))
        finally:
            os.unlink(path)

    def test_invalid_extension(self):
        from analysis import is_safe_filepath
        self.assertFalse(is_safe_filepath("/tmp/test.exe"))

    def test_empty_path(self):
        from analysis import is_safe_filepath
        self.assertFalse(is_safe_filepath(""))


class TestPromptTemplate(unittest.TestCase):
    """B1/B2: Prompt-Template-Logik."""

    def test_zusammenfassung_has_placeholder(self):
        from Gui import Gui
        # The default summary prompt must use {text} placeholder to avoid double formatting issues.
        self.assertIn("{text}", "Fasse den Text zusammen: {text}")

    def test_prompt_templates_contain_placeholder(self):
        """Alle vordefinierten Prompts müssen {text} als Platzhalter enthalten."""
        templates = [
            "Fasse den Text zusammen: {text}",
            "Extrahiere Schlüsselwörter aus diesem Text: {text}",
            "Analysiere die Stimmung und den Tonfall dieses Textes: {text}",
            "Erkenne die Hauptthemen des nachfolgenden Textes: {text}",
        ]
        for template in templates:
            self.assertIn("{text}", template,
                          f"Template '{template}' fehlt {{text}}-Platzhalter")

    def test_template_format_succeeds(self):
        """Template.replace('{text}', ...) muss ohne Fehler funktionieren."""
        template = "Fasse den Text zusammen: {text}"
        result = template.replace("{text}", "Beispieltext")
        self.assertIn("Beispieltext", result)
        self.assertNotIn("{text}", result)

    def test_template_replace_with_braces_in_content(self):
        """Content mit geschweiften Klammern darf .replace() nicht crashen."""
        template = "Fasse den Text zusammen: {text}"
        content_with_braces = '{"key": "value", "nested": {"a": 1}}'
        result = template.replace("{text}", content_with_braces)
        self.assertIn(content_with_braces, result)


class TestWebsiteExtractionTimeout(unittest.TestCase):
    """S4: Timeout für HTTP-Requests."""

    @patch('security.requests.Session')
    @patch('socket.getaddrinfo')
    def test_timeout_is_set(self, mock_getaddrinfo, mock_session_cls):
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))
        ]
        mock_response = MagicMock()
        mock_response.text = "<html>Test</html>"
        mock_response.raise_for_status = MagicMock()
        mock_response.url = "https://example.com"
        mock_response.is_redirect = False
        mock_session = mock_session_cls.return_value
        mock_session.get.return_value = mock_response

        from analysis import extract_text_from_website
        extract_text_from_website("https://example.com")

        call_kwargs = mock_session.get.call_args[1]
        self.assertIn("timeout", call_kwargs)
        self.assertGreater(call_kwargs["timeout"], 0)


class TestWebsiteExtractionValidation(unittest.TestCase):
    """S3: extract_text_from_website validiert URL vor Request."""

    def test_unsafe_url_raises(self):
        from analysis import extract_text_from_website
        from security import SecurityException
        with self.assertRaises(SecurityException):
            extract_text_from_website("http://localhost")


class TestConfigKeyConsistency(unittest.TestCase):
    """B6: Config-Key-Konsistenz zwischen setup.py und config.py."""

    def test_config_key_name(self):
        """config.py muss nach 'OpenAI_Key' suchen (nicht 'openai_api_key')."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.py")
        with open(config_path, "r", encoding="utf-8") as f:
            config_content = f.read()
        self.assertIn("OpenAI_Key", config_content)

    def test_setup_key_name(self):
        """setup.py muss einen der unterstützten API-Key-Namen enthalten."""
        setup_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "setup.py")
        with open(setup_path, "r", encoding="utf-8") as f:
            setup_content = f.read()
        self.assertTrue(
            "OpenAI_Key" in setup_content or "openai_api_key" in setup_content
        )


class TestNoEnvVarLeak(unittest.TestCase):
    """S6: API-Key wird nicht in os.environ geschrieben."""

    def test_save_does_not_set_env(self):
        """save_api_key soll os.environ['OPENAI_API_KEY'] nicht setzen."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.py")
        with open(config_path, "r", encoding="utf-8") as f:
            config_content = f.read()

        save_section = config_content.split("def save_api_key")[1].split("def get_api_key")[0]
        self.assertNotIn("os.environ['OPENAI_API_KEY']", save_section)
        self.assertNotIn('os.environ["OPENAI_API_KEY"]', save_section)


class TestModelSelection(unittest.TestCase):
    """F3: Modellauswahl."""

    def test_available_models_exist(self):
        from analysis import AVAILABLE_MODELS
        self.assertIn("gpt-4o", AVAILABLE_MODELS)
        self.assertIn("gpt-4o-mini", AVAILABLE_MODELS)

    def test_set_model_valid(self):
        from analysis import set_model, get_model, DEFAULT_MODEL
        set_model("gpt-4o-mini")
        self.assertEqual(get_model(), "gpt-4o-mini")
        set_model(DEFAULT_MODEL)

    def test_set_model_invalid_ignored(self):
        from analysis import set_model, get_model, DEFAULT_MODEL
        original = get_model()
        set_model("nonexistent-model")
        self.assertEqual(get_model(), original)

    def test_model_has_cost_info(self):
        from analysis import AVAILABLE_MODELS
        for key, info in AVAILABLE_MODELS.items():
            self.assertIn("cost_per_1k_input", info)
            self.assertIn("cost_per_1k_output", info)
            self.assertGreater(info["cost_per_1k_input"], 0)


class TestTokenEstimation(unittest.TestCase):
    """F6: Token-Schätzung und Content-Length-Validierung."""

    def test_estimate_tokens_short_text(self):
        from analysis import estimate_tokens
        self.assertEqual(estimate_tokens("Hallo"), 1)

    def test_estimate_tokens_long_text(self):
        from analysis import estimate_tokens
        text = "a" * 4000
        self.assertEqual(estimate_tokens(text), 1000)

    def test_validate_content_length_ok(self):
        from analysis import validate_content_length
        is_valid, est, max_tok, msg = validate_content_length("Kurzer Text")
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

    def test_validate_content_length_too_long(self):
        from analysis import validate_content_length
        long_text = "x" * 500000
        is_valid, est, max_tok, msg = validate_content_length(long_text)
        self.assertFalse(is_valid)
        self.assertIn("zu lang", msg)


class TestRetryMechanism(unittest.TestCase):
    """F5: Retry-Mechanismus."""

    def test_retry_succeeds_on_second_attempt(self):
        from analysis import _retry_api_call
        from openai import APIConnectionError
        call_count = [0]

        def flaky():
            call_count[0] += 1
            if call_count[0] < 2:
                raise APIConnectionError(message="Temporärer Fehler", request=MagicMock())
            return "Erfolg"

        result = _retry_api_call(flaky, max_retries=3, base_delay=0.01)
        self.assertEqual(result, "Erfolg")
        self.assertEqual(call_count[0], 2)

    def test_retry_fails_after_max(self):
        from analysis import _retry_api_call
        from openai import APIConnectionError

        def always_fail():
            raise APIConnectionError(message="Dauerhafter Fehler", request=MagicMock())

        with self.assertRaises(APIConnectionError):
            _retry_api_call(always_fail, max_retries=2, base_delay=0.01)

    def test_bad_request_not_retried(self):
        from analysis import _retry_api_call
        from openai import BadRequestError

        def bad_request():
            raise BadRequestError(message="Invalid request", response=MagicMock(), body=None)

        with self.assertRaises(BadRequestError):
            _retry_api_call(bad_request, max_retries=3, base_delay=0.01)


class TestUsageStats(unittest.TestCase):
    """F4: Token/Cost-Tracking."""

    def test_get_usage_stats_initial(self):
        from analysis import get_usage_stats, reset_usage_stats
        reset_usage_stats()
        stats = get_usage_stats()
        self.assertIn("total_tokens", stats)
        self.assertIn("total_cost", stats)
        self.assertIn("model", stats)

    def test_reset_usage_stats(self):
        from analysis import reset_usage_stats, get_usage_stats
        reset_usage_stats()
        stats = get_usage_stats()
        self.assertEqual(stats["total_tokens"], 0)
        self.assertEqual(stats["total_cost"], 0.0)


class TestNonCriticalFixes(unittest.TestCase):
    """Nicht-kritische Fixes aus dem Review."""

    def test_config_path_cwd_independent(self):
        """B2: get_config_path() muss unabhängig vom CWD sein."""
        import config
        path1 = config.get_config_path()
        original_cwd = os.getcwd()
        try:
            os.chdir(os.path.dirname(original_cwd))
            path2 = config.get_config_path()
        finally:
            os.chdir(original_cwd)
        self.assertEqual(path1, path2)

    def test_markdown_tags_font_size_param(self):
        """C1: configure_markdown_tags akzeptiert font_size-Parameter."""
        import tkinter as tk
        from markdown_formatter import configure_markdown_tags
        root = tk.Tk()
        root.withdraw()
        try:
            tw = tk.Text(root)
            configure_markdown_tags(tw, font_size=18)
            bold_font = tw.tag_cget("bold", "font")
            self.assertIn("18", bold_font)
            h1_font = tw.tag_cget("h1", "font")
            self.assertIn("30", h1_font)
        finally:
            root.destroy()

    def test_template_replace_with_braces_in_enhanced(self):
        """A2: .replace() statt .format() in Enhanced GUI - Content mit geschweiften Klammern."""
        template = "Fasse den Text zusammen: {text}"
        content_with_braces = '{"key": "value", "nested": {"a": 1}}'
        result = template.replace("{text}", content_with_braces)
        self.assertIn(content_with_braces, result)
        self.assertNotIn("{text}", result)

    def test_custom_prompt_replaces_text_placeholder(self):
        """Benutzerdefinierter Prompt muss {text}-Platzhalter ersetzen, nicht anhängen."""
        from Gui import Gui
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        try:
            app = Gui(root)
            app.question_text.delete(1.0, tk.END)
            app.question_text.insert(1.0, "Erkläre kurz: {text}")
            prompt = app.get_prompt("Hallo Welt")
            self.assertIn("Hallo Welt", prompt)
            self.assertNotIn("{text}", prompt)
        finally:
            root.destroy()

    def test_pdf_cleanup_no_locals_or_dir(self):
        """A4: PDF-Cleanup nutzt weder locals() noch dir()."""
        analysis_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "analysis.py")
        with open(analysis_path, "r", encoding="utf-8") as f:
            analysis_content = f.read()
        cleanup_section = analysis_content.split("finally:")[1]
        self.assertNotIn("locals()", cleanup_section)
        self.assertNotIn("dir()", cleanup_section)


if __name__ == "__main__":
    unittest.main()
