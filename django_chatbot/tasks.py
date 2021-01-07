# *****************************************************************************
#  MIT License
#
#  Copyright (c) 2020 Alexey Londkevich <londkevich@gmail.com>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom
#  the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#  ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#  THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# *****************************************************************************

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
