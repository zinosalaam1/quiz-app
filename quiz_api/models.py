from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.

class Team(models.Model):
    """Team model representing each quiz team"""
    TEAM_CHOICES = [
        ('team_a', 'Tour Arcade Team A'),
        ('team_b', 'Tour Arcade Team B'),
        ('team_c', 'Tour Arcade Team C'),
        ('team_d', 'Tour Arcade Team D'),
    ]
    
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('answering', 'Answering'),
        ('locked', 'Locked'),
        ('timeout', 'Timeout'),
        ('buzzed', 'Buzzed'),
    ]
    
    id = models.CharField(max_length=20, primary_key=True, choices=TEAM_CHOICES)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    score = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-score']
    
    def __str__(self):
        return self.name


class Question(models.Model):
    """Question model for quiz questions"""
    ROUND_CHOICES = [
        (1, 'Round 1 - General Questions'),
        (2, 'Round 2 - Pass The Mic'),
        (3, 'Round 3 - Buzzer Round'),
        (4, 'Round 4 - Rapid Fire'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    round = models.IntegerField(choices=ROUND_CHOICES)
    question = models.TextField()
    answer = models.CharField(max_length=500)
    options = models.JSONField(null=True, blank=True)  # Optional multiple choice
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['round', 'order']
    
    def __str__(self):
        return f"Round {self.round} - Question {self.order}"


class GameSession(models.Model):
    """Game session model to track current game state"""
    ROUND_TYPE_CHOICES = [
        ('general', 'General Questions'),
        ('pass-the-mic', 'Pass The Mic'),
        ('buzzer', 'Buzzer Round'),
        ('rapid-fire', 'Rapid Fire'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    current_round = models.IntegerField(default=1)
    current_question_index = models.IntegerField(default=0)
    active_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='active_sessions')
    timer_seconds = models.IntegerField(default=0)
    is_timer_running = models.BooleanField(default=False)
    round_type = models.CharField(max_length=20, choices=ROUND_TYPE_CHOICES, default='general')
    buzzer_enabled = models.BooleanField(default=False)
    buzzer_order = models.JSONField(default=list)  # List of team IDs in buzz order
    question_revealed = models.BooleanField(default=False)
    game_started = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Session {self.id} - Round {self.current_round}"


class Answer(models.Model):
    """Answer submission tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    question = models.ForeignKey(
    Question,
    on_delete=models.CASCADE,
    related_name='submissions'
)
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    answer_text = models.TextField()
    is_correct = models.BooleanField(null=True, blank=True)  # Null until admin evaluates
    points_awarded = models.IntegerField(default=0)
    time_taken = models.IntegerField(help_text="Seconds taken to answer")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.team.name} - Question {self.question.id}"


class AdminCode(models.Model):
    """Admin authentication code"""
    code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.code