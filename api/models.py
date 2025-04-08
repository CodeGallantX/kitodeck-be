from django.db import models
from django.contrib.auth.models import User

class SafetyReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    conversation_id = models.CharField(max_length=255)
    risk_score = models.FloatField()
    risk_level = models.CharField(max_length=10)
    details = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Safety Report for {self.user.username} - {self.risk_level}"