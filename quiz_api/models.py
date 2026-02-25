import uuid
from django.db import models, transaction


class GameSession(models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)

    current_question = models.ForeignKey(
        "Question",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    active_team = models.ForeignKey(
        "Team",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    buzzer_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # If this session is being activated
        if self.is_active:
            with transaction.atomic():
                # Deactivate all other sessions
                GameSession.objects.exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Team(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=12, unique=True, blank=True)
    session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name="teams"
    )
    score = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        default="waiting"
    )

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = str(uuid.uuid4()).split("-")[0].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Participant(models.Model):
    name = models.CharField(max_length=255)
    join_code = models.CharField(max_length=8, unique=True, blank=True)
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="participants"
    )

    def save(self, *args, **kwargs):
        if not self.join_code:
            self.join_code = str(uuid.uuid4()).split("-")[0].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Question(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    round = models.IntegerField(default=1)
    question = models.TextField()
    answer = models.CharField(max_length=500)
    options = models.JSONField(null=True, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["round", "order"]

    def __str__(self):
        return f"Round {self.round} - Question {self.order}"


class Answer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="submissions"
    )
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)

    answer_text = models.TextField()
    is_correct = models.BooleanField(null=True, blank=True)
    points_awarded = models.IntegerField(default=0)
    time_taken = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.team.name} - {self.question.id}"


class AdminCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code