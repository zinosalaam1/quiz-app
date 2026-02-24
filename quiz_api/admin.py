from django.contrib import admin
from .models import Team, Question, GameSession, Answer, AdminCode, Participant


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "session", "score", "status", "code"]
    list_filter = ["status", "session"]
    search_fields = ["name", "code"]
    readonly_fields = ["code"]
    ordering = ["-score"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["round", "order", "question"]
    list_filter = ["round"]
    ordering = ["round", "order"]


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "current_question", "active_team", "buzzer_locked"]
    list_filter = ["is_active", "buzzer_locked"]
    search_fields = ["name"]
    ordering = ["-created_at"]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ["team", "question", "is_correct", "points_awarded", "created_at"]
    list_filter = ["is_correct", "session"]
    search_fields = ["team__name"]
    ordering = ["-created_at"]


@admin.register(AdminCode)
class AdminCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["code"]


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ["name", "team", "join_code"]
    search_fields = ["name", "join_code"]
    readonly_fields = ["join_code"]