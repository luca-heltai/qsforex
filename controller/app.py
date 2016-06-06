from __future__ import absolute_import

from celery import Celery
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

# Create a new controller
controller = Celery(name='qsforex.controller')
controller.config_from_object('qsforex.controller.celeryconfig')

# Next we start the controller
if __name__ == '__main__':
    logger.info("Starting controller")
    controller.start()

