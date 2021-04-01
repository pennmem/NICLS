from django.dispatch import Signal

dispatcher = Signal()

class Publisher:
    def __init__(self, publisher_id=None):
        if publisher_id:
            self.publisher_id = publisher_id
        else:
            self.publisher_id = str(uuid4().hex)

# JPB: TODO: Consider making publish function that automatically has sender
#    def publish(self, message, **kwargs):
#        dispatcher.send(sender=self.publisher_id, message=message, **kwargs)
