import asyncio
import sys
from twisted.internet import asyncioreactor
import logging

logger = logging.getLogger(__name__)

def install_reactor():
    """Ініціалізує Twisted AsyncioSelectorReactor один раз."""
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            logger.info("Set WindowsSelectorEventLoopPolicy")
        asyncioreactor.install()
        logger.info("AsyncioSelectorReactor installed")
    except Exception as e:
        logger.warning(f"Reactor installation skipped: {str(e)}")

# Викликати ініціалізацію один раз
install_reactor()