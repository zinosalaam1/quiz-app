import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import GameSession, Team
from .serializers import GameSessionSerializer, TeamSerializer



@database_sync_to_async
def is_valid_active_session(session_id):
    return GameSession.objects.filter(
        id=session_id,
        is_active=True
    ).exists()

class GameConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.user = self.scope["user"]

    # 🔒 Check if session exists AND is active
        valid_session = await is_valid_active_session(self.session_id)

        if not valid_session:
            await self.close()
            return

        self.room_group_name = f"quiz_game_{self.session_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        await self.send_game_state()
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "update_score":
            await self.update_score(data)
            await self.broadcast_game_state()

        elif action == "update_status":
            await self.update_team_status(data)
            await self.broadcast_game_state()

        elif action == "next_question":
            await self.next_question(data)

        elif action == "buzz":
            await self.handle_buzz(data)

        elif action == "timer_tick":
            await self.timer_tick(data)

    # =====================================
    # GAME STATE
    # =====================================

    async def send_game_state(self):
        session = await self.get_session()
        teams = await self.get_teams()

        await self.send(text_data=json.dumps({
            "type": "game_state",
            "session": session,
            "teams": teams
        }))

    async def broadcast_game_state(self):
        session = await self.get_session()
        teams = await self.get_teams()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_state_message",
                "session": session,
                "teams": teams
            }
        )

    async def game_state_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "game_state",
            "session": event["session"],
            "teams": event["teams"]
        }))

    # =====================================
    # NEXT QUESTION
    # =====================================

    async def next_question(self, data):
        question_id = data.get("question_id")
        await self.reset_for_next_question(question_id)
        await self.broadcast_game_state()

    @database_sync_to_async
    def reset_for_next_question(self, question_id):
        session = GameSession.objects.filter(id=self.session_id).first()
        if not session:
            return

        session.current_question_id = question_id
        session.active_team = None
        session.buzzer_locked = False
        session.save()

    # =====================================
    # BUZZER LOGIC
    # =====================================

    async def handle_buzz(self, data):
        team_id = data.get("team_id")
        await self.lock_buzzer(team_id)
        await self.broadcast_game_state()

    @database_sync_to_async
    def lock_buzzer(self, team_id):
        session = GameSession.objects.filter(id=self.session_id).first()
        if not session or session.buzzer_locked:
            return

        team = Team.objects.filter(id=team_id).first()
        if not team:
            return

        session.active_team = team
        session.buzzer_locked = True
        session.save()

    # =====================================
    # DATABASE HELPERS
    # =====================================

    @database_sync_to_async
    def get_session(self):
        session = GameSession.objects.filter(id=self.session_id).first()
        if session:
            return GameSessionSerializer(session).data
        return None

    @database_sync_to_async
    def get_teams(self):
        teams = Team.objects.filter(session_id=self.session_id)
        return TeamSerializer(teams, many=True).data

    @database_sync_to_async
    def update_score(self, data):
        team = Team.objects.filter(id=data.get("team_id")).first()
        if team:
            points = data.get("points", 0)
            team.score = max(0, team.score + points)
            team.save()

    @database_sync_to_async
    def update_team_status(self, data):
        Team.objects.filter(id=data.get("team_id")).update(
            status=data.get("status")
        )

    @database_sync_to_async
    def get_active_session(self):
        return GameSession.objects.filter(is_active=True).first()


    @database_sync_to_async
    def is_valid_active_session(self, session_id):
        return GameSession.objects.filter(
            id=session_id,
            is_active=True
        ).exists()
    # =====================================
    # TIMER
    # =====================================

    async def timer_tick(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "timer_message",
                "seconds": data.get("seconds")
            }
        )

    async def timer_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "timer",
            "seconds": event["seconds"]
        }))