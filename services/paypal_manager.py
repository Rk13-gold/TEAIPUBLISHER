"""
Gestor de pagos PayPal vía API REST.

Métodos:
  - create_order(ebook_id, usuario_id) → approval_url
  - check_pending_payments() → [(venta_id, usuario_id, ebook_id), ...]
"""

import base64
import json
import logging
import time

import requests

from core.database import Database
from core.models import Ebook, Usuario, Venta

logger = logging.getLogger(__name__)


class PayPalManager:
    """API REST de PayPal (sandbox/producción) sin webhooks. Usa polling."""

    TOKEN_URL = "/v1/oauth2/token"
    ORDERS_URL = "/v2/checkout/orders"

    def __init__(self, config):
        self.client_id = getattr(config, "paypal_client_id", "") or ""
        self.client_secret = getattr(config, "paypal_client_secret", "") or ""
        sandbox = getattr(config, "paypal_sandbox", True)
        self.base_url = (
            "https://api-m.sandbox.paypal.com"
            if sandbox
            else "https://api-m.paypal.com"
        )
        self._access_token = None
        self._token_expires_at = 0.0
        self.db = Database()

    # ── Token ──

    def _ensure_token(self):
        """Solicita un token de acceso si está vencido o no existe."""
        if self._access_token and time.time() < self._token_expires_at:
            return

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "PayPal client_id y client_secret no configurados. "
                "Agregalos en config.json (paypal_client_id, paypal_client_secret)."
            )

        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        resp = requests.post(
            f"{self.base_url}{self.TOKEN_URL}",
            headers={
                "Authorization": f"Basic {auth}",
                "Accept": "application/json",
            },
            data={"grant_type": "client_credentials"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        # Renovar 5 minutos antes del vencimiento real
        expires_in = data.get("expires_in", 32400)
        self._token_expires_at = time.time() + expires_in - 300
        logger.info("Token PayPal renovado (vence en %d s).", expires_in)

    # ── Crear orden ──

    def create_order(self, ebook_id: int, usuario_id: int) -> str | None:
        """
        Crea una orden en PayPal y guarda el order_id en la Venta.

        Returns:
            approval_url (str | None): enlace para que el usuario pague.
        """
        self._ensure_token()

        session = self.db.get_session()
        try:
            ebook = session.query(Ebook).get(ebook_id)
            if not ebook:
                logger.error("Ebook %d no encontrado.", ebook_id)
                return None

            usuario = session.query(Usuario).get(usuario_id)
            if not usuario:
                logger.error("Usuario %d no encontrado.", usuario_id)
                return None

            payload = {
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "reference_id": str(ebook_id),
                        "description": ebook.titulo,
                        "amount": {
                            "currency_code": "USD",
                            "value": f"{ebook.precio:.2f}",
                        },
                    }
                ],
                "payment_source": {
                    "paypal": {
                        "experience_context": {
                            "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                            "landing_page": "LOGIN",
                            "user_action": "PAY_NOW",
                            "return_url": "https://example.com/return",
                            "cancel_url": "https://example.com/cancel",
                        }
                    }
                },
            }

            resp = requests.post(
                f"{self.base_url}{self.ORDERS_URL}",
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            order = resp.json()
            order_id = order["id"]

            # Guardar order_id en la Venta
            venta = Venta(
                usuario_id=usuario_id,
                ebook_id=ebook_id,
                metodo_pago="PayPal",
                payment_id=order_id,
                monto=ebook.precio,
                estado="Pendiente",
            )
            session.add(venta)
            session.commit()
            logger.info(
                "Orden PayPal %s creada para ebook %d / usuario %d.",
                order_id, ebook_id, usuario_id,
            )

            # Extraer approval_url
            for link in order.get("links", []):
                if link.get("rel") == "payer-action":
                    return link["href"]

            logger.warning("No se encontró payer-action en la orden %s.", order_id)
            return None

        except requests.RequestException as e:
            logger.error("Error creando orden PayPal: %s", e)
            return None
        except Exception:
            logger.exception("Error inesperado creando orden PayPal")
            return None
        finally:
            session.close()

    # ── Polling ──

    def check_pending_payments(self) -> list[dict]:
        """
        Revisa todas las ventas Pendiente con método PayPal y consulta su
        estado real en PayPal.

        Returns:
            Lista de dicts con ventas que pasaron a Pagado:
            [{"venta_id": int, "usuario_id": int, "ebook_id": int}, ...]
        """
        self._ensure_token()
        completadas: list[dict] = []

        session = self.db.get_session()
        try:
            pendientes = (
                session.query(Venta)
                .filter_by(estado="Pendiente", metodo_pago="PayPal")
                .all()
            )

            for venta in pendientes:
                if not venta.payment_id:
                    continue

                try:
                    resp = requests.get(
                        f"{self.base_url}{self.ORDERS_URL}/{venta.payment_id}",
                        headers={
                            "Authorization": f"Bearer {self._access_token}",
                            "Accept": "application/json",
                        },
                        timeout=15,
                    )
                    if resp.status_code == 404:
                        logger.warning(
                            "Orden %s no encontrada en PayPal, ignorando.",
                            venta.payment_id,
                        )
                        continue
                    resp.raise_for_status()
                    order = resp.json()
                    status = order.get("status", "")

                    if status == "COMPLETED":
                        venta.estado = "Pagado"
                        session.commit()
                        completadas.append({
                            "venta_id": venta.id,
                            "usuario_id": venta.usuario_id,
                            "ebook_id": venta.ebook_id,
                        })
                        logger.info(
                            "Venta %d pagada (PayPal order %s).",
                            venta.id, venta.payment_id,
                        )

                except requests.RequestException as e:
                    logger.error(
                        "Error consultando orden %s: %s", venta.payment_id, e,
                    )

        except Exception:
            logger.exception("Error en check_pending_payments")
        finally:
            session.close()

        return completadas
