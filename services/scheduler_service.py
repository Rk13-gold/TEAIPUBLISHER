import logging
import json
from datetime import datetime, timedelta

import requests

from PySide6.QtCore import QThread, Signal, QTimer
from core.database import Database
from core.models import Schedule, Bot, Chat

logger = logging.getLogger(__name__)


class SchedulerWorker(QThread):
    log = Signal(str)
    error = Signal(str)
    schedule_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._timer = None

    def run(self):
        self._running = True
        self._timer = QTimer()
        self._timer.timeout.connect(self._check_schedules)
        self._timer.start(30000)
        self.log.emit("Programador iniciado (cada 30s)")
        self.exec()

    def stop(self):
        self._running = False
        if self._timer:
            self._timer.stop()
        self.quit()
        self.wait(2000)

    def _check_schedules(self):
        if not self._running:
            return
        try:
            db = Database()
            session = db.get_session()
            now = datetime.now()
            pending = session.query(Schedule).filter(
                Schedule.status == 'pending',
                Schedule.scheduled_at <= now
            ).all()

            for sched in pending:
                if not self._running:
                    break
                self._send_schedule(session, sched)

            session.commit()
            db.dispose()
            if pending:
                self.schedule_updated.emit()
        except Exception as e:
            self.error.emit(f"Error en programador: {e}")

    def _send_schedule(self, session, sched: Schedule):
        bot = session.query(Bot).filter_by(id=sched.bot_id).first()
        chat = session.query(Chat).filter_by(id=sched.chat_id).first()
        if not bot or not chat:
            sched.status = 'failed'
            self.log.emit(f"Schedule #{sched.id}: bot/chat no encontrado")
            return

        token = bot.token_api
        chat_id = chat.chat_id
        content = sched.content

        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    'chat_id': chat_id,
                    'text': content,
                    'parse_mode': 'HTML',
                },
                timeout=(5, 10)
            )
            data = resp.json()
            if data.get('ok'):
                sched.last_sent_at = datetime.now()
                if sched.repeat:
                    next_time = self._next_repeat(sched)
                    if next_time:
                        new_sched = Schedule(
                            bot_id=sched.bot_id,
                            chat_id=sched.chat_id,
                            content=sched.content,
                            scheduled_at=next_time,
                            repeat=sched.repeat,
                            status='pending',
                            created_at=datetime.now()
                        )
                        session.add(new_sched)
                sched.status = 'sent'
                self.log.emit(f"✅ Programación #{sched.id} enviada a {chat.nombre or chat_id}")
            else:
                sched.status = 'failed'
                desc = data.get('description', 'error desconocido')
                self.log.emit(f"❌ Programación #{sched.id} falló: {desc}")
        except Exception as e:
            sched.status = 'failed'
            self.log.emit(f"❌ Programación #{sched.id} error: {e}")

    def _next_repeat(self, sched: Schedule) -> datetime | None:
        if not sched.scheduled_at:
            return None
        base = sched.last_sent_at or sched.scheduled_at
        if sched.repeat == 'daily':
            return base + timedelta(days=1)
        elif sched.repeat == 'weekly':
            return base + timedelta(weeks=1)
        elif sched.repeat == 'monthly':
            return base + timedelta(days=30)
        return None
