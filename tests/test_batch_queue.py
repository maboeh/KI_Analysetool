import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import AnalysisError, AnalysisErrorCode, AnalysisOutcome
from batch_queue import BatchQueue
from results_manager import ResultsManager


def _ok(content="Ergebnis"):
    return AnalysisOutcome(content=content, prompt_tokens=10, completion_tokens=5)


def _err(code=AnalysisErrorCode.PROVIDER_ERROR, retryable=False):
    return AnalysisOutcome(error=AnalysisError(code, "Fehler", retryable=retryable))


class BatchQueueTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.db_path = str(self.tmp / "results.db")
        self.results_manager = ResultsManager(self.db_path, str(self.tmp / "results"))
        self.queue = BatchQueue(self.db_path, results_manager=self.results_manager)

    def tearDown(self):
        for job in self.queue.list_jobs():
            self.queue.cancel_job(job.id)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _wait(self, job_id, timeout=10.0):
        thread = self.queue._threads.get(job_id)
        if thread:
            thread.join(timeout=timeout)

    def _create_text_job(self, name="Job", sources=("t1", "t2")):
        return self.queue.create_job(
            name=name,
            prompt="Analysiere: {text}",
            items=[{"source": s, "source_type": "text"} for s in sources],
        )


class TestJobPersistence(BatchQueueTestCase):
    def test_create_job_persists_items(self):
        job_id = self._create_text_job()
        job = self.queue.get_job(job_id)
        self.assertEqual(job.status, "pending")
        items = self.queue.get_items(job_id)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].status, "pending")
        self.assertEqual(items[0].position, 0)

    def test_validation(self):
        with self.assertRaises(ValueError):
            self.queue.create_job("x", "p", items=[])
        with self.assertRaises(ValueError):
            self.queue.create_job("x", "  ", items=[{"source": "a"}])

    def test_delete_job_removes_items(self):
        job_id = self._create_text_job()
        self.assertTrue(self.queue.delete_job(job_id))
        self.assertIsNone(self.queue.get_job(job_id))
        self.assertEqual(self.queue.get_items(job_id), [])


class TestExecution(BatchQueueTestCase):
    @patch("batch_queue.analyze_text")
    def test_items_complete_and_save_results(self, mock_analyze):
        mock_analyze.side_effect = \
            lambda prompt, model=None: _ok(f"Ergebnis für {len(prompt)}")
        job_id = self._create_text_job()
        self.assertTrue(self.queue.start_job(job_id))
        self._wait(job_id)

        job = self.queue.get_job(job_id)
        self.assertEqual(job.status, "completed")
        progress = self.queue.get_job_progress(job_id)
        self.assertEqual(progress["done"], 2)
        self.assertGreater(progress["cost"], 0)
        for item in self.queue.get_items(job_id):
            self.assertEqual(item.status, "done")
            self.assertIsNotNone(item.result_id)
            self.assertIsNotNone(
                self.results_manager.load_result(item.result_id))

    @patch("batch_queue.analyze_text")
    def test_retryable_error_retried_once(self, mock_analyze):
        mock_analyze.side_effect = [
            _err(AnalysisErrorCode.RATE_LIMITED, retryable=True),
            _ok("Retry-Ergebnis"),
        ]
        job_id = self._create_text_job(sources=("t1",))
        self.queue.start_job(job_id)
        self._wait(job_id)
        item = self.queue.get_items(job_id)[0]
        self.assertEqual(item.status, "done")
        self.assertEqual(item.attempts, 2)
        self.assertEqual(mock_analyze.call_count, 2)

    @patch("batch_queue.analyze_text")
    def test_non_retryable_error_fails_immediately(self, mock_analyze):
        mock_analyze.return_value = _err(AnalysisErrorCode.PROVIDER_ERROR)
        job_id = self._create_text_job(sources=("t1",))
        self.queue.start_job(job_id)
        self._wait(job_id)
        item = self.queue.get_items(job_id)[0]
        self.assertEqual(item.status, "failed")
        self.assertEqual(item.attempts, 1)
        self.assertEqual(item.error_code, "provider_error")
        self.assertEqual(self.queue.get_job(job_id).status, "failed")

    @patch("batch_queue.analyze_text")
    def test_privacy_findings_skip_item(self, mock_analyze):
        job_id = self._create_text_job(
            sources=("Mail an test@example.com", "Sauberer Text"))
        mock_analyze.return_value = _ok()
        self.queue.start_job(job_id)
        self._wait(job_id)
        items = self.queue.get_items(job_id)
        self.assertEqual(items[0].status, "skipped")
        self.assertEqual(items[1].status, "done")
        self.assertEqual(self.queue.get_job(job_id).status, "completed")
        # Find-Item wurde nie an analyze_text gesendet
        self.assertEqual(mock_analyze.call_count, 1)

    @patch("batch_queue.analyze_text")
    def test_generic_invalid_input_stays_failed(self, mock_analyze):
        """Nur Datenschutz-Funde werden 'skipped'; INVALID_INPUT bleibt 'failed'."""
        mock_analyze.return_value = _err(AnalysisErrorCode.INVALID_INPUT)
        job_id = self._create_text_job(sources=("Sauberer Text",))
        self.queue.start_job(job_id)
        self._wait(job_id)
        item = self.queue.get_items(job_id)[0]
        self.assertEqual(item.status, "failed")
        self.assertEqual(item.error_code, AnalysisErrorCode.INVALID_INPUT.value)

    @patch("batch_queue.analyze_text")
    def test_job_model_passed_without_session_mutation(self, mock_analyze):
        """Das Job-Modell wird explizit übergeben, die Session bleibt unverändert."""
        import analysis
        previous_model = analysis._default_session.current_model
        mock_analyze.return_value = _ok()
        job_id = self.queue.create_job(
            name="Job",
            prompt="Analysiere: {text}",
            model="gpt-4o-mini",
            items=[{"source": "t1", "source_type": "text"}],
        )
        self.queue.start_job(job_id)
        self._wait(job_id)
        _, kwargs = mock_analyze.call_args
        self.assertEqual(kwargs.get("model"), "gpt-4o-mini")
        self.assertEqual(analysis._default_session.current_model, previous_model)

    def test_cancel_marks_open_items(self):
        job_id = self._create_text_job()
        self.queue.cancel_job(job_id)
        job = self.queue.get_job(job_id)
        self.assertEqual(job.status, "cancelled")
        for item in self.queue.get_items(job_id):
            self.assertEqual(item.status, "cancelled")
        self.assertFalse(self.queue.start_job(job_id))

    @patch("batch_queue.analyze_text")
    def test_pause_then_resume(self, mock_analyze):
        mock_analyze.return_value = _ok()
        job_id = self._create_text_job()
        # Scheduler mit gesetztem Pause-Flag: endet sofort, Items bleiben pending
        self.queue._control(job_id)["pause"].set()
        self.queue._run_job(job_id, None)
        items = self.queue.get_items(job_id)
        self.assertTrue(all(i.status == "pending" for i in items))

        # Fortsetzen verarbeitet den Rest
        self.queue.resume_job(job_id)
        self._wait(job_id)
        for thread in list(self.queue._threads.values()):
            thread.join(timeout=5)
        self.assertTrue(all(i.status == "done"
                            for i in self.queue.get_items(job_id)))

    def test_interrupted_items_resume_after_restart(self):
        job_id = self._create_text_job()
        with self.queue._connect() as conn:
            conn.execute("UPDATE batch_items SET status='running' WHERE job_id=?",
                         (job_id,))
            conn.execute("UPDATE batch_jobs SET status='running' WHERE id=?",
                         (job_id,))
            conn.commit()
        # Neustart simulieren
        new_queue = BatchQueue(self.db_path, results_manager=self.results_manager)
        job = new_queue.get_job(job_id)
        self.assertEqual(job.status, "paused")
        self.assertTrue(all(i.status == "pending"
                            for i in new_queue.get_items(job_id)))


if __name__ == "__main__":
    unittest.main()
