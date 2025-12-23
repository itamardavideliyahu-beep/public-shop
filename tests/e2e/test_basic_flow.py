import uuid
import random

from playwright.sync_api import sync_playwright

from app import create_app, db
from app.models import User, Listing

BASE_URL = "http://127.0.0.1:5000"

# Create an application context so we can talk to the same database
app, socketio = create_app()
app.app_context().push()

# Make sure all tables exist before tests run (extra safety).
db.create_all()


def generate_random_user():
    """
    Generate random but valid user data for each test run.
    This makes each run slightly different while still deterministic inside the test.
    """
    random_suffix = uuid.uuid4().hex[:8]
    email = f"e2e_{random_suffix}@example.com"
    display_name_prefixes = ["Alex", "Taylor", "Jordan", "Sam", "Morgan"]
    display_name = random.choice(display_name_prefixes) + "_" + random_suffix
    password = "TestPass!" + random_suffix
    return email, display_name, password


def create_db_user():
    """
    Create a new user directly in the database and return
    both the ORM object and its login credentials.
    """
    email, display_name, password = generate_random_user()
    user = User(email=email, display_name=display_name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user, email, display_name, password


def create_db_listing_for_seller(seller: User) -> Listing:
    """
    Create a new active listing for the given seller.
    """
    suffix = uuid.uuid4().hex[:6]
    title = f"E2E Listing {suffix}"
    description = "This is a test listing created for an end-to-end flow."
    price = round(random.uniform(10, 999), 2)

    listing = Listing(
        seller=seller,
        title=title,
        description=description,
        price=price,
        category="electronics",  # must be a valid category value
        status="active",
    )
    db.session.add(listing)
    db.session.commit()
    return listing


def login_via_ui(page, email: str, password: str):
    """
    Log in using the real UI:
    - Go to home page.
    - Click the 'Login' link in the navbar.
    - Fill the login form and submit.
    """
    # Go to home page
    page.goto(BASE_URL, wait_until="networkidle")

    # Click on the "Login" link in the navbar
    page.click("text=Login")

    # Small wait to ensure the login page is loaded
    page.wait_for_timeout(500)

    # Fill login form.
    # NOTE: If your inputs have different names, adjust selectors below.
    page.fill("input[name='email']", email)
    page.fill("input[name='password']", password)

    # Submit login form
    try:
        page.click("button[type='submit']")
    except Exception:
        page.click("input[type='submit']")

    page.wait_for_timeout(1000)  # Wait for redirect and page load


def test_login_with_created_user():
    """
    E2E:
    - Create a user in the database.
    - Log in through the real UI (home -> Login).
    - Verify that the navbar shows the correct greeting.
    """
    user, email, display_name, password = create_db_user()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(5000)  # fail faster if something is wrong

        # Use the helper to log in via the UI
        login_via_ui(page, email, password)

        # Verify user is logged in - check for profile dropdown or user name
        final_html = page.content()
        assert (
            display_name in final_html
        ), f"User name '{display_name}' not found in page HTML after login."

        browser.close()


def test_contact_seller_message_flow():
    """
    E2E:
    - Create a seller and a buyer in the database.
    - Create a listing for the seller.
    - Log in as the buyer via the UI.
    - Open the listing page and click 'Contact seller'.
    - Send a message and verify it appears in the conversation.
    """
    # Create seller, buyer and listing in the database
    seller, seller_email, seller_display_name, seller_password = create_db_user()
    buyer, buyer_email, buyer_display_name, buyer_password = create_db_user()
    listing = create_db_listing_for_seller(seller)

    message_text = (
        f"Hi, I am interested in this item ({uuid.uuid4().hex[:4]})."
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(5000)

        # Step 1: log in as buyer using the real UI
        login_via_ui(page, buyer_email, buyer_password)

        # Step 2: go to the listing detail page
        page.goto(f"{BASE_URL}/listing/{listing.id}", wait_until="networkidle")

        # Step 3: click "Contact seller" (form submit button)
        page.click("text=Contact seller")
        page.wait_for_timeout(1000)  # Wait for conversation to be created and page to load

        # Step 4: verify that the conversation page loaded
        page_title = page.title()
        assert (
            seller_display_name in page_title
        ), f"Seller name '{seller_display_name}' not found in page title '{page_title}'."

        # Step 5: send a message in the conversation
        page.fill("textarea[name='content']", message_text)

        try:
            page.click("button[type='submit']")
        except Exception:
            page.click("input[type='submit']")

        page.wait_for_timeout(1000)  # Wait for message to be saved and page to reload

        # Step 6: verify that the message appears in the conversation HTML
        final_html = page.content()
        assert (
            message_text in final_html
        ), f"Sent message text '{message_text}' was not found in conversation HTML."

        browser.close()


def test_conversations_inbox():
    """
    E2E test for conversations inbox:
    - Create a seller and a buyer
    - Create a listing and start a conversation
    - Log in as buyer and check conversations inbox
    - Verify conversation appears in the inbox
    """
    # Create seller, buyer and listing
    seller, seller_email, seller_display_name, seller_password = create_db_user()
    buyer, buyer_email, buyer_display_name, buyer_password = create_db_user()
    listing = create_db_listing_for_seller(seller)

    # Create a conversation and message in the database
    from app.models import Conversation, Message
    from datetime import datetime
    
    conversation = Conversation(
        buyer=buyer,
        seller=seller,
        listing=listing,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(conversation)
    db.session.commit()

    message_text = "Test message for inbox"
    message = Message(
        conversation=conversation,
        sender=buyer,
        content=message_text,
        created_at=datetime.utcnow(),
        is_read=False,
    )
    db.session.add(message)
    conversation.updated_at = datetime.utcnow()
    db.session.commit()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(10000)

        # Step 1: Log in as buyer
        login_via_ui(page, buyer_email, buyer_password)

        # Step 2: Open profile dropdown and click Messages
        # Click on profile dropdown (avatar/name)
        page.click("#profileDropdown")
        page.wait_for_timeout(500)
        
        # Click on Messages in dropdown
        page.click("text=Messages")
        page.wait_for_timeout(1000)

        # Step 3: Verify conversations inbox loaded
        page_title = page.title()
        assert "Messages" in page_title, f"Expected 'Messages' in title, got '{page_title}'"

        # Step 4: Verify conversation appears in inbox
        page_content = page.content()
        assert (
            seller_display_name in page_content
        ), f"Seller name '{seller_display_name}' not found in conversations inbox."
        
        # Step 5: Verify last message preview appears
        assert (
            message_text in page_content
        ), f"Message text '{message_text}' not found in conversations inbox."

        # Step 6: Click on the conversation to open it
        page.click(f"text={seller_display_name}")
        page.wait_for_timeout(1000)

        # Step 7: Verify conversation detail page loaded
        conversation_page_content = page.content()
        assert (
            message_text in conversation_page_content
        ), f"Message text '{message_text}' not found in conversation detail page."

        browser.close()
