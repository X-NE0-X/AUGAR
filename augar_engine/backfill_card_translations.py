from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Iterable

import translators as ts


TEXT_FIELDS = ("headline", "subline", "short_reading", "long_reading")


def has_cjk(value: str) -> bool:
    return any("\u3400" <= char <= "\u9fff" for char in value)


def result_text(result: dict[str, Any]) -> str:
    return "\n".join(str(result.get(field, "")) for field in TEXT_FIELDS)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def translate(text: str, *, source: str, target: str, retries: int, sleep: float) -> str:
    if not text:
        return ""
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return str(ts.translate_text(text, from_language=source, to_language=target))
        except Exception as exc:  # pragma: no cover - network/service dependent
            last_error = exc
            if attempt < retries:
                time.sleep(sleep)
    raise RuntimeError(f"translation failed {source}->{target}: {last_error}") from last_error


def same_result(left: dict[str, Any] | None, right: dict[str, Any] | None) -> bool:
    if not left or not right:
        return False
    return all(str(left.get(field, "")) == str(right.get(field, "")) for field in TEXT_FIELDS)


def translate_result(
    result: dict[str, Any],
    *,
    source: str,
    target: str,
    retries: int,
    sleep: float,
) -> dict[str, Any]:
    translated = dict(result)
    for field in TEXT_FIELDS:
        translated[field] = translate(
            str(result.get(field, "")),
            source=source,
            target=target,
            retries=retries,
            sleep=sleep,
        )
    return translated


def iter_card_files(cards_root: Path) -> Iterable[Path]:
    return sorted(cards_root.glob("*/*/*.json"))


def backfill_cards(cards_root: Path, *, force: bool, retries: int, sleep: float) -> tuple[int, int]:
    scanned = 0
    updated = 0
    for path in iter_card_files(cards_root):
        card = load_json(path)
        result = card.get("result")
        if not isinstance(result, dict):
            continue
        scanned += 1

        result_en = card.get("result_en") if isinstance(card.get("result_en"), dict) else None
        source_is_zh = has_cjk(result_text(result))

        if source_is_zh:
            if not force and result_en and not same_result(result_en, result):
                continue
            card["result_en"] = translate_result(
                result,
                source="zh",
                target="en",
                retries=retries,
                sleep=sleep,
            )
        else:
            if result_en and not force:
                continue
            card["result_en"] = dict(result)
            card["result"] = translate_result(
                result,
                source="en",
                target="zh",
                retries=retries,
                sleep=sleep,
            )

        write_json(path, card)
        updated += 1
        print(f"updated_card {path.as_posix()}")
    return scanned, updated


def sync_readings(data_root: Path) -> tuple[int, int]:
    card_lookup: dict[tuple[str, str, str], dict[str, Any]] = {}
    for path in iter_card_files(data_root / "cards"):
        period, ticker, engine_file = path.parts[-3:]
        card_lookup[(period, ticker, path.stem)] = load_json(path)

    scanned = 0
    updated = 0
    for path in sorted((data_root / "readings").rglob("*.json")):
        reading = load_json(path)
        cards = reading.get("cards")
        asset = reading.get("asset") if isinstance(reading.get("asset"), dict) else {}
        period = reading.get("period") if isinstance(reading.get("period"), dict) else {}
        if not isinstance(cards, list):
            continue

        path_period = ""
        try:
            rel = path.relative_to(data_root / "readings")
            path_period = rel.parts[0]
        except ValueError:
            pass
        period_id = str(period.get("id", path_period))
        ticker = str(asset.get("ticker", path.stem if path.parent.name != "readings" else ""))
        new_cards = []
        changed = False
        for card in cards:
            scanned += 1
            engine = card.get("engine") if isinstance(card, dict) else {}
            engine_id = str(engine.get("id", ""))
            replacement = card_lookup.get((period_id, ticker, engine_id))
            if replacement is None and path_period:
                replacement = card_lookup.get((path_period, ticker, engine_id))
            if replacement:
                new_cards.append(replacement)
                changed = changed or replacement != card
            else:
                new_cards.append(card)
        if changed:
            reading["cards"] = new_cards
            write_json(path, reading)
            updated += 1
            print(f"updated_reading {path.as_posix()}")
    return scanned, updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill AUGAR public card translations.")
    parser.add_argument("--data-root", default="public/data")
    parser.add_argument("--force", action="store_true", help="Retranslate cards even when result_en already differs from result.")
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--sleep", type=float, default=1.5)
    args = parser.parse_args()

    data_root = Path(args.data_root)
    scanned_cards, updated_cards = backfill_cards(
        data_root / "cards",
        force=args.force,
        retries=args.retries,
        sleep=args.sleep,
    )
    scanned_embedded_cards, updated_readings = sync_readings(data_root)
    print(
        json.dumps(
            {
                "scanned_card_files": scanned_cards,
                "updated_card_files": updated_cards,
                "scanned_embedded_cards": scanned_embedded_cards,
                "updated_reading_files": updated_readings,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
