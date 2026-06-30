"""WebSocket 实时推送执行状态"""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# 活跃的 WebSocket 连接
active_connections: dict[str, list[WebSocket]] = {}


async def broadcast_execution_update(execution_id: int, data: dict):
    """向所有监听该执行 ID 的客户端推送消息"""
    key = f"execution_{execution_id}"
    message = json.dumps(data, ensure_ascii=False)
    dead = []
    for ws in active_connections.get(key, []):
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        active_connections[key].remove(ws)


@router.websocket("/ws/executions/{execution_id}")
async def websocket_execution(websocket: WebSocket, execution_id: int):
    """客户端连接监听某个执行记录的实时状态"""
    await websocket.accept()
    key = f"execution_{execution_id}"
    active_connections.setdefault(key, []).append(websocket)

    try:
        while True:
            # 保持连接，等待客户端消息（可接收控制指令）
            raw = await websocket.receive_text()
            data = json.loads(raw)
            # 可选：处理客户端发来的控制指令
            if data.get("action") == "stop":
                await websocket.send_text(json.dumps({"event": "stopped", "execution_id": execution_id}))
                break
    except WebSocketDisconnect:
        pass
    finally:
        if key in active_connections and websocket in active_connections[key]:
            active_connections[key].remove(websocket)
