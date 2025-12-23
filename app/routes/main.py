import os
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    abort,
)
from flask_login import login_required, current_user

from app import db
from app.models import (
    Post,
    Listing,
    User,
    Conversation,
    Message,
)
from app.utils import save_uploaded_image, sanitize_input
from app.forms import PostForm, ListingForm, SearchForm
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


main_bp = Blueprint("main", __name__)

# Central definition of listing categories:
# internal value, display label
LISTING_CATEGORIES = [
    ("real_estate", "Real estate"),
    ("cars", "Cars"),
    ("electronics", "Electronics"),
    ("furniture", "Furniture"),
    ("pets", "Pets"),
    ("hobby", "Hobby"),
    ("else", "Else"),
]

# Available regions
REGIONS = [
    ("israel", "Israel"),
]


@main_bp.route("/")
def index():
    """
    Home page: show marketplace offers.

    Filter options:
    - 'following': Show only offers from users the current user follows (if authenticated)
    - 'all': Show all offers from all users (default)
    """
    from flask import request

    category_filter = request.args.get("category", "").strip() or None
    region_filter = request.args.get("region", "").strip() or None
    view_filter = request.args.get("view", "all").strip()  # 'all' or 'following'
    page = request.args.get("page", 1, type=int)

    # Filter out expired listings
    now = datetime.utcnow()

    # Offers (listings) with pagination
    query = Listing.query.filter_by(status="active")

    # Apply view filter
    if current_user.is_authenticated and view_filter == "following":
        # IDs of followed users + the current user
        followed_ids = [u.id for u in current_user.followed]
        followed_ids.append(current_user.id)
        query = query.filter(Listing.seller_id.in_(followed_ids))
    # If view_filter is 'all' or user not authenticated, show all listings (already set above)

    # Filter out expired listings
    query = query.filter((Listing.expires_at.is_(None)) | (Listing.expires_at > now))

    # Optional category filter for offers
    if category_filter:
        query = query.filter_by(category=category_filter)

    # Optional region filter for offers
    if region_filter:
        # Join with User to filter by region
        query = query.join(User).filter(User.region == region_filter)

    listings_pagination = query.order_by(Listing.created_at.desc()).paginate(
        page=page, per_page=current_app.config["LISTINGS_PER_PAGE"], error_out=False
    )
    listings = listings_pagination.items

    return render_template(
        "index.html",
        listings=listings,
        listings_pagination=listings_pagination,
        current_category=category_filter,
        current_region=region_filter,
        current_view=view_filter if current_user.is_authenticated else "all",
        categories=LISTING_CATEGORIES,
        regions=REGIONS,
    )


@main_bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    """
    Dashboard for the currently authenticated user.

    - On GET:
        Show a form to create a new story and a new offer,
        plus lists of the user's stories and offers.
    - On POST:
        Handle either story creation or offer creation,
        depending on the hidden 'form_type' field.
    """
    if request.method == "POST":
        form_type = request.form.get("form_type")

        # --- Create a new offer (listing) with optional image upload ---
        if form_type == "listing":
            title = sanitize_input(request.form.get("title", ""), max_length=120)
            description = sanitize_input(
                request.form.get("description", ""), max_length=2000
            )
            price_raw = request.form.get("price", "").strip()
            category_value = request.form.get("category", "").strip()
            image_file = request.files.get("image")

            errors = []

            if not title:
                errors.append("Title is required for an offer.")
            elif len(title) < 3:
                errors.append("Title must be at least 3 characters long.")
            elif len(title) > 120:
                errors.append("Title must be no more than 120 characters.")

            # Check if this is a free listing (giveaway) - check this before price validation
            is_free = (
                request.form.get("is_free") == "on"
                or request.form.get("is_free") == "true"
            )

            # Price validation - only required if not a free listing
            price = 0.0
            if is_free:
                # Free listings don't need price validation
                price = 0.0
            else:
                if not price_raw:
                    errors.append("Price is required.")
                else:
                    try:
                        price = float(price_raw)
                        if price <= 0:
                            errors.append("Price must be a positive number.")
                        elif price > 999999999:
                            errors.append("Price is too large.")
                    except ValueError:
                        errors.append("Price must be a valid number.")

            # Validate category
            valid_category_values = {value for value, _ in LISTING_CATEGORIES}
            if not category_value:
                errors.append("Category is required.")
            elif category_value not in valid_category_values:
                errors.append("Invalid category selected.")

            image_filename = None

            # Handle optional image upload with validation
            if image_file and image_file.filename:
                image_filename = save_uploaded_image(
                    image_file,
                    subdirectory="listings",
                    prefix=f"listing_{current_user.id}",
                )
                if not image_filename:
                    errors.append(
                        "Failed to upload image. Please check the file type and size."
                    )

            # Handle expiration date
            expires_at = None
            expires_days_raw = request.form.get("expires_days", "").strip()
            if expires_days_raw:
                try:
                    expires_days = int(expires_days_raw)
                    if expires_days < 1:
                        errors.append("Expiration days must be at least 1.")
                    elif expires_days > 365:
                        errors.append(
                            "Expiration cannot be more than 1 year (365 days)."
                        )
                    else:
                        from datetime import timedelta

                        expires_at = datetime.utcnow() + timedelta(days=expires_days)
                except ValueError:
                    errors.append("Expiration days must be a valid number.")
            else:
                # Default to 1 year if not specified
                from datetime import timedelta

                expires_at = datetime.utcnow() + timedelta(days=365)

            if errors:
                for msg in errors:
                    flash(msg, "error")
            else:
                try:
                    listing = Listing(
                        seller=current_user,
                        title=title,
                        description=description or None,
                        price=(
                            price if not is_free else 0.0
                        ),  # Free listings have price 0
                        status="active",
                        image_filename=image_filename,
                        category=category_value,
                        expires_at=expires_at,
                        is_free=is_free,
                    )
                    db.session.add(listing)
                    db.session.commit()

                    flash("Offer created successfully.", "success")
                    return redirect(url_for("main.dashboard"))
                except Exception as e:
                    current_app.logger.error(f"Error creating listing: {str(e)}")
                    db.session.rollback()
                    flash(
                        "An error occurred while creating your offer. Please try again.",
                        "error",
                    )

        else:
            # Unknown or missing form_type
            flash("Unknown form type submitted.", "error")

    # On GET (or if there were validation errors), show current data
    user_listings = (
        Listing.query.filter_by(seller_id=current_user.id)
        .order_by(Listing.created_at.desc())
        .all()
    )

    return render_template(
        "dashboard.html",
        user_listings=user_listings,
        listing_categories=LISTING_CATEGORIES,
    )


@main_bp.route("/listing/<int:listing_id>")
def listing_detail(listing_id: int):
    """
    Show a detailed page for a single offer.
    """
    listing = Listing.query.get_or_404(listing_id)

    # Check if listing is expired
    if listing.expires_at and listing.expires_at < datetime.utcnow():
        listing.status = "inactive"
        db.session.commit()
        flash("This offer has expired.", "warning")

    return render_template("listing_detail.html", listing=listing)


@main_bp.route("/listing/<int:listing_id>/interest", methods=["POST"])
@login_required
def show_interest(listing_id: int):
    """
    Show interest in a listing: start a conversation and send email notification.
    """
    listing = Listing.query.get_or_404(listing_id)

    if current_user.id == listing.seller_id:
        flash("You cannot show interest in your own listing.", "error")
        return redirect(url_for("main.listing_detail", listing_id=listing_id))

    # Check if conversation already exists
    existing_conversation = Conversation.query.filter_by(
        listing_id=listing_id,
        buyer_id=current_user.id,
        seller_id=listing.seller_id,
    ).first()

    if existing_conversation:
        # Conversation already exists, just redirect to it
        flash("You already have a conversation about this listing.", "info")
        return redirect(
            url_for(
                "main.conversation_detail", conversation_id=existing_conversation.id
            )
        )

    # Create new conversation
    try:
        conversation = Conversation(
            listing=listing,
            buyer=current_user,
            seller=listing.seller,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(conversation)

        # Send initial message
        initial_message = Message(
            conversation=conversation,
            sender=current_user,
            content=f"I'm interested in your listing: {listing.title}",
            created_at=datetime.utcnow(),
            is_read=False,
        )
        db.session.add(initial_message)
        db.session.commit()

        # Send email notification to seller
        try:
            from app.utils import send_email_notification

            send_email_notification(
                to_email=listing.seller.email,
                subject=f"New Interest in Your Listing: {listing.title}",
                message=f"{current_user.display_name} ({current_user.email}) is interested in your listing '{listing.title}'. Check your messages to start the conversation.",
            )
        except Exception as e:
            current_app.logger.error(f"Failed to send email notification: {str(e)}")
            # Don't fail the request if email fails

        flash(
            "Interest shown! A conversation has been started with the seller.",
            "success",
        )
        return redirect(
            url_for("main.conversation_detail", conversation_id=conversation.id)
        )
    except Exception as e:
        current_app.logger.error(f"Error showing interest: {str(e)}")
        db.session.rollback()
        flash("An error occurred. Please try again.", "error")
        return redirect(url_for("main.listing_detail", listing_id=listing_id))


# ==========================
# Messaging (conversations)
# ==========================
@main_bp.route("/conversations")
@login_required
def conversations_inbox():
    """
    Inbox for the current user.

    Renders a HTML page that lists all conversations where the
    current user is either the buyer or the seller.
    """
    from flask import request

    page = request.args.get("page", 1, type=int)

    # Base query for conversations
    conversations_query = Conversation.query.filter(
        (Conversation.buyer_id == current_user.id)
        | (Conversation.seller_id == current_user.id)
    ).order_by(Conversation.updated_at.desc())

    # Paginate conversations
    pagination = conversations_query.paginate(
        page=page,
        per_page=current_app.config["CONVERSATIONS_PER_PAGE"],
        error_out=False,
    )
    conversations = pagination.items

    # Get last message for each conversation
    conversations_with_last_message = []
    for conv in conversations:
        last_message = (
            Message.query.filter_by(conversation_id=conv.id)
            .order_by(Message.created_at.desc())
            .first()
        )
        conversations_with_last_message.append(
            {"conversation": conv, "last_message": last_message}
        )

    return render_template(
        "conversations.html",
        conversations_data=conversations_with_last_message,
        pagination=pagination,
    )


@main_bp.route("/conversations/start/<int:listing_id>", methods=["POST"])
@login_required
def start_conversation(listing_id: int):
    """
    Start (or reuse) a conversation between the current user (buyer)
    and the listing's seller, about the given listing.
    """
    listing = Listing.query.get_or_404(listing_id)

    if listing.seller_id == current_user.id:
        flash("You cannot start a conversation with yourself as the seller.", "error")
        return redirect(url_for("main.listing_detail", listing_id=listing.id))

    # Try to find an existing conversation for this buyer+seller+listing
    conversation = Conversation.query.filter_by(
        buyer_id=current_user.id,
        seller_id=listing.seller_id,
        listing_id=listing.id,
    ).first()

    if conversation is None:
        conversation = Conversation(
            buyer=current_user,
            seller=listing.seller,
            listing=listing,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(conversation)
        db.session.commit()
        flash("Conversation started with the seller.", "success")
    else:
        flash("Opened existing conversation with the seller.", "info")

    return redirect(
        url_for("main.conversation_detail", conversation_id=conversation.id)
    )


@main_bp.route("/conversations/start-with-user/<int:user_id>", methods=["POST"])
@login_required
def start_conversation_with_user(user_id: int):
    """
    Start (or reuse) a conversation between the current user and another user.
    This is for general conversations not tied to a specific listing.
    """
    other_user = User.query.get_or_404(user_id)

    if other_user.id == current_user.id:
        flash("You cannot start a conversation with yourself.", "error")
        return redirect(url_for("main.profile", user_id=user_id))

    # Try to find an existing conversation between these two users (without a listing)
    # Check both directions: current_user as buyer or as seller
    conversation = Conversation.query.filter(
        (
            (
                (Conversation.buyer_id == current_user.id)
                & (Conversation.seller_id == other_user.id)
            )
            | (
                (Conversation.buyer_id == other_user.id)
                & (Conversation.seller_id == current_user.id)
            )
        ),
        Conversation.listing_id.is_(None),  # General conversation, not about a listing
    ).first()

    if conversation is None:
        # Create new conversation
        # Use current_user as buyer and other_user as seller for consistency
        conversation = Conversation(
            buyer=current_user,
            seller=other_user,
            listing=None,  # No listing for general conversations
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(conversation)
        db.session.commit()
        flash(f"Conversation started with {other_user.display_name}.", "success")
    else:
        flash(f"Opened existing conversation with {other_user.display_name}.", "info")

    return redirect(
        url_for("main.conversation_detail", conversation_id=conversation.id)
    )


@main_bp.route("/conversations/<int:conversation_id>")
@login_required
def conversation_detail(conversation_id: int):
    """
    Show a single conversation, with all messages, in a HTML template.
    """
    conversation = Conversation.query.get_or_404(conversation_id)

    if current_user.id not in (conversation.buyer_id, conversation.seller_id):
        abort(403)

    messages = (
        Message.query.filter_by(conversation_id=conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    if current_user.id == conversation.buyer_id:
        other = conversation.seller
    else:
        other = conversation.buyer

    return render_template(
        "conversation_detail.html",
        conversation=conversation,
        messages=messages,
        other_user=other,
    )


@main_bp.route("/conversations/<int:conversation_id>/message", methods=["POST"])
@login_required
def send_message(conversation_id: int):
    """
    Send a new message in an existing conversation.
    Supports both regular form submission and AJAX requests.
    """
    conversation = Conversation.query.get_or_404(conversation_id)

    if current_user.id not in (conversation.buyer_id, conversation.seller_id):
        abort(403)

    content = sanitize_input(request.form.get("content", ""), max_length=2000)

    if not content:
        if (
            request.is_json
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        ):
            from flask import jsonify

            return (
                jsonify(
                    {"success": False, "error": "Message content cannot be empty."}
                ),
                400,
            )
        flash("Message content cannot be empty.", "error")
        return redirect(
            url_for("main.conversation_detail", conversation_id=conversation.id)
        )
    elif len(content) < 1:
        if (
            request.is_json
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        ):
            from flask import jsonify

            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Message content must be at least 1 character long.",
                    }
                ),
                400,
            )
        flash("Message content must be at least 1 character long.", "error")
        return redirect(
            url_for("main.conversation_detail", conversation_id=conversation.id)
        )

    try:
        message = Message(
            conversation=conversation,
            sender=current_user,
            content=content,
            created_at=datetime.utcnow(),
            is_read=False,
        )

        conversation.updated_at = datetime.utcnow()

        db.session.add(message)
        db.session.commit()

        # Determine recipient and send email notification
        recipient = (
            conversation.seller
            if conversation.buyer_id == current_user.id
            else conversation.buyer
        )

        # Emit SocketIO event for real-time updates
        try:
            from app import socketio

            socketio.emit(
                "new_message",
                {
                    "conversation_id": conversation_id,
                    "message_id": message.id,
                    "sender_id": message.sender_id,
                    "sender_name": current_user.display_name,
                    "content": message.content,
                    "created_at": message.created_at.strftime("%d %b %H:%M"),
                },
                room=f"conversation_{conversation_id}",
            )
        except Exception as e:
            current_app.logger.error(f"Failed to emit SocketIO event: {str(e)}")

        # Send email notification to recipient
        try:
            from app.utils import send_email_notification

            send_email_notification(
                to_email=recipient.email,
                subject=f"New message from {current_user.display_name}",
                message=f"You have received a new message from {current_user.display_name} ({current_user.email}):\n\n{content}\n\nView your messages: {request.url_root}conversations/{conversation.id}",
            )
        except Exception as e:
            current_app.logger.error(f"Failed to send email notification: {str(e)}")

        # If AJAX request, return JSON
        if (
            request.is_json
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        ):
            from flask import jsonify

            return (
                jsonify(
                    {
                        "success": True,
                        "message": {
                            "id": message.id,
                            "content": message.content,
                            "sender_id": message.sender_id,
                            "sender_name": message.sender.display_name,
                            "created_at": message.created_at.strftime("%d %b %H:%M"),
                        },
                    }
                ),
                200,
            )

        flash("Message sent.", "success")
        return redirect(
            url_for("main.conversation_detail", conversation_id=conversation.id)
        )
    except Exception as e:
        current_app.logger.error(f"Error sending message: {str(e)}")
        db.session.rollback()
        if (
            request.is_json
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        ):
            from flask import jsonify

            return (
                jsonify(
                    {
                        "success": False,
                        "error": "An error occurred while sending your message.",
                    }
                ),
                500,
            )
        flash(
            "An error occurred while sending your message. Please try again.", "error"
        )
        return redirect(
            url_for("main.conversation_detail", conversation_id=conversation.id)
        )


@main_bp.route("/conversations/<int:conversation_id>/messages")
@login_required
def get_messages(conversation_id: int):
    """
    API endpoint to get messages for a conversation.
    Used for live chat polling.
    """
    conversation = Conversation.query.get_or_404(conversation_id)

    if current_user.id not in (conversation.buyer_id, conversation.seller_id):
        abort(403)

    # Get last message ID from query parameter (for polling)
    last_message_id = request.args.get("last_id", type=int, default=0)

    # Get messages after the last known message
    messages_query = Message.query.filter_by(conversation_id=conversation.id)
    if last_message_id:
        messages_query = messages_query.filter(Message.id > last_message_id)

    messages = messages_query.order_by(Message.created_at.asc()).all()

    # Determine other user
    if current_user.id == conversation.buyer_id:
        other_user = conversation.seller
    else:
        other_user = conversation.buyer

    messages_data = []
    for msg in messages:
        messages_data.append(
            {
                "id": msg.id,
                "content": msg.content,
                "sender_id": msg.sender_id,
                "sender_name": msg.sender.display_name,
                "is_own": msg.sender_id == current_user.id,
                "created_at": msg.created_at.strftime("%d %b %H:%M"),
            }
        )

    return {"messages": messages_data}, 200


# ==========================
# Profiles and following
# ==========================


@main_bp.route("/profile/<int:user_id>")
def profile(user_id: int):
    """
    Public profile page for a user.
    Shows basic profile info plus their offers.
    """
    user = User.query.get_or_404(user_id)

    listings = (
        Listing.query.filter_by(seller_id=user.id, status="active")
        .order_by(Listing.created_at.desc())
        .all()
    )

    return render_template(
        "profile.html",
        user=user,
        listings=listings,
    )


@main_bp.route("/follow/<int:user_id>", methods=["POST"])
@login_required
def follow(user_id: int):
    """
    Current user follows another user.
    """
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot follow yourself.", "error")
    elif current_user.is_following(user):
        flash("You are already following this user.", "info")
    else:
        current_user.follow(user)
        db.session.commit()
        flash("You are now following this user.", "success")

    # Redirect back to the page that initiated the follow
    next_page = request.args.get("next") or request.referrer
    if next_page and next_page.startswith("/"):
        return redirect(next_page)
    return redirect(url_for("main.profile", user_id=user.id))


@main_bp.route("/unfollow/<int:user_id>", methods=["POST"])
@login_required
def unfollow(user_id: int):
    """
    Current user unfollows another user.
    """
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot unfollow yourself.", "error")
    elif not current_user.is_following(user):
        flash("You are not following this user.", "info")
    else:
        current_user.unfollow(user)
        db.session.commit()
        flash("You have unfollowed this user.", "success")

    # Redirect back to the page that initiated the unfollow
    next_page = request.args.get("next") or request.referrer
    if next_page and next_page.startswith("/"):
        return redirect(next_page)
    # Check if coming from search page
    if request.referrer and "search" in request.referrer:
        return redirect(request.referrer)
    return redirect(url_for("main.profile", user_id=user.id))


@main_bp.route("/search")
@login_required
def search():
    """Unified search page with tabs for users and listings."""
    from app.forms import SearchForm

    query = request.args.get("q", "").strip()
    form = SearchForm(request.args)
    form.category.choices = [("", "All Categories")] + LISTING_CATEGORIES

    # Get users if query provided
    users = []
    users_pagination = None
    if query:
        from sqlalchemy import func

        search_pattern = f"%{query}%"
        users_query = (
            User.query.filter(
                (func.lower(User.username).like(func.lower(search_pattern)))
                | (func.lower(User.display_name).like(func.lower(search_pattern)))
            )
            .filter(User.id != current_user.id)
            .order_by(User.username.asc() if User.username else User.display_name.asc())
        )
        page = request.args.get("page", 1, type=int)
        users_pagination = users_query.paginate(page=page, per_page=20, error_out=False)
        users = users_pagination.items

    # Get listings if form submitted
    listings = []
    listings_pagination = None
    if form.query.data or form.category.data:
        now = datetime.utcnow()
        listings_query = Listing.query.filter(
            Listing.status == "active",
            (Listing.expires_at.is_(None)) | (Listing.expires_at > now),
        )

        if form.query.data:
            search_term = f"%{form.query.data}%"
            listings_query = listings_query.filter(
                (Listing.title.ilike(search_term))
                | (Listing.description.ilike(search_term))
            )

        if form.category.data:
            listings_query = listings_query.filter_by(category=form.category.data)

        page = request.args.get("page", 1, type=int)
        listings_pagination = listings_query.order_by(
            Listing.created_at.desc()
        ).paginate(
            page=page, per_page=current_app.config["LISTINGS_PER_PAGE"], error_out=False
        )
        listings = listings_pagination.items

    return render_template(
        "search.html",
        users=users,
        listings=listings,
        query=query,
        form=form,
        pagination=users_pagination,
        categories=LISTING_CATEGORIES,
    )


@main_bp.route("/search/users")
def search_users():
    """
    Search for users by username (or display_name as fallback).
    Returns a page with search results showing users that can be followed.
    """
    query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    if query:
        # Search users by username (case-insensitive, partial match)
        # Use func.lower for SQLite compatibility
        from sqlalchemy import func

        search_pattern = f"%{query}%"
        users_query = (
            User.query.filter(
                (func.lower(User.username).like(func.lower(search_pattern)))
                | (func.lower(User.display_name).like(func.lower(search_pattern)))
            )
            .filter(
                User.id != current_user.id if current_user.is_authenticated else True
            )  # Exclude current user if authenticated
            .order_by(User.username.asc() if User.username else User.display_name.asc())
        )

        users_pagination = users_query.paginate(page=page, per_page=20, error_out=False)
        users = users_pagination.items
    else:
        users = []
        users_pagination = None

    return render_template(
        "search.html",
        users=users,
        user_query=query,
        user_pagination=users_pagination,
        categories=LISTING_CATEGORIES,
    )


@main_bp.route("/search/listings")
def search_listings():
    """
    Search listings by title, description, or category.
    """
    form = SearchForm(request.args)
    # Set category choices
    form.category.choices = [("", "All Categories")] + LISTING_CATEGORIES

    page = request.args.get("page", 1, type=int)
    now = datetime.utcnow()

    query = Listing.query.filter(
        Listing.status == "active",
        (Listing.expires_at.is_(None)) | (Listing.expires_at > now),
    )

    if form.query.data:
        search_term = f"%{form.query.data}%"
        query = query.filter(
            (Listing.title.ilike(search_term))
            | (Listing.description.ilike(search_term))
        )

    if form.category.data:
        query = query.filter_by(category=form.category.data)

    if form.min_price.data:
        query = query.filter(Listing.price >= form.min_price.data)

    if form.max_price.data:
        query = query.filter(Listing.price <= form.max_price.data)

    listings_pagination = query.order_by(Listing.created_at.desc()).paginate(
        page=page, per_page=current_app.config["LISTINGS_PER_PAGE"], error_out=False
    )

    return render_template(
        "search_listings.html",
        form=form,
        listings=listings_pagination.items,
        pagination=listings_pagination,
        categories=LISTING_CATEGORIES,
    )


@main_bp.route("/health")
def health_check():
    """
    Health check endpoint for monitoring.
    """
    from flask import jsonify

    try:
        # Check database connection
        db.session.execute(db.text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return jsonify(
        {
            "status": "ok" if db_status == "healthy" else "degraded",
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    ), (200 if db_status == "healthy" else 503)


@main_bp.route("/following")
@login_required
def following():
    """
    Page that shows all users the current user is following.
    Visible only to the authenticated user.
    """
    followed_users = current_user.followed.order_by(
        User.username.asc() if User.username else User.display_name.asc()
    ).all()
    return render_template("following.html", users=followed_users)


@main_bp.route("/settings/profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    """
    Settings page for the current user to edit their profile.
    Allows changing display name, bio, and avatar image.
    """
    if request.method == "POST":
        display_name = sanitize_input(
            request.form.get("display_name", ""), max_length=80
        )
        bio = sanitize_input(request.form.get("bio", ""), max_length=500)
        avatar_file = request.files.get("avatar")

        errors = []

        if not display_name:
            errors.append("Display name is required.")
        elif len(display_name) < 2:
            errors.append("Display name must be at least 2 characters long.")
        elif len(display_name) > 80:
            errors.append("Display name must be no more than 80 characters.")

        avatar_filename = current_user.avatar_filename

        if avatar_file and avatar_file.filename:
            avatar_filename = save_uploaded_image(
                avatar_file, subdirectory="avatars", prefix=f"avatar_{current_user.id}"
            )
            if not avatar_filename:
                errors.append(
                    "Failed to upload avatar. Please check the file type and size."
                )

        if errors:
            for msg in errors:
                flash(msg, "error")
        else:
            try:
                current_user.display_name = display_name
                current_user.bio = bio or None
                if avatar_filename:
                    current_user.avatar_filename = avatar_filename
                db.session.commit()

                flash("Profile updated successfully.", "success")
                return redirect(url_for("main.edit_profile"))
            except Exception as e:
                current_app.logger.error(f"Error updating profile: {str(e)}")
                db.session.rollback()
                flash(
                    "An error occurred while updating your profile. Please try again.",
                    "error",
                )

    # GET: show current values
    return render_template("edit_profile.html")
