import asyncio

from src.core import telegram_client, bot, logger
from src.root.tracker import NFTTracker


async def main():
    await telegram_client.start()
    logger.info("Telegram client started")

    tracker = NFTTracker()
    try:
        logger.info("Starting NFT tracker")
        await tracker.run()
    except Exception as e:
        logger.error(f"Error in main process: {e}")
    finally:
        logger.info("Shutting down...")
        if tracker.worker_task and not tracker.worker_task.cancelled():
            tracker.worker_task.cancel()

        for task in tracker.active_tasks.values():
            if not task.cancelled():
                task.cancel()

        await asyncio.gather(*tracker.active_tasks.values(), return_exceptions=True)

        await telegram_client.stop()
        await bot.session.close()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
