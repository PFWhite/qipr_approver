from django.db import models

class Registerable(models.Model):
    in_registry = models.BooleanField(default=False)

    def register(self):
        self.in_registry = True

    def natural_key(self):
        return (self.guid, self.get_natural_dict())

    class Meta:
        abstract = True
