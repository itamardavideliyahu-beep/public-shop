"""
Background tasks for the Public Shop application.
"""

from datetime import datetime

from app import db
from app.models import Listing


def cleanup_expired_listings():
    """
    Mark expired listings as inactive.
    This should be run periodically (e.g., via cron job or scheduled task).
    """
    now = datetime.utcnow()
    expired_listings = Listing.query.filter(
        Listing.expires_at.isnot(None),
        Listing.expires_at < now,
        Listing.status == "active",
    ).all()

    count = 0
    for listing in expired_listings:
        listing.status = "inactive"
        count += 1

    if count > 0:
        db.session.commit()
        return f"Marked {count} expired listing(s) as inactive."
    return "No expired listings found."
