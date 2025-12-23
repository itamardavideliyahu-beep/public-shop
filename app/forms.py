"""
WTForms for the Public Shop application.
"""

import re

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    FloatField,
    PasswordField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    NumberRange,
    Optional,
    Regexp,
    ValidationError,
)


def validate_password_strength(form, field):
    """Validate password strength."""
    password = field.data
    if not password:
        return

    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one number.")

    if errors:
        raise ValidationError(" ".join(errors))


class RegisterForm(FlaskForm):
    """Registration form with CSRF protection."""

    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=30),
            Regexp(
                "^[a-zA-Z0-9_]+$",
                message="Username can only contain letters, numbers, and underscores",
            ),
        ],
    )
    display_name = StringField(
        "Display Name", validators=[DataRequired(), Length(min=2, max=80)]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), validate_password_strength]
    )
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])

    def validate_confirm_password(self, field):
        if self.password.data != field.data:
            raise ValidationError("Passwords must match.")

    def validate_username(self, field):
        """Validate username uniqueness."""
        from app.models import User

        username = field.data.strip().lower() if field.data else None
        if username:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                raise ValidationError(
                    "This username is already taken. Please choose another."
                )


class EmailVerificationForm(FlaskForm):
    """Form for email verification code."""

    verification_code = StringField(
        "Verification Code", validators=[DataRequired(), Length(min=6, max=6)]
    )


class LoginForm(FlaskForm):
    """Login form with CSRF protection."""

    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class PostForm(FlaskForm):
    """Form for creating posts."""

    content = TextAreaField(
        "Content", validators=[DataRequired(), Length(min=3, max=5000)]
    )


class ListingForm(FlaskForm):
    """Form for creating listings."""

    title = StringField("Title", validators=[DataRequired(), Length(min=3, max=120)])
    description = TextAreaField(
        "Description", validators=[Optional(), Length(max=2000)]
    )
    price = FloatField(
        "Price", validators=[DataRequired(), NumberRange(min=0.01, max=999999999)]
    )
    category = SelectField("Category", validators=[DataRequired()])
    image = FileField(
        "Image",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "gif", "webp"], "Images only!"),
        ],
    )
    expires_days = FloatField(
        "Expiration Days",
        validators=[Optional(), NumberRange(min=1, max=365)],
        default=365,
    )


class MessageForm(FlaskForm):
    """Form for sending messages."""

    content = TextAreaField(
        "Message", validators=[DataRequired(), Length(min=1, max=2000)]
    )


class SearchForm(FlaskForm):
    """Form for searching listings."""

    query = StringField("Search", validators=[Optional(), Length(max=100)])
    category = SelectField("Category", validators=[Optional()])
    min_price = FloatField("Min Price", validators=[Optional(), NumberRange(min=0)])
    max_price = FloatField("Max Price", validators=[Optional(), NumberRange(min=0)])
