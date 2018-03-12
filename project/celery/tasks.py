from project.celery.modules.video_scanner import scan
from project import celery

@celery.task(bind=True)
def video_scanner(self):
    scan()
