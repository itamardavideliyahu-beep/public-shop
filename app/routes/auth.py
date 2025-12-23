import re
import secrets
from datetime import datetime, timedelta
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    session,
)
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)

from app import db
from app.models import User, EmailVerification
from app.utils import sanitize_input, send_email_notification
from app.forms import RegisterForm, LoginForm, EmailVerificationForm
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# Limiter will be initialized in __init__.py
def get_limiter():
    from flask import current_app

    return current_app.extensions.get("limiter")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Register a new user account.

    On POST, validate the form and send email verification code.
    User account is only created after email verification.
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        username = form.username.data.strip().lower()
        display_name = form.display_name.data
        password = form.password.data

        # Check for existing user by email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user is not None:
            flash("This email is already registered.", "error")
        # Check for existing user by username
        elif User.query.filter_by(username=username).first() is not None:
            flash("This username is already taken. Please choose another.", "error")
        else:
            # Check for pending verification
            existing_verification = EmailVerification.query.filter_by(
                email=email, verified=False
            ).first()

            if (
                existing_verification
                and existing_verification.expires_at > datetime.utcnow()
            ):
                flash(
                    "A verification code has already been sent to this email. Please check your inbox.",
                    "info",
                )
                return redirect(url_for("auth.verify_email", email=email))

            try:
                # Generate 6-digit verification code
                verification_code = "".join(
                    [str(secrets.randbelow(10)) for _ in range(6)]
                )

                # Hash password for storage
                temp_user = User(
                    email=email,
                    username=username,
                    display_name=display_name,
                    password_hash="",
                )
                temp_user.set_password(password)
                password_hash = temp_user.password_hash

                # Create email verification record
                verification = EmailVerification(
                    email=email,
                    verification_code=verification_code,
                    username=username,
                    display_name=display_name,
                    password_hash=password_hash,
                    expires_at=datetime.utcnow()
                    + timedelta(minutes=15),  # Code expires in 15 minutes
                )

                # Delete old unverified records for this email
                EmailVerification.query.filter_by(email=email, verified=False).delete()

                db.session.add(verification)
                db.session.commit()

                # Send verification email
                email_subject = "Verify your email - Public Shop"
                email_message = f"""
Hello {display_name},

Thank you for registering with Public Shop!

Your verification code is: {verification_code}

This code will expire in 15 minutes.

If you didn't register for Public Shop, please ignore this email.

Best regards,
Public Shop Team
"""
                email_html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #667eea;">Welcome to Public Shop!</h2>
        <p>Hello {display_name},</p>
        <p>Thank you for registering with Public Shop!</p>
        <div style="background: #f8f9ff; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
            <p style="margin: 0; font-size: 14px; color: #65676b;">Your verification code is:</p>
            <h1 style="color: #667eea; font-size: 32px; letter-spacing: 5px; margin: 10px 0;">{verification_code}</h1>
            <p style="margin: 0; font-size: 12px; color: #65676b;">This code will expire in 15 minutes.</p>
        </div>
        <p>If you didn't register for Public Shop, please ignore this email.</p>
        <p style="color: #65676b; font-size: 12px; margin-top: 30px;">Best regards,<br>Public Shop Team</p>
    </div>
</body>
</html>
"""

                send_email_notification(
                    to_email=email,
                    subject=email_subject,
                    message=email_message,
                    html=email_html,
                )

                flash(
                    "Verification code has been sent to your email. Please check your inbox.",
                    "success",
                )
                return redirect(url_for("auth.verify_email", email=email))

            except Exception as e:
                current_app.logger.error(f"Error creating verification: {str(e)}")
                db.session.rollback()
                flash("An error occurred. Please try again.", "error")

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Log in an existing user.

    If the user is already authenticated, redirect to the home page.
    On POST, validate credentials and log the user in.
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(password):
            current_app.logger.warning(f"Failed login attempt for email: {email}")
            flash("Invalid email or password.", "error")
        else:
            # Allow login for existing users (backward compatibility)
            # Auto-verify existing users for backward compatibility
            if not user.email_verified:
                user.email_verified = True
                db.session.commit()
                flash("Your email has been verified. Welcome back!", "success")

            login_user(user)
            current_app.logger.info(f"User {user.id} logged in successfully")
            flash("Logged in successfully.", "success")

            next_page = request.args.get("next")
            # Security: validate next_page to prevent open redirects
            if next_page and not next_page.startswith("/"):
                next_page = None
            return redirect(next_page or url_for("main.index"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    """
    Verify email address with verification code.
    Creates user account after successful verification.
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    email = request.args.get("email")
    if not email:
        flash("Invalid verification link.", "error")
        return redirect(url_for("auth.register"))

    form = EmailVerificationForm()

    # Get the verification record
    verification = (
        EmailVerification.query.filter_by(email=email, verified=False)
        .order_by(EmailVerification.created_at.desc())
        .first()
    )

    if not verification:
        flash(
            "No pending verification found for this email. Please register again.",
            "error",
        )
        return redirect(url_for("auth.register"))

    if verification.expires_at < datetime.utcnow():
        flash("Verification code has expired. Please register again.", "error")
        db.session.delete(verification)
        db.session.commit()
        return redirect(url_for("auth.register"))

    if form.validate_on_submit():
        code = form.verification_code.data.strip()

        if code == verification.verification_code:
            try:
                # Check if username is still available (in case someone else took it)
                if User.query.filter_by(username=verification.username).first():
                    flash(
                        "This username is no longer available. Please register again with a different username.",
                        "error",
                    )
                    db.session.delete(verification)
                    db.session.commit()
                    return redirect(url_for("auth.register"))

                # Create the user account
                user = User(
                    email=verification.email,
                    username=verification.username,
                    display_name=verification.display_name,
                    password_hash=verification.password_hash,
                    email_verified=True,
                    mfa_enabled=False,
                    mfa_secret=None,
                )
                db.session.add(user)

                # Mark verification as completed
                verification.verified = True

                db.session.commit()

                # Log the user in automatically
                login_user(user)

                flash(
                    "Email verified successfully! Your account has been created.",
                    "success",
                )
                return redirect(url_for("main.index"))

            except Exception as e:
                current_app.logger.error(
                    f"Error creating user after verification: {str(e)}"
                )
                db.session.rollback()
                flash(
                    "An error occurred while creating your account. Please try again.",
                    "error",
                )
        else:
            flash("Invalid verification code. Please try again.", "error")

    return render_template("auth/verify_email.html", form=form, email=email)


@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    """Resend verification code to email."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    email = request.form.get("email")
    if not email:
        flash("Invalid request.", "error")
        return redirect(url_for("auth.register"))

    verification = (
        EmailVerification.query.filter_by(email=email, verified=False)
        .order_by(EmailVerification.created_at.desc())
        .first()
    )

    if not verification:
        flash("No pending verification found. Please register again.", "error")
        return redirect(url_for("auth.register"))

    try:
        # Generate new code
        verification_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
        verification.verification_code = verification_code
        verification.expires_at = datetime.utcnow() + timedelta(minutes=15)
        verification.created_at = datetime.utcnow()

        db.session.commit()

        # Send email
        email_subject = "Verify your email - Public Shop"
        email_message = f"""
Hello {verification.display_name},

Your new verification code is: {verification_code}

This code will expire in 15 minutes.

Best regards,
Public Shop Team
"""
        email_html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #667eea;">Verification Code</h2>
        <p>Hello {verification.display_name},</p>
        <div style="background: #f8f9ff; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
            <p style="margin: 0; font-size: 14px; color: #65676b;">Your verification code is:</p>
            <h1 style="color: #667eea; font-size: 32px; letter-spacing: 5px; margin: 10px 0;">{verification_code}</h1>
            <p style="margin: 0; font-size: 12px; color: #65676b;">This code will expire in 15 minutes.</p>
        </div>
        <p style="color: #65676b; font-size: 12px; margin-top: 30px;">Best regards,<br>Public Shop Team</p>
    </div>
</body>
</html>
"""

        send_email_notification(
            to_email=email,
            subject=email_subject,
            message=email_message,
            html=email_html,
        )

        flash("New verification code has been sent to your email.", "success")
    except Exception as e:
        current_app.logger.error(f"Error resending verification: {str(e)}")
        db.session.rollback()
        flash("An error occurred. Please try again.", "error")

    return redirect(url_for("auth.verify_email", email=email))


@auth_bp.route("/logout")
@login_required
def logout():
    """
    Log out the currently authenticated user.
    """
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))
