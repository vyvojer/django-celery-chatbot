import logging

from celery import Task
from celery import shared_task

from django_chatbot.services.dispatcher import Dispatcher

log = logging.getLogger(__name__)


class LoggingTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        log.exception(
            "Task %s (id=%s) failed, exc=%s  exinfo=%s",
            self.name, task_id, exc, einfo
        )
        super(LoggingTask, self).on_failure(exc, task_id, args, kwargs, einfo)


@shared_task(bind=True, ignore_result=True)
def dispatch(self, update_data: dict, token_slug: str):
    log.debug("Task started")
    dispatcher = Dispatcher(update_data=update_data, token_slug=token_slug)
    dispatcher.dispatch()
