import math
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import MAX_EXCHANGES_PER_COMBINATION
from ..models import ExchangeRequest, Notification, Skill, SkillExchange, User
from .notification_service import notify


def combination(requester_id, receiver_id, offered_skill_id, requested_skill_id):
    if requester_id < receiver_id:
        return requester_id, receiver_id, offered_skill_id, requested_skill_id
    return receiver_id, requester_id, requested_skill_id, offered_skill_id


def remaining_days(exchange: SkillExchange, now=None):
    now = now or datetime.now(timezone.utc)
    end = exchange.end_date
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return max(0, math.ceil((end - now).total_seconds() / 86400))


def exchange_view(exchange: SkillExchange):
    return {
        "id": exchange.id, "requester_id": exchange.requester_id,
        "receiver_id": exchange.receiver_id, "offered_skill_id": exchange.offered_skill_id,
        "requested_skill_id": exchange.requested_skill_id, "duration_days": exchange.duration_days,
        "status": exchange.status, "cycle_number": exchange.cycle_number,
        "start_date": exchange.start_date, "end_date": exchange.end_date,
        "remaining_days": remaining_days(exchange),
    }


def request_view(request: ExchangeRequest):
    return {
        "id": request.id, "requester_id": request.requester_id, "receiver_id": request.receiver_id,
        "offered_skill_id": request.offered_skill_id, "requested_skill_id": request.requested_skill_id,
        "duration_days": request.duration_days, "proposed_by_id": request.proposed_by_id,
        "status": request.status, "exchange_id": request.exchange_id, "created_at": request.created_at,
    }


def create_request(db: Session, user: User, receiver_id, offered_skill_id, requested_skill_id, duration_days):
    if user.id == receiver_id:
        raise HTTPException(400, detail={"detail": "You cannot exchange with yourself", "code": "self_exchange"})
    receiver = db.query(User).filter(User.id == receiver_id, User.is_active.is_(True)).first()
    if receiver is None:
        raise HTTPException(404, detail={"detail": "Receiver not found", "code": "receiver_not_found"})
    offered = db.query(Skill).filter(Skill.id == offered_skill_id, Skill.owner_id == user.id).first()
    requested = db.query(Skill).filter(Skill.id == requested_skill_id, Skill.owner_id == receiver_id).first()
    if offered is None or requested is None:
        raise HTTPException(400, detail={"detail": "Skills must be owned by the correct participants", "code": "invalid_skill_owner"})
    low, high, skill_low, skill_high = combination(user.id, receiver_id, offered.id, requested.id)
    exists = db.query(ExchangeRequest).filter(
        ExchangeRequest.status == "pending",
        ExchangeRequest.user_low_id == low, ExchangeRequest.user_high_id == high,
        ExchangeRequest.skill_of_low_id == skill_low, ExchangeRequest.skill_of_high_id == skill_high,
    ).first()
    active = db.query(SkillExchange).filter(
        SkillExchange.status == "active",
        SkillExchange.user_low_id == low, SkillExchange.user_high_id == high,
        SkillExchange.skill_of_low_id == skill_low, SkillExchange.skill_of_high_id == skill_high,
    ).first()
    if exists or active:
        raise HTTPException(409, detail={"detail": "A matching exchange is already open", "code": "duplicate_exchange"})
    used = db.query(SkillExchange).filter(
        SkillExchange.user_low_id == low, SkillExchange.user_high_id == high,
        SkillExchange.skill_of_low_id == skill_low, SkillExchange.skill_of_high_id == skill_high,
    ).count()
    if used >= MAX_EXCHANGES_PER_COMBINATION:
        raise HTTPException(409, detail={"detail": "This exchange combination has already been used the maximum number of times", "code": "exchange_limit"})
    request = ExchangeRequest(
        requester_id=user.id, receiver_id=receiver_id, offered_skill_id=offered.id,
        requested_skill_id=requested.id, proposed_by_id=user.id, duration_days=duration_days,
        user_low_id=low, user_high_id=high, skill_of_low_id=skill_low, skill_of_high_id=skill_high,
    )
    db.add(request)
    try:
        db.flush()
        notify(db, receiver_id, "exchange_request", f"{user.username} sent you an exchange request.", "exchange_request", request.id)
        db.commit()
        db.refresh(request)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, detail={"detail": "A matching exchange is already open", "code": "duplicate_exchange"})
    return request


def get_participant_request(db: Session, request_id: int, user_id: int):
    row = db.query(ExchangeRequest).filter(ExchangeRequest.id == request_id).first()
    if row is None or user_id not in (row.requester_id, row.receiver_id):
        raise HTTPException(404, detail={"detail": "Request not found", "code": "not_found"})
    return row


def counter_request(db: Session, request: ExchangeRequest, user: User, duration_days: int):
    if request.status != "pending":
        raise HTTPException(409, detail={"detail": "Request is no longer pending", "code": "invalid_transition"})
    if request.proposed_by_id == user.id:
        raise HTTPException(409, detail={"detail": "Only the other participant may counter this proposal", "code": "wrong_exchange_party"})
    request.duration_days = duration_days
    request.proposed_by_id = user.id
    notify(db, request.requester_id if user.id == request.receiver_id else request.receiver_id,
           "exchange_counter", f"{user.username} proposed a duration of {duration_days} days.", "exchange_request", request.id)
    db.commit()
    db.refresh(request)
    return request


def accept_request(db: Session, request: ExchangeRequest, user: User, duration_days=None):
    if request.status != "pending":
        raise HTTPException(409, detail={"detail": "Request is no longer pending", "code": "invalid_transition"})
    if request.proposed_by_id == user.id:
        raise HTTPException(409, detail={"detail": "The other participant must accept this proposal", "code": "wrong_exchange_party"})
    if duration_days is not None and duration_days != request.duration_days:
        raise HTTPException(409, detail={"detail": "Use the counter endpoint to propose a different duration", "code": "duration_mismatch"})
    used = db.query(SkillExchange).filter(
        SkillExchange.user_low_id == request.user_low_id,
        SkillExchange.user_high_id == request.user_high_id,
        SkillExchange.skill_of_low_id == request.skill_of_low_id,
        SkillExchange.skill_of_high_id == request.skill_of_high_id,
    ).count()
    if used >= MAX_EXCHANGES_PER_COMBINATION:
        raise HTTPException(409, detail={"detail": "This exchange combination has already been used the maximum number of times", "code": "exchange_limit"})
    now = datetime.now(timezone.utc)
    exchange = SkillExchange(
        requester_id=request.requester_id, receiver_id=request.receiver_id,
        offered_skill_id=request.offered_skill_id, requested_skill_id=request.requested_skill_id,
        duration_days=request.duration_days, status="active",
        user_low_id=request.user_low_id, user_high_id=request.user_high_id,
        skill_of_low_id=request.skill_of_low_id, skill_of_high_id=request.skill_of_high_id,
        cycle_number=used + 1, start_date=now, end_date=now + timedelta(days=request.duration_days),
    )
    request.status = "accepted"
    db.add(exchange)
    try:
        db.flush()
        request.exchange_id = exchange.id
        notify(db, request.requester_id, "exchange_accepted", f"{user.username} accepted your exchange request.", "skill_exchange", exchange.id)
        for participant_id in (request.requester_id, request.receiver_id):
            notify(db, participant_id, "exchange_started", "Your skill exchange has started.", "skill_exchange", exchange.id)
        db.commit()
        db.refresh(exchange)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, detail={"detail": "This exchange combination has already been used the maximum number of times", "code": "exchange_limit"})
    return exchange


def maybe_notify_near_end(db: Session, exchange: SkillExchange):
    days = remaining_days(exchange)
    if days > 3:
        return
    for participant_id in (exchange.requester_id, exchange.receiver_id):
        exists = db.query(Notification.id).filter(
            Notification.user_id == participant_id,
            Notification.type == "exchange_nearing_completion",
            Notification.related_type == "skill_exchange",
            Notification.related_id == exchange.id,
        ).first()
        if exists is None:
            notify(db, participant_id, "exchange_nearing_completion",
                   f"Your exchange has {days} day(s) remaining.", "skill_exchange", exchange.id)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
