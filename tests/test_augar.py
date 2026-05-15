from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from augar_engine.constants import ALL_ENGINES
from augar_engine.core import parse_period
from augar_engine.data import DataProcessing
from augar_engine.pipeline import GenerateRequest, run_generation


class AugarTests(unittest.TestCase):
    def test_data_processing_import_and_symbols(self) -> None:
        data = DataProcessing()
        symbols = data.discover_symbols()
        self.assertEqual(symbols, ["000001.SS", "000300.SS", "DJI", "FTSE", "HSI", "NDX", "SPX", "VIX"])

    def test_period_requires_explicit_shape(self) -> None:
        self.assertEqual(parse_period("2026-04-M").label, "April 2026")
        with self.assertRaises(ValueError):
            parse_period("2026-04")

    def test_llm_params_accept_chatgpt_oauth(self) -> None:
        request = GenerateRequest(period="2026-04-M", provider="chatgpt_oauth", model="gpt-5.5")
        params = request.llm_params()
        self.assertEqual(params.provider, "chatgpt_oauth")
        self.assertEqual(params.model, "gpt-5.5")

    def test_mock_full_generation(self) -> None:
        temp = Path(tempfile.mkdtemp(prefix="augar-test-"))
        try:
            result = run_generation(GenerateRequest(period="2026-04-M", output_root=str(temp), provider="mock"))
            self.assertEqual(result["bundle_count"], 8)
            self.assertEqual(result["card_count"], 8 * len(ALL_ENGINES))
            self.assertEqual(result["generated_cards"], 8 * len(ALL_ENGINES))
            index = json.loads((temp / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(len(index["symbols"]), 8)
            self.assertEqual(index["engines"], list(ALL_ENGINES))
            reading = json.loads((temp / "readings" / "2026-04-M" / "SPX.json").read_text(encoding="utf-8"))
            self.assertEqual(len(reading["cards"]), len(ALL_ENGINES))
            for card in reading["cards"]:
                self.assertNotIn("raw_artifact", card)
                self.assertNotIn("market_context", card)
                self.assertIn("raw_ref", card)
            second = run_generation(GenerateRequest(period="2026-04-M", output_root=str(temp), provider="mock"))
            self.assertEqual(second["generated_cards"], 0)
            self.assertEqual(second["skipped_cards"], 8 * len(ALL_ENGINES))
            forced = run_generation(GenerateRequest(period="2026-04-M", output_root=str(temp), provider="mock", force="tarot"))
            self.assertEqual(forced["generated_cards"], 8)
        finally:
            shutil.rmtree(temp, ignore_errors=True)

    def test_history_provider_replays_debug_cards(self) -> None:
        source_temp = Path(tempfile.mkdtemp(prefix="augar-history-source-"))
        temp = Path(tempfile.mkdtemp(prefix="augar-history-test-"))
        try:
            source = run_generation(
                GenerateRequest(
                    period="2026-04-M",
                    symbols=["SPX"],
                    engines=["tarot"],
                    output_root=str(source_temp),
                    provider="mock",
                    force=True,
                )
            )
            replay = run_generation(
                GenerateRequest(
                    period="2026-04-M",
                    symbols=["SPX"],
                    engines=["tarot"],
                    output_root=str(temp),
                    provider="history",
                    history_run_id=str(source["run_id"]),
                    force=True,
                )
            )
            self.assertEqual(replay["generated_cards"], 1)
            card = json.loads((temp / "cards" / "2026-04-M" / "SPX" / "tarot.json").read_text(encoding="utf-8"))
            self.assertIn("raw_ref", card)
            self.assertIn("Tarot reads SPX", card["result"]["headline"])
        finally:
            shutil.rmtree(source_temp, ignore_errors=True)
            shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
