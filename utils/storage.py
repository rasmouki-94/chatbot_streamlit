from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

import pandas as pd


CSV_PATH = Path("data") / "responses.csv"
EXPECTED_COLUMNS = [
    "timestamp",
    "prenom",
    "nom",
    "entreprise",
    "email",
    "q1",
    "q2",
    "q3",
    "q4",
    "q5",
    "q6",
    "q7",
    "q8",
    "q9",
    "q10",
    "score",
    "band",
]


def append_to_csv(data: Dict[str, str | int]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {col: data.get(col, "") for col in EXPECTED_COLUMNS}
    if not payload["timestamp"]:
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()

    frame = pd.DataFrame([payload], columns=EXPECTED_COLUMNS)
    file_exists = CSV_PATH.exists()
    frame.to_csv(
        CSV_PATH,
        mode="a",
        header=not file_exists,
        index=False,
        encoding="utf-8",
    )
