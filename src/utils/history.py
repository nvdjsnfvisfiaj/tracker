import json
import os
from pathlib import Path
from typing import Dict

from src.core import logger


class HistoryManager:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent
        self.history_file = self.root_dir / "data" / "history.json"
        self.collections_file = self.root_dir / "collections.json"
        self.history: Dict[str, int] = {}
        self._load_history()

    def _load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = {}
            self._save_history()

    def _save_history(self):
        os.makedirs(self.history_file.parent, exist_ok=True)
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def get_current_number(self, collection: str) -> int:
        return self.history.get(collection, 0)

    def update_number(self, collection: str, number: int):
        self.history[collection] = number
        self._save_history()

    def load_collections(self) -> dict:
        try:
            with open(self.collections_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load collections: {e}")
            return {}
