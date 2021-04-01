from django.dispatch import Signal

TASK_SERVER = "task_server"
CLASSIFIER = "classifier"
BIOSEMI = "biosemi"

dispatcher = Signal()

class Publisher:
    def __init__(self, uid=None):
        if uid:
            self.uid = uid
        else:
            self.uid = str(uuid4().hex)

