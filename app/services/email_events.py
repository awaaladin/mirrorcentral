"""Sends Mirror's event emails (welcome, payment receipt) without touching the code that creates users
or confirms payments: it listens to the database instead.

An email is queued when the row is written and sent only after the transaction COMMITS; a rollback
discards the queue, so nobody gets a receipt for a payment that did not stick.
"""
from __future__ import annotations

import logging

from sqlalchemy import event, inspect, select
from sqlalchemy.orm import Session, object_session

from app.models.enums import PaymentStatus
from app.models.payment import Payment
from app.models.user import User
from app.services import mailer

logger = logging.getLogger(__name__)
_QUEUE_KEY = "pending_emails"


def _queue(target, job) -> None:
    session = object_session(target)
    if session is not None:
        session.info.setdefault(_QUEUE_KEY, []).append(job)


@event.listens_for(User, "after_insert")
def _welcome(mapper, connection, user: User) -> None:
    email = user.email
    _queue(user, lambda: mailer.send_welcome(email))


def _paid(mapper, connection, payment: Payment) -> None:
    state = inspect(payment)
    just_paid = payment.status == PaymentStatus.SUCCESS and (
        state.transient or state.pending or state.attrs.status.history.has_changes()
    )
    if not just_paid:
        return
    email = connection.execute(select(User.__table__.c.email).where(User.__table__.c.id == payment.user_id)).scalar()
    if email:
        amount, reference = payment.amount_kobo, payment.reference
        _queue(payment, lambda: mailer.send_receipt(email, amount, reference))


event.listen(Payment, "after_insert", _paid)
event.listen(Payment, "after_update", _paid)


@event.listens_for(Session, "after_commit")
def _send_after_commit(session: Session) -> None:
    for job in session.info.pop(_QUEUE_KEY, []):
        try:
            job()
        except Exception:  # noqa: BLE001
            logger.exception("An email job failed")


@event.listens_for(Session, "after_rollback")
def _discard_on_rollback(session: Session) -> None:
    session.info.pop(_QUEUE_KEY, None)
