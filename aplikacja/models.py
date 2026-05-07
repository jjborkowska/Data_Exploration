from django.db import models

# Create your models here.
class Question(models.Model):
    question_text = models.Charfield("a question", max_length=200)
    pub_date = models.DateTimeField("date published")

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CHarField(max_length=200)