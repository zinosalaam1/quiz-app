from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework import permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Team, Question, GameSession, Answer, AdminCode
from .serializers import (
    TeamSerializer, QuestionSerializer, QuestionListSerializer,
    GameSessionSerializer, AnswerSerializer
)

# Custom permission for admin
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        admin_code = request.headers.get('X-Admin-Code')
        return AdminCode.objects.filter(code=admin_code, is_active=True).exists()


# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    """Verify admin code"""
    code = request.data.get('code')
    if AdminCode.objects.filter(code=code, is_active=True).exists():
        return Response({'success': True, 'message': 'Admin authenticated'})
    return Response({'success': False, 'message': 'Invalid admin code'}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def team_login(request):
    """Verify team code"""
    code = request.data.get('code')
    try:
        team = Team.objects.get(code=code)
        return Response({
            'success': True,
            'team': TeamSerializer(team).data
        })
    except Team.DoesNotExist:
        return Response({'success': False, 'message': 'Invalid team code'}, status=400)


# Team ViewSet
class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['post'])
    def update_score(self, request, pk=None):
        """Update team score"""
        team = self.get_object()
        points = request.data.get('points', 0)
        team.score = max(0, team.score + points)
        team.save()
        return Response(TeamSerializer(team).data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update team status"""
        team = self.get_object()
        status = request.data.get('status')
        if status in ['waiting', 'answering', 'locked', 'timeout', 'buzzed']:
            team.status = status
            team.save()
            return Response(TeamSerializer(team).data)
        return Response({'error': 'Invalid status'}, status=400)
    
    @action(detail=False, methods=['post'])
    def reset_all(self, request):
        """Reset all teams (admin only)"""
        Team.objects.all().update(score=0, status='waiting')
        return Response({'success': True})


# Question ViewSet
class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        # Hide answers from team view
        if self.action == 'list' and not self.is_admin(self.request):
            return QuestionListSerializer
        return QuestionSerializer
    
    def is_admin(self, request):
        admin_code = request.headers.get('X-Admin-Code')
        return AdminCode.objects.filter(code=admin_code, is_active=True).exists()
    
    @action(detail=False, methods=['get'])
    def by_round(self, request):
        """Get questions filtered by round"""
        round_num = request.query_params.get('round')
        if round_num:
            questions = self.queryset.filter(round=round_num)
            serializer = self.get_serializer(questions, many=True)
            return Response(serializer.data)
        return Response({'error': 'Round parameter required'}, status=400)


# Game Session ViewSet
class GameSessionViewSet(viewsets.ModelViewSet):
    queryset = GameSession.objects.filter(is_active=True)
    serializer_class = GameSessionSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current active game session"""
        session = GameSession.objects.filter(is_active=True).first()
        if session:
            return Response(GameSessionSerializer(session).data)
        return Response({'error': 'No active session'}, status=404)
    
    @action(detail=True, methods=['post'])
    def start_game(self, request, pk=None):
        """Start the game"""
        session = self.get_object()
        session.game_started = True
        session.save()
        return Response(GameSessionSerializer(session).data)
    
    @action(detail=True, methods=['post'])
    def set_round(self, request, pk=None):
        """Set current round"""
        session = self.get_object()
        round_num = request.data.get('round')
        
        round_types = {1: 'general', 2: 'pass-the-mic', 3: 'buzzer', 4: 'rapid-fire'}
        session.current_round = round_num
        session.round_type = round_types.get(round_num, 'general')
        session.buzzer_enabled = (round_num == 3)
        session.current_question_index = 0
        session.active_team = None
        session.save()
        
        return Response(GameSessionSerializer(session).data)
    
    @action(detail=True, methods=['post'])
    def next_question(self, request, pk=None):
        """Move to next question"""
        session = self.get_object()
        session.current_question_index += 1
        session.active_team = None
        session.buzzer_order = []
        session.question_revealed = False
        session.timer_seconds = 0
        session.is_timer_running = False
        session.save()
        return Response(GameSessionSerializer(session).data)
    
    @action(detail=True, methods=['post'])
    def set_active_team(self, request, pk=None):
        """Set active team"""
        session = self.get_object()
        team_id = request.data.get('team_id')
        if team_id:
            session.active_team_id = team_id
            session.save()
            # Update team statuses
            Team.objects.all().update(status='waiting')
            Team.objects.filter(id=team_id).update(status='answering')
        return Response(GameSessionSerializer(session).data)
    
    @action(detail=True, methods=['post'])
    def team_buzz(self, request, pk=None):
        """Team buzzes in"""
        session = self.get_object()
        team_id = request.data.get('team_id')
        
        if session.buzzer_enabled and team_id not in session.buzzer_order:
            session.buzzer_order.append(team_id)
            if len(session.buzzer_order) == 1:
                session.active_team_id = team_id
            session.save()
            Team.objects.filter(id=team_id).update(status='buzzed')
            
        return Response(GameSessionSerializer(session).data)


# Answer ViewSet
class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['post'])
    def evaluate(self, request, pk=None):
        """Admin evaluates answer as correct/wrong"""
        answer = self.get_object()
        is_correct = request.data.get('is_correct')
        points = request.data.get('points', 0)
        
        answer.is_correct = is_correct
        answer.points_awarded = points
        answer.save()
        
        # Update team score
        if is_correct:
            answer.team.score += points
        else:
            answer.team.score = max(0, answer.team.score + points)  # points can be negative
        answer.team.save()
        
        return Response(AnswerSerializer(answer).data)

