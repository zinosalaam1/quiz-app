from django.core.management.base import BaseCommand
from quiz_api.models import Team, AdminCode, GameSession

class Command(BaseCommand):
    help = 'Set up initial quiz data'

    def handle(self, *args, **options):
        # Create teams
        teams_data = [
            {'id': 'team_a', 'name': 'Tour Arcade Team A', 'code': 'ARCADE-A-2024'},
            {'id': 'team_b', 'name': 'Tour Arcade Team B', 'code': 'ARCADE-B-2024'},
            {'id': 'team_c', 'name': 'Tour Arcade Team C', 'code': 'ARCADE-C-2024'},
            {'id': 'team_d', 'name': 'Tour Arcade Team D', 'code': 'ARCADE-D-2024'},
        ]
        
        for team_data in teams_data:
            Team.objects.get_or_create(**team_data)
        
        # Create admin code
        AdminCode.objects.get_or_create(code='QUIZ-MASTER-2024')
        
        # Create initial game session
        GameSession.objects.get_or_create(
            is_active=True,
            defaults={'current_round': 1, 'round_type': 'general'}
        )
        
        self.stdout.write(self.style.SUCCESS('Successfully set up initial data'))