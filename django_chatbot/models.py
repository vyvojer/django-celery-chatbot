from django.db import models

# Create your models here.
from polymorphic.models import PolymorphicModel


class Message(models.Model):
    text = models.TextField(default="")

    def __str__(self):
        return self.text


class Pattern(PolymorphicModel):
    def match(self, message: str) -> bool:
        return False


class Phrase(models.Model):
    phrase = models.TextField(unique=True, db_index=True)

    def __str__(self):
        return self.phrase


class SimplePattern(Pattern):
    """ Checks if the words or phrases are in the message. """
    ANY = 'any'
    ALL = 'all'
    CONDITIONS = (
        (ANY, 'Any'),
        (ALL, 'All'),
    )

    phrases = models.ManyToManyField(Phrase)
    condition = models.CharField(max_length=3, choices=CONDITIONS, default=ANY)

    def match(self, message: str) -> bool:
        if self.condition == self.ALL:
            return all(phrase.phrase.lower() in message.lower()
                       for phrase in self.phrases.all())
        else:
            return any(phrase.phrase.lower() in message.lower()
                       for phrase in self.phrases.all())
