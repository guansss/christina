import atexit
from apscheduler.schedulers.background import BackgroundScheduler


scheduler = BackgroundScheduler()
scheduler.start()

atexit.register(lambda: scheduler.shutdown())
