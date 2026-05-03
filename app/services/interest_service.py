from datetime import datetime
from sqlalchemy import update
from app import db
from app.models import UserInterest, Item, UserEntityInterest
from .interest_weights import INTEREST_WEIGHTS
from app.constants import TargetType


def extract_entities_from_target(target):
    if isinstance(target, Item):
        return [{"brand_id": target.brand_id, "category_id": target.category_id}]
    return []


def update_user_interest(
    *,
    user_id,
    target_type,
    target_id,
    action,
    increment_interaction=False,
    entities=None
):
    """
    Update a single UserInterest record + optional entity score.
    Used directly by routes that need fine-grained control.
    For the common case (view/save/click), prefer handle_interaction_interest()
    which fetches UserInterest only once for the combined increment + entity scoring.
    """
    entities = entities or {}
    weight = INTEREST_WEIGHTS.get(action)

    user_interest = UserInterest.query.filter_by(
        user_id=user_id,
        target_type=target_type,
        target_id=target_id
    ).first()

    if not user_interest:
        user_interest = UserInterest(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            interaction_count=0,
            last_interaction_at=datetime.utcnow()
        )
        db.session.add(user_interest)
        db.session.flush()

    if increment_interaction:
        user_interest.interaction_count += 1
        user_interest.last_interaction_at = datetime.utcnow()

    if weight is not None and entities:
        entity_interest = UserEntityInterest.query.filter_by(
            user_interest_id=user_interest.id,
            **entities
        ).first()

        if entity_interest:
            entity_interest.score += weight
        else:
            db.session.add(
                UserEntityInterest(
                    user_interest_id=user_interest.id,
                    score=weight,
                    **entities
                )
            )


def handle_interaction_interest(user, target, action):
    """
    Record a user interaction on a target item, updating both the aggregate
    interaction counter and the entity-level (brand/category) interest scores.

    Fix #18 — Redundant DB Queries Eliminated:
      BEFORE: Called update_user_interest() TWICE with the same (user_id, target_type,
              target_id). Both calls ran UserInterest.query.filter_by(...) independently,
              fetching the SAME row from DB twice — 4 queries per interaction:
                1. SELECT UserInterest (increment call)
                2. INSERT/UPDATE UserInterest
                3. SELECT UserInterest AGAIN (entity call) ← redundant round-trip
                4. SELECT/INSERT UserEntityInterest

      AFTER: Fetches UserInterest ONCE, then performs increment + entity scoring
             on the same in-memory object — 2-3 queries per interaction:
                1. SELECT UserInterest (or INSERT if new)
                2. SELECT/INSERT UserEntityInterest
             Result: ~50% fewer DB queries per interaction event.
    """
    if not user or not target:
        return

    target_type = TargetType.PRODUCT
    weight = INTEREST_WEIGHTS.get(action)

    # ── 1. Fetch or create UserInterest ONCE ──────────────────────────────────
    # Previously this record was fetched independently in two separate
    # update_user_interest() calls — now we fetch it once and reuse it.
    user_interest = UserInterest.query.filter_by(
        user_id=user.id,
        target_type=target_type,
        target_id=target.id
    ).first()

    if not user_interest:
        user_interest = UserInterest(
            user_id=user.id,
            target_type=target_type,
            target_id=target.id,
            interaction_count=0,
            last_interaction_at=datetime.utcnow()
        )
        db.session.add(user_interest)
        db.session.flush()  # Get PK so entity records can reference it

    # ── 2. Increment interaction counter (was a separate update_user_interest call) ──
    user_interest.interaction_count += 1
    user_interest.last_interaction_at = datetime.utcnow()

    # ── 3. Entity-level scoring (brand, category) ──────────────────────────────
    # Process all entities for this target in a single pass using the already-
    # fetched user_interest.id — no additional UserInterest SELECT needed.
    if weight is not None:
        for entity in extract_entities_from_target(target):
            entity_interest = UserEntityInterest.query.filter_by(
                user_interest_id=user_interest.id,
                **entity
            ).first()

            if entity_interest:
                entity_interest.score += weight
            else:
                db.session.add(
                    UserEntityInterest(
                        user_interest_id=user_interest.id,
                        score=weight,
                        **entity
                    )
                )
