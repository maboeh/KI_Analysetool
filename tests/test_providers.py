import io
import json
import unittest
from unittest import mock

import analysis
from providers import (
    PROVIDERS, detect_models, get_provider, build_client,
    looks_like_cloud_model,
)


class TestProviderRegistry(unittest.TestCase):

    def test_openai_is_external(self):
        provider = get_provider("openai")
        self.assertFalse(provider.is_local)
        self.assertTrue(provider.external_transfer)
        self.assertTrue(provider.requires_api_key)

    def test_ollama_is_local(self):
        provider = get_provider("ollama")
        self.assertTrue(provider.is_local)
        self.assertFalse(provider.external_transfer)
        self.assertFalse(provider.requires_api_key)
        self.assertEqual(provider.base_url, "http://localhost:11434/v1")

    def test_custom_requires_base_url(self):
        self.assertIsNone(get_provider("custom"))
        provider = get_provider("custom", "http://localhost:1234/v1")
        self.assertTrue(provider.is_local)

    def test_custom_remote_url_is_external(self):
        provider = get_provider("custom", "https://llm.example.com/v1")
        self.assertFalse(provider.is_local)
        self.assertTrue(provider.external_transfer)

    def test_unknown_provider(self):
        self.assertIsNone(get_provider("does-not-exist"))


class TestDetectModels(unittest.TestCase):

    def _mock_response(self, payload):
        response = mock.MagicMock()
        response.read.return_value = json.dumps(payload).encode("utf-8")
        response.__enter__ = lambda s: s
        response.__exit__ = mock.MagicMock(return_value=False)
        return response

    def test_parses_openai_models_payload(self):
        provider = get_provider("ollama")
        payload = {"data": [{"id": "llama3:latest"}, {"id": "mistral"}]}
        with mock.patch("providers.urlopen",
                        return_value=self._mock_response(payload)):
            models = detect_models(provider)
        self.assertEqual(models, ["llama3:latest", "mistral"])

    def test_unreachable_returns_empty(self):
        provider = get_provider("ollama")
        with mock.patch("providers.urlopen", side_effect=OSError("down")):
            self.assertEqual(detect_models(provider), [])

    def test_provider_without_base_url(self):
        self.assertEqual(detect_models(get_provider("openai")), [])


class TestBuildClient(unittest.TestCase):

    def test_openai_requires_key(self):
        with self.assertRaises(ValueError):
            build_client(get_provider("openai"), api_key=None)

    def test_local_needs_no_real_key(self):
        with mock.patch("openai.OpenAI") as mock_openai:
            build_client(get_provider("ollama"))
            _args, kwargs = mock_openai.call_args
            self.assertEqual(kwargs["base_url"], "http://localhost:11434/v1")
            self.assertTrue(kwargs["api_key"])

    def test_custom_without_url_fails(self):
        provider = get_provider("custom", "http://localhost:1/v1")
        broken = type(provider)(id="custom", name="x", base_url=None,
                                requires_api_key=False)
        with self.assertRaises(ValueError):
            build_client(broken)


class TestSessionProvider(unittest.TestCase):

    def setUp(self):
        self.session = analysis.AnalysisSession()

    def test_default_provider_is_openai(self):
        self.assertEqual(self.session.current_provider.id, "openai")
        self.assertFalse(self.session.is_local_provider)

    def test_set_ollama(self):
        self.session.set_provider("ollama")
        self.assertTrue(self.session.is_local_provider)

    def test_custom_requires_url(self):
        self.session.set_provider("custom")
        self.assertEqual(self.session.current_provider.id, "openai")
        self.session.set_provider("custom", "http://localhost:1234/v1")
        self.assertEqual(self.session.current_provider.id, "custom")
        self.assertTrue(self.session.is_local_provider)

    def test_unknown_provider_rejected(self):
        self.session.set_provider("bogus")
        self.assertEqual(self.session.current_provider.id, "openai")

    def test_local_model_allowed(self):
        self.session.set_provider("ollama")
        self.session.set_model("llama3:latest", allow_unknown=True)
        self.assertEqual(self.session.get_model(), "llama3:latest")

    def test_unknown_model_rejected_without_flag(self):
        self.session.set_model("llama3:latest")
        self.assertEqual(self.session.get_model(), analysis.DEFAULT_MODEL)

    def test_local_usage_is_free(self):
        self.session.set_provider("ollama")
        self.session.set_model("llama3:latest", allow_unknown=True)
        self.session.record_usage(1000, 500)
        stats = self.session.get_usage_stats()
        self.assertEqual(stats["total_tokens"], 1500)
        self.assertEqual(stats["total_cost"], 0.0)


class TestAnalyzeLocalProvider(unittest.TestCase):

    def tearDown(self):
        analysis.set_provider("openai")
        analysis.set_model(analysis.DEFAULT_MODEL)

    def test_local_provider_needs_no_api_key(self):
        analysis.set_provider("ollama")
        analysis.set_model("llama3:latest", allow_unknown=True)

        response = mock.MagicMock()
        response.choices = [mock.MagicMock(
            message=mock.MagicMock(content="Antwort"))]
        response.usage = mock.MagicMock(prompt_tokens=10, completion_tokens=5)

        client = mock.MagicMock()
        client.chat.completions.create.return_value = response

        with mock.patch("analysis.get_api_key", return_value=None), \
             mock.patch("providers.build_client", return_value=client):
            outcome = analysis.analyze_text("Teste den Inhalt bitte.")

        self.assertTrue(outcome.success)
        self.assertEqual(outcome.content, "Antwort")
        client.chat.completions.create.assert_called_once()
        self.assertEqual(
            client.chat.completions.create.call_args.kwargs["model"],
            "llama3:latest")

    def test_estimate_cost_zero_for_local_model(self):
        analysis.set_provider("ollama")
        estimate = analysis.estimate_request_cost("x" * 400, model="llama3")
        self.assertEqual(estimate["estimated_cost"], 0.0)

    def test_estimate_cost_falls_back_for_unknown_external_model(self):
        analysis.set_provider("openai")
        estimate = analysis.estimate_request_cost("x" * 400, model="llama3")
        self.assertGreater(estimate["estimated_cost"], 0.0)

    def test_validate_length_uses_default_for_unknown_model(self):
        is_valid, _est, max_tokens, _msg = analysis.validate_content_length(
            "kurz", model="llama3")
        self.assertTrue(is_valid)
        self.assertEqual(max_tokens, 32768)

    def test_pdf_analysis_rejected_for_local_provider(self):
        """PDF-Direktanalyse darf bei lokalem Provider nicht still zu OpenAI gehen."""
        import tempfile, os
        analysis.set_provider("ollama")
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 test")
            path = f.name
        try:
            with mock.patch("analysis.get_api_key", return_value="secret"), \
                 mock.patch("providers.build_client") as mock_build:
                outcome = analysis.analyze_pdf(path, "Analysiere")
            self.assertFalse(outcome.success)
            self.assertEqual(outcome.error.code,
                             analysis.AnalysisErrorCode.UNSUPPORTED_FORMAT)
            mock_build.assert_not_called()
        finally:
            os.unlink(path)


class TestCloudModelHeuristic(unittest.TestCase):

    def test_openai_models_look_like_cloud(self):
        for name in ("gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "o1-preview",
                     "o3-mini", "chatgpt-4o-latest", "text-embedding-3-small",
                     "whisper-1", "dall-e-3"):
            self.assertTrue(looks_like_cloud_model(name), name)

    def test_local_models_do_not(self):
        for name in ("llama3:latest", "mistral", "qwen2.5:7b",
                     "phi-4", "gemma2:9b"):
            self.assertFalse(looks_like_cloud_model(name), name)

    def test_empty_and_none(self):
        self.assertFalse(looks_like_cloud_model(None))
        self.assertFalse(looks_like_cloud_model(""))
        self.assertFalse(looks_like_cloud_model("   "))


class TestTransferConfirmationLocal(unittest.TestCase):

    def tearDown(self):
        analysis.set_provider("openai")

    def test_local_provider_disables_external_notice(self):
        from transfer_confirmation import evaluate_transfer
        analysis.set_provider("ollama")
        analysis.set_model("llama3:latest", allow_unknown=True)
        try:
            context = evaluate_transfer("Harmloser Text", source_type="pdf",
                                        privacy_check=False)
        finally:
            analysis.set_model(analysis.DEFAULT_MODEL)
        self.assertFalse(context.external)
        self.assertIn("lokal", context.notice.lower())
        # PDF-Quelle löst bei lokalem Provider keinen Pflichtdialog aus.
        self.assertFalse(context.needs_confirmation)

    def test_openai_provider_keeps_external_notice(self):
        from transfer_confirmation import evaluate_transfer
        analysis.set_provider("openai")
        context = evaluate_transfer("Harmloser Text", source_type="pdf",
                                    privacy_check=False)
        self.assertTrue(context.external)
        self.assertIn("OpenAI", context.notice)
        self.assertTrue(context.needs_confirmation)

    def test_cloud_model_on_local_provider_warns(self):
        """Cloud-Modellname auf lokalem Provider löst eine Warnung aus."""
        from transfer_confirmation import evaluate_transfer
        analysis.set_provider("ollama")
        analysis.set_model("gpt-4o", allow_unknown=True)
        try:
            context = evaluate_transfer("Harmloser Text", source_type="file",
                                        privacy_check=False)
        finally:
            analysis.set_model(analysis.DEFAULT_MODEL)
        self.assertFalse(context.external)
        self.assertIsNotNone(context.model_warning)
        self.assertIn("gpt-4o", context.model_warning)
        self.assertTrue(context.needs_confirmation)

    def test_local_model_on_local_provider_no_warning(self):
        from transfer_confirmation import evaluate_transfer
        analysis.set_provider("ollama")
        analysis.set_model("llama3:latest", allow_unknown=True)
        try:
            context = evaluate_transfer("Harmloser Text", source_type="file",
                                        privacy_check=False)
        finally:
            analysis.set_model(analysis.DEFAULT_MODEL)
        self.assertIsNone(context.model_warning)
        self.assertFalse(context.needs_confirmation)


if __name__ == "__main__":
    unittest.main()
