import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, Tuple, List

from aiogram.types import LinkPreviewOptions

from data.config import CHANNEL_ID
from src.core import bot, logger
from .parser import parse_gift
from ..utils.formatter import format_mint_message
from ..utils.history import HistoryManager


class NFTTracker:
    BACKOFF_INITIAL = 10
    BACKOFF_MAX = 300
    REFRESH_PROBABILITY = 0.05
    LONG_BACKOFF_THRESHOLD = 60
    LONG_BACKOFF_REFRESH_PROBABILITY = 0
    MESSAGE_INTERVAL = 0
    TASK_RESTART_DELAY = 0
    COLLECTION_START_DELAY = 0

    def __init__(self):
        self.history_manager = HistoryManager()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.processing: Set[str] = set()
        self.collections_config = self.history_manager.load_collections()
        self.rate_limit_cooldown: Dict[str, datetime] = {}
        self.last_published = datetime.now()
        self.message_queue = asyncio.Queue()
        self.worker_task = None
        self.last_filter_results = {}

    @staticmethod
    def extract_attributes(data: dict) -> Dict[str, str]:
        attributes = {}
        attrs = data['gift']['attributes']

        if len(attrs) >= 3:
            type_mapping = {0: 'model', 1: 'symbol', 2: 'backdrop'}

            for pos, attr_type in type_mapping.items():
                if pos < len(attrs):
                    attributes[attr_type] = attrs[pos]['name']

        return attributes

    @staticmethod
    def parse_allowed_values(config_value) -> List[str]:
        if not config_value:
            return []

        if isinstance(config_value, list):
            return config_value

        if isinstance(config_value, str):
            if config_value.endswith('.'):
                config_value = config_value[:-1]
            return [value.strip() for value in config_value.split(',') if value.strip()]

        return []

    def should_post_mint(self, collection: str, data: dict) -> bool:
        if not self.collections_config or collection not in self.collections_config:
            return True

        config = self.collections_config.get(collection, {})

        if all(not value for value in config.values()):
            return True

        attributes = self.extract_attributes(data)
        logger.debug(f"Extracted attributes: {attributes}")

        filter_results = {}

        for attr_type, expected in config.items():
            if attr_type not in ('model', 'backdrop', 'symbol') or not expected:
                continue

            allowed_values = self.parse_allowed_values(expected)

            attr_value = attributes.get(attr_type)

            matches = attr_value in allowed_values if allowed_values and attr_value else True

            filter_results[attr_type] = {
                'value': attr_value,
                'allowed': allowed_values,
                'matches': matches
            }

            if allowed_values and not matches and attr_value:
                self.last_filter_results = filter_results
                return False

        self.last_filter_results = filter_results
        return True

    async def handle_rate_limit(self, collection: str, wait_time: int = 60) -> None:
        cooldown_until = datetime.now() + timedelta(seconds=wait_time)
        self.rate_limit_cooldown[collection] = cooldown_until
        logger.warning(f"Rate limit for {collection}, cooldown until {cooldown_until.strftime('%H:%M:%S')}")

        await asyncio.sleep(wait_time * 1.1)

    async def update_supply(self, collection: str) -> Tuple[bool, Optional[int]]:
        if collection in self.rate_limit_cooldown:
            if datetime.now() < self.rate_limit_cooldown[collection]:
                logger.debug(f"Skipping update for {collection} - in cooldown")
                return False, None
            else:
                del self.rate_limit_cooldown[collection]

        try:
            await asyncio.sleep(random.uniform(0.5, 2.0))

            data = await parse_gift(f"{collection}-1")

            if 'error' not in data:
                current = data['gift']['availability_issued']
                self.history_manager.update_number(collection, current)
                logger.info(f"Updated {collection} supply to #{current}")
                return True, current

            return False, None

        except Exception as e:
            if "Too Many Requests" in str(e) or "FLOOD_WAIT_" in str(e):
                wait_time = 60

                try:
                    if "FLOOD_WAIT_" in str(e):
                        wait_time = int(str(e).split("FLOOD_WAIT_")[1].split(" ")[0])
                except:
                    pass

                await self.handle_rate_limit(collection, wait_time)

            else:
                logger.error(f"Error updating supply for {collection}: {e}")

            return False, None

    async def message_worker(self):
        while True:
            try:
                data = await self.message_queue.get()

                now = datetime.now()
                since_last_publish = (now - self.last_published).total_seconds()

                if since_last_publish < self.MESSAGE_INTERVAL:
                    wait_time = self.MESSAGE_INTERVAL - since_last_publish
                    logger.debug(f"Rate limiting: waiting {wait_time:.2f}s before next message")
                    await asyncio.sleep(wait_time)

                await self.send_mint_notification(data)
                self.last_published = datetime.now()

                self.message_queue.task_done()

            except Exception as e:
                logger.error(f"Error in message worker: {e}")
                await asyncio.sleep(self.TASK_RESTART_DELAY)

    @staticmethod
    async def send_mint_notification(data: dict):
        message, nft_url = format_mint_message(data)
        await bot.send_message(
            CHANNEL_ID,
            message,
            link_preview_options=LinkPreviewOptions(
                url=nft_url,
                show_above_text=True
            )
        )
        logger.info(f"Published: {data['gift']['title']}-{data['gift']['num']}")

    def format_filter_log(self) -> str:
        if not self.last_filter_results:
            return "No filter data"

        return " | ".join([
            f"{k.title()}: {v['value']} (Allowed: {', '.join(v['allowed'][:3]) + ('...' if len(v['allowed']) > 3 else '') if v['allowed'] else 'Any'})"
            for k, v in self.last_filter_results.items()
            if v.get('allowed')
        ])

    async def track_collection(self, collection: str):
        consecutive_errors = 0
        backoff_delay = self.BACKOFF_INITIAL

        while True:
            try:
                current_num = self.history_manager.get_current_number(collection)

                refresh_needed = (consecutive_errors > 0 or
                                  random.random() < self.REFRESH_PROBABILITY)

                if refresh_needed:
                    success, refreshed_num = await self.update_supply(collection)
                    if success:
                        current_num = refreshed_num
                        consecutive_errors = 0
                        backoff_delay = self.BACKOFF_INITIAL

                next_num = current_num + 1
                data = await parse_gift(f"{collection}-{next_num}")

                if 'error' not in data:
                    if self.should_post_mint(collection, data):
                        await self.message_queue.put(data)
                        logger.debug(f"Queued: {collection}-{next_num}")
                    else:
                        filter_log = self.format_filter_log()
                        logger.info(f"Skipped: {collection}-{next_num} (filtered) - {filter_log}")

                    self.history_manager.update_number(collection, next_num)
                    consecutive_errors = 0
                    backoff_delay = self.BACKOFF_INITIAL

                    await asyncio.sleep(random.uniform(3, 7))
                else:
                    await asyncio.sleep(backoff_delay)

                    backoff_delay = min(backoff_delay * 1.2, self.BACKOFF_MAX)

                    if (backoff_delay > self.LONG_BACKOFF_THRESHOLD and
                            random.random() < self.LONG_BACKOFF_REFRESH_PROBABILITY):
                        logger.debug(f"Long delay for {collection}, trying refresh")
                        await self.update_supply(collection)

            except Exception as e:
                if "Too Many Requests" in str(e) or "FLOOD_WAIT_" in str(e):
                    wait_time = 20
                    try:
                        if "FLOOD_WAIT_" in str(e):
                            wait_time = int(str(e).split("FLOOD_WAIT_")[1].split(" ")[0])
                    except:
                        pass

                    await self.handle_rate_limit(collection, wait_time)
                    await self.update_supply(collection)
                else:
                    logger.error(f"Error tracking {collection}: {e}")
                    consecutive_errors += 1
                    backoff_delay = min(backoff_delay * 2, self.BACKOFF_MAX)
                    await asyncio.sleep(5)

    async def start_tracking(self, collection: str):
        if collection in self.processing:
            return

        self.processing.add(collection)
        try:
            await self.update_supply(collection)

            task = asyncio.create_task(self.track_collection(collection))
            self.active_tasks[collection] = task
        finally:
            self.processing.remove(collection)

    async def run(self):
        self.worker_task = asyncio.create_task(self.message_worker())
        logger.info("Message queue worker started")

        collections = list(self.collections_config.keys())
        logger.info(f"Starting to track {len(collections)} collections")

        for i, col in enumerate(collections):
            await self.start_tracking(col)
            if i < len(collections) - 1:
                await asyncio.sleep(self.COLLECTION_START_DELAY)

        logger.info("All collection trackers started")

        while self.active_tasks:
            done, _ = await asyncio.wait(
                list(self.active_tasks.values()),
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in done:
                for col, t in list(self.active_tasks.items()):
                    if t == task:
                        del self.active_tasks[col]
                        logger.warning(f"Collection tracker for {col} completed unexpectedly")

                        if not task.cancelled():
                            logger.info(f"Restarting tracker for {col}")
                            await asyncio.sleep(self.TASK_RESTART_DELAY)
                            new_task = asyncio.create_task(self.track_collection(col))
                            self.active_tasks[col] = new_task
