BROKER_URL = 'amqp://'
CELERY_RESULT_BACKEND = 'amqp://'

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'Europe/Rome'
CELERY_ENABLE_UTC = True
CELERY_IMPORTS = ("qsforex.library.price_handlers")

# This will be necessary when we start doing real stuff
# CELERY_ANNOTATIONS = {
#     'tasks.add': {'rate_limit': '10/m'}
# }
