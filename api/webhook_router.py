"""
Cobo Webhook Endpoint'i
=======================
Cobo platformundan gelen POST bildirimlerini karşılar.
Hızlıca 200 OK döner ve asıl işlemi BackgroundTasks'a atar.

Asıl işleme mantığı: workers/webhook_processor.py
"""

import logging
from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import Response
from workers.webhook_processor import process_cobo_notification

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Webhook"])


@router.post("/cobo/callback")
async def cobo_callback(request: Request, background_tasks: BackgroundTasks):
    """
    Cobo webhook endpoint'i.
    Hızla 200 OK döner, işlemi background'a atar.
    """
    try:
        # JSON verisini hemen oku
        data = await request.json()
        logger.info(f"📥 Webhook alındı (Queue'ya eklendi): {data.get('event_id', 'unknown')}")

        # Ağır işlemi arka plana at
        background_tasks.add_task(process_cobo_notification, data)

        # Cobo'ya hemen "ok" (plain text) dön
        return Response(content="ok", media_type="text/plain")

    except Exception as e:
        logger.error(f"❌ Webhook karşılama hatası: {e}")
        # Hata olsa bile 200 dönelim ki Cobo sürekli retry yapmasın
        return Response(content="ok", media_type="text/plain")
