# app/domains/chat/websocket_manager.py
import logging
from collections import defaultdict
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def init(self):
        # نستعملو defaultdict(list) باش الكود يكون Clean أوتوماتيكيا يكريي List كي يجي يوزر جديد
        # key = user_id, value = list of WebSockets (multiple devices for the same user)
        self.active_connections: Dict[int, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, user_id: int):
        """يتم استدعاؤها لما تطبيق Flutter يطلب فتح اتصال WebSocket"""
        await websocket.accept()
        
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected. Total devices: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int): 
        """Offline handling and Memory Leak prevention"""
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
                
                # إذا خرج من كامل الأجهزة (all devices) نحذفوه من القاموس (Memory leak prevention)
                if len(self.active_connections[user_id]) == 0:
                    del self.active_connections[user_id]
                
                logger.info(f"User {user_id} disconnected.")

            except ValueError:
                # ws is sensitive to network drops. 
                # إذا تقطعت الكونيكسيون فجأة في الـ Mobile وما لقيناش الـ socket، نتجاهلو الخطأ
                pass

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)

    async def broadcast_to_group(self, message: dict, group_members_ids: List[int]):
        """يبعث رسالة لكامل أعضاء الـ Group باستعمال IDs تاعهم"""
        for user_id in group_members_ids:
            await self.send_personal_message(message, user_id)

# Une seule instance تسيّر Online users في كامل الـ App
manager = ConnectionManager()