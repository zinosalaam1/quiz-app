from django.core.management.base import BaseCommand
from quiz_api.models import GameSession, Team

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        session = GameSession.objects.create(name="Tour Arcade Event", is_active=True)

        for name in ["Team A", "Team B", "Team C", "Team D"]:
            Team.objects.create(name=name, session=session)

        self.stdout.write(self.style.SUCCESS("Game setup complete"))