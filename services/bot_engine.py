"""
Motor asíncrono de bots de Telegram usando Telethon.

Lee los bots activos de la DB, inicia un cliente Telethon por cada uno,
y registra event handlers según el tipo de chat (Grupo → Cazador, Privado → Vendedor).
"""

import asyncio
import logging
import os
import time

from telethon import TelegramClient, events, Button

from core.database import Database
from core.models import Bot, Chat, Ebook, Usuario, Venta

logger = logging.getLogger(__name__)


class TelegramEngine:
    """Puente entre la DB y Telegram. Gestiona múltiples bots de forma asíncrona."""

    def __init__(self, config=None):
        self.config = config
        self.db = Database()
        self.clients: dict[int, TelegramClient] = {}
        self._api_id: int | None = None
        self._api_hash: str | None = None

    # ── Inicialización ──

    def _load_telethon_credentials(self):
        if self.config:
            self._api_id = getattr(self.config, 'api_id', None)
            self._api_hash = getattr(self.config, 'api_hash', None)
        if not self._api_id:
            self._api_id = os.environ.get('TELETHON_API_ID')
        if not self._api_hash:
            self._api_hash = os.environ.get('TELETHON_API_HASH')
        if not self._api_id or not self._api_hash:
            raise ValueError(
                "Se requiere api_id y api_hash para usar Telethon.\n"
                "Configúralos en config.json o en las variables de entorno "
                "TELETHON_API_ID y TELETHON_API_HASH."
            )
        if isinstance(self._api_id, str):
            self._api_id = int(self._api_id)

    async def init(self):
        """Inicia un cliente Telethon por cada bot activo en la DB."""
        self._load_telethon_credentials()

        session = self.db.get_session()
        try:
            bots = session.query(Bot).filter_by(activo=True).all()
            if not bots:
                logger.warning("No hay bots activos en la DB.")
                return

            for bot in bots:
                client = TelegramClient(
                    f"session_bot_{bot.id}",
                    self._api_id,
                    self._api_hash,
                )
                await client.start(bot_token=bot.token_api)
                self.clients[bot.id] = client
                me = await client.get_me()
                logger.info(
                    "Bot '%s' iniciado como @%s (id=%d)",
                    bot.nombre, me.username, bot.id,
                )
        finally:
            session.close()

    # ── Listeners ──

    async def start_listeners(self):
        """Registra los event handlers en cada cliente."""
        for bot_id, client in self.clients.items():
            self._register_handlers(bot_id, client)
        logger.info("Listeners activos para %d bot(es).", len(self.clients))

    def _register_handlers(self, bot_id: int, client: TelegramClient):
        @client.on(events.NewMessage)
        async def message_handler(event):
            await self._on_message(bot_id, event)

        @client.on(events.CallbackQuery)
        async def callback_handler(event):
            await self._on_callback(bot_id, event)

    # ── Ruteo de mensajes ──

    async def _on_message(self, bot_id: int, event):
        # Mensajes privados → Bot Vendedor (menú de eBooks)
        if event.is_private:
            await self._handle_private_message(bot_id, event)
            return

        # Mensajes de grupo → buscar en Chats de la DB
        chat_id_str = str(event.chat_id)
        session = self.db.get_session()
        try:
            chat = (
                session.query(Chat)
                .filter_by(bot_id=bot_id, chat_id=chat_id_str, activo=True)
                .first()
            )
            if chat and chat.tipo == "Grupo":
                await self._handle_group_message(bot_id, event, chat)
        finally:
            session.close()

    # ── Lógica Bot Cazador (Grupos) ──

    async def _handle_group_message(self, bot_id: int, event, chat):
        text = (event.text or "").lower()
        keywords = ("perdí", "perdi", "perdido", "perdida", "pierdo")
        if not any(kw in text for kw in keywords):
            return

        # Buscar al Bot Vendedor para obtener su link
        vendedor_link = None
        session = self.db.get_session()
        try:
            vendedor = session.query(Bot).filter(Bot.nombre.ilike("%Vendedor%")).first()
            if vendedor and vendedor.id in self.clients:
                me = await self.clients[vendedor.id].get_me()
                vendedor_link = f"https://t.me/{me.username}"
        except Exception:
            logger.exception("Error al obtener link del Bot Vendedor")
        finally:
            session.close()

        if vendedor_link:
            await event.reply(
                "🤖 ¡No te preocupes! Muchos traders pasan por pérdidas.\n\n"
                f"💬 Chatea con nuestro asesor especializado: {vendedor_link}\n"
                "📚 También tenemos eBooks que te ayudarán a mejorar.",
            )
        else:
            await event.reply(
                "🤖 Entendemos que pasar por pérdidas es difícil. "
                "Pronto tendremos un asesor disponible para ayudarte.",
            )

    # ── Lógica Bot Vendedor (Privado) ──

    async def _handle_private_message(self, bot_id: int, event):
        session = self.db.get_session()
        try:
            ebooks = session.query(Ebook).all()
        finally:
            session.close()

        if not ebooks:
            await event.respond("📚 Por ahora no hay eBooks disponibles.")
            return

        buttons = [
            [Button.inline(f"📘 {e.titulo} — ${e.precio:.2f}", data=f"ebook_{e.id}".encode())]
            for e in ebooks
        ]

        await event.respond(
            "📚 *Bienvenido a la Tienda de eBooks de Trading*\n\n"
            "Seleccioná un libro para ver los detalles:",
            buttons=buttons,
            parse_mode="markdown",
        )

    # ── Callbacks (botones inline) ──

    async def _on_callback(self, bot_id: int, event):
        data = event.data.decode()

        if data.startswith("ebook_"):
            await self._show_ebook_detail(bot_id, event, data)
        elif data.startswith("pay_"):
            await self._process_payment(bot_id, event, data)
        elif data == "back_menu":
            await self._show_ebook_menu(event)

    async def _show_ebook_detail(self, bot_id: int, event, data: str):
        ebook_id = int(data.split("_")[1])

        session = self.db.get_session()
        try:
            ebook = session.query(Ebook).get(ebook_id)
            if not ebook:
                await event.answer("❌ eBook no encontrado.", alert=True)
                return

            sender = await event.get_sender()
            telegram_id = str(sender.id)

            usuario = session.query(Usuario).filter_by(telegram_id=telegram_id).first()
            if not usuario:
                usuario = Usuario(
                    telegram_id=telegram_id,
                    username=sender.username or "",
                    estado="Lead",
                )
                session.add(usuario)
                session.commit()

            msg = (
                f"📘 *{ebook.titulo}*\n\n"
                f"💰 *Precio:* ${ebook.precio:.2f}\n\n"
                "Elegí tu método de pago:"
            )
            buttons = [
                [Button.url("💳 PayPal", "https://paypal.com")],
                [Button.inline("₿ USDT (Crypto)", data=f"pay_usdt_{ebook.id}_{usuario.id}".encode())],
                [Button.inline("⬅️ Volver", data=b"back_menu")],
            ]
            await event.edit(msg, buttons=buttons, parse_mode="markdown")
        finally:
            session.close()

    async def _process_payment(self, bot_id: int, event, data: str):
        parts = data.split("_")
        method = parts[1]
        ebook_id = int(parts[2])
        usuario_id = int(parts[3])

        session = self.db.get_session()
        try:
            ebook = session.query(Ebook).get(ebook_id)
            if not ebook:
                await event.answer("❌ eBook no encontrado.", alert=True)
                return

            payment_id = f"{method}_{ebook_id}_{usuario_id}_{int(time.time())}"

            venta = Venta(
                usuario_id=usuario_id,
                ebook_id=ebook_id,
                metodo_pago=method.upper(),
                payment_id=payment_id,
                monto=ebook.precio,
                estado="Pendiente",
            )
            session.add(venta)
            session.commit()

            await event.edit(
                f"📋 *Resumen de Compra*\n\n"
                f"📘 *{ebook.titulo}*\n"
                f"💰 ${ebook.precio:.2f}\n"
                f"💳 {method.upper()}\n"
                f"🆔 ID: `{payment_id}`\n\n"
                "⏳ El pago está *Pendiente*. Te avisaremos cuando se confirme.\n\n"
                "Gracias por tu interés 🙌",
                parse_mode="markdown",
            )
        finally:
            session.close()

    async def _show_ebook_menu(self, event):
        session = self.db.get_session()
        try:
            ebooks = session.query(Ebook).all()
        finally:
            session.close()

        buttons = [
            [Button.inline(f"📘 {e.titulo} — ${e.precio:.2f}", data=f"ebook_{e.id}".encode())]
            for e in ebooks
        ]
        await event.edit(
            "📚 *Bienvenido a la Tienda de eBooks de Trading*\n\n"
            "Seleccioná un libro:",
            buttons=buttons,
            parse_mode="markdown",
        )

    # ── Ejecución ──

    async def run(self):
        """Ejecuta todos los clientes en un mismo bucle asyncio."""
        if not self.clients:
            logger.warning("No hay clientes para ejecutar.")
            return

        logger.info("Ejecutando %d bot(es) concurrentemente...", len(self.clients))
        await asyncio.gather(
            *(client.run_until_disconnected() for client in self.clients.values())
        )

    async def stop(self):
        """Desconecta todos los clientes."""
        for bot_id, client in list(self.clients.items()):
            await client.disconnect()
        self.clients.clear()
        logger.info("Todos los bots detenidos.")
