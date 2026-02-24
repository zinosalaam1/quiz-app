import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import GameSession, Team
from .serializers import GameSessionSerializer, TeamSerializer

class GameConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time game updates"""
    
    async def connect(self):
        self.room_group_name = 'quiz_game'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current state on connect
        await self.send_game_state()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'update_score':
            await self.update_score(data)
        elif action == 'update_status':
            await self.update_team_status(data)
        elif action == 'timer_tick':
            await self.timer_tick(data)
        elif action == 'game_state_change':
            await self.broadcast_game_state()
    
    async def send_game_state(self):
        """Send current game state to client"""
        session = await self.get_current_session()
        teams = await self.get_all_teams()
        
        if session:
            await self.send(text_data=json.dumps({
                'type': 'game_state',
                'session': session,
                'teams': teams
            }))
    
    async def broadcast_game_state(self):
        """Broadcast game state to all clients"""
        session = await self.get_current_session()
        teams = await self.get_all_teams()
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_state_message',
                'session': session,
                'teams': teams
            }
        )
    
    async def game_state_message(self, event):
        """Send game state message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'session': event['session'],
            'teams': event['teams']
        }))
    
    @database_sync_to_async
    def get_current_session(self):
        session = GameSession.objects.filter(is_active=True).first()
        if session:
            return GameSessionSerializer(session).data
        return None
    
    @database_sync_to_async
    def get_all_teams(self):
        teams = Team.objects.all()
        return TeamSerializer(teams, many=True).data
    
    @database_sync_to_async
    def update_score(self, data):
        team_id = data.get('team_id')
        points = data.get('points', 0)
        team = Team.objects.get(id=team_id)
        team.score = max(0, team.score + points)
        team.save()
    
    @database_sync_to_async
    def update_team_status(self, data):
        team_id = data.get('team_id')
        status = data.get('status')
        Team.objects.filter(id=team_id).update(status=status)
    
    async def timer_tick(self, data):
        """Broadcast timer tick"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'timer_message',
                'seconds': data.get('seconds')
            }
        )
    
    async def timer_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'timer',
            'seconds': event['seconds']
        }))