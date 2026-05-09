import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Worker started and waiting for jobs...")
    while True:
        try:
            logger.info("Worker heartbeat - system running")
            time.sleep(30)
        except KeyboardInterrupt:
            logger.info("Worker shutting down...")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()