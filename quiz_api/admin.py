
from django.contrib import admin
from .models import Team, Question, GameSession, Answer, AdminCode

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'score', 'status']
    list_filter = ['status']
    search_fields = ['name']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['round', 'question', 'order']
    list_filter = ['round']
    ordering = ['round', 'order']

admin.site.register(GameSession)
admin.site.register(Answer)
admin.site.register(AdminCode)