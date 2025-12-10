from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .logging import logger

def start_scheduler(recompute_func):
    scheduler = BackgroundScheduler()
    scheduler.add_job(recompute_func, CronTrigger(hour=2, minute=0))
    scheduler.start()
    logger.info("scheduler_started")
    return scheduler
