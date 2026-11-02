import json
import os
from pathlib import Path
from typing import Dict, Optional
from app.models import Account, LedgerData


def get_default_ledger_path() -> Path:
    env_path = os.getenv("LEDGER_PATH")
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parent.parent / "ledger.json"


def load_ledger(path: Optional[Path] = None) -> LedgerData:
    ledger_path = path or get_default_ledger_path()
    if not ledger_path.exists():
        raise FileNotFoundError(f"Ledger file not found at: {ledger_path}")

    with open(ledger_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return LedgerData(**data)


def build_account_map(accounts: list[Account]) -> Dict[str, Account]:
    return {account.number: account for account in accounts}
