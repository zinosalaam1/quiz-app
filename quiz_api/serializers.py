from rest_framework import serializers
from .models import Team, Question, GameSession, Answer, AdminCode

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'code', 'score', 'status', 'created_at']



class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'round', 'question', 'answer', 'options', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class QuestionListSerializer(serializers.ModelSerializer):
    """Serializer for listing questions (without answer for teams)"""
    class Meta:
        model = Question
        fields = ['id', 'round', 'question', 'options', 'order']


class GameSessionSerializer(serializers.ModelSerializer):
    active_team_name = serializers.CharField(source='active_team.name', read_only=True)
    
    class Meta:
        model = GameSession
        fields = [
            'id', 'current_round', 'current_question_index', 'active_team',
            'active_team_name', 'timer_seconds', 'is_timer_running',
            'round_type', 'buzzer_enabled', 'buzzer_order',
            'question_revealed', 'game_started', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AnswerSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    
    class Meta:
        model = Answer
        fields = [
            'id', 'team', 'team_name', 'question', 'session',
            'answer_text', 'is_correct', 'points_awarded',
            'time_taken', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']