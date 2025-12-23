"""
Utility functions for the Public Shop application.
"""

import os
from pathlib import Path
from typing import Optional, Tuple

from flask import current_app
from PIL import Image
from werkzeug.utils import secure_filename


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    Check if a file has an allowed extension.

    Args:
        filename: The name of the file to check.
        allowed_extensions: Set of allowed file extensions (without dots).

    Returns:
        True if the file extension is allowed, False otherwise.
    """
    if "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in allowed_extensions


def validate_image_file(file) -> Tuple[bool, Optional[str]]:
    """
    Validate an uploaded image file.

    Args:
        file: The uploaded file object from Flask.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, error_message is None.
    """
    if not file or not file.filename:
        return False, "No file provided"

    # Check file extension
    if not allowed_file(file.filename, current_app.config["ALLOWED_IMAGE_EXTENSIONS"]):
        return (
            False,
            f"File type not allowed. Allowed types: {', '.join(current_app.config['ALLOWED_IMAGE_EXTENSIONS'])}",
        )

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer

    if file_size > current_app.config["MAX_IMAGE_SIZE"]:
        max_size_mb = current_app.config["MAX_IMAGE_SIZE"] / (1024 * 1024)
        return False, f"File too large. Maximum size: {max_size_mb:.1f}MB"

    # Validate that it's actually an image
    try:
        file.seek(0)
        img = Image.open(file)
        img.verify()
        file.seek(0)  # Reset after verify
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"

    return True, None


def create_thumbnail(image_path: Path, size: tuple, output_path: Path) -> bool:
    """
    Create a thumbnail from an image.

    Args:
        image_path: Path to the source image.
        size: Tuple of (width, height) for thumbnail.
        output_path: Path where thumbnail should be saved.

    Returns:
        True if successful, False otherwise.
    """
    try:
        img = Image.open(image_path)
        img.thumbnail(size, Image.Resampling.LANCZOS)

        # Convert RGBA to RGB if necessary (for JPEG compatibility)
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "JPEG", quality=85, optimize=True)
        return True
    except Exception as e:
        current_app.logger.error(f"Error creating thumbnail: {str(e)}")
        return False


def save_uploaded_image(
    file, subdirectory: str, prefix: str = "", create_thumb: bool = False
) -> Optional[str]:
    """
    Save an uploaded image file to the uploads directory and optionally create thumbnails.

    Args:
        file: The uploaded file object from Flask.
        subdirectory: Subdirectory within uploads (e.g., 'listings', 'avatars').
        prefix: Optional prefix for the filename.
        create_thumb: Whether to create a thumbnail version.

    Returns:
        The saved filename if successful, None otherwise.
    """
    if not file or not file.filename:
        return None

    # Validate the file
    is_valid, error = validate_image_file(file)
    if not is_valid:
        current_app.logger.warning(f"Image validation failed: {error}")
        return None

    # Generate secure filename
    filename = secure_filename(file.filename)
    if prefix:
        name, ext = os.path.splitext(filename)
        filename = f"{prefix}_{name}{ext}"

    # Ensure unique filename
    upload_path = Path(current_app.config["UPLOAD_FOLDER"]) / subdirectory
    upload_path.mkdir(parents=True, exist_ok=True)

    file_path = upload_path / filename
    counter = 1
    while file_path.exists():
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{counter}{ext}"
        file_path = upload_path / filename
        counter += 1

    # Save the file
    try:
        file.seek(0)
        file.save(str(file_path))

        # Create thumbnail if requested
        if create_thumb:
            thumb_size = current_app.config.get("THUMBNAIL_SIZE", (400, 400))
            if subdirectory == "avatars":
                thumb_size = current_app.config.get("AVATAR_SIZE", (200, 200))

            thumb_path = upload_path / "thumbs" / filename
            create_thumbnail(file_path, thumb_size, thumb_path)

        # Optimize the main image
        try:
            img = Image.open(file_path)
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(
                    img, mask=img.split()[-1] if img.mode == "RGBA" else None
                )
                img = background

            # Save optimized version
            img.save(file_path, "JPEG", quality=85, optimize=True)
        except Exception as e:
            current_app.logger.warning(f"Could not optimize image: {str(e)}")

        return filename
    except Exception as e:
        current_app.logger.error(f"Error saving file: {str(e)}")
        return None


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input by stripping whitespace and optionally truncating.

    Args:
        text: The text to sanitize.
        max_length: Optional maximum length to truncate to.

    Returns:
        Sanitized text.
    """
    if not text:
        return ""
    text = text.strip()
    if max_length and len(text) > max_length:
        text = text[:max_length]
    return text


def send_email_notification(
    to_email: str, subject: str, message: str, html: str = None
) -> bool:
    """
    Send an email notification using Flask-Mail.

    Args:
        to_email: Recipient email address.
        subject: Email subject.
        message: Plain text email body.
        html: Optional HTML email body.

    Returns:
        True if email was sent successfully, False otherwise.
    """
    try:
        from flask_mail import Message

        # Check if mail is configured
        if not current_app.config.get("MAIL_USERNAME"):
            current_app.logger.warning(
                f"Email not configured. Would send to {to_email}: {subject}"
            )
            return True  # Don't fail if email not configured

        msg = Message(subject=subject, recipients=[to_email], body=message, html=html)

        mail = current_app.extensions.get("mail")
        if mail:
            mail.send(msg)
            current_app.logger.info(f"Email sent to {to_email}: {subject}")
            return True
        else:
            current_app.logger.warning("Flask-Mail not initialized")
            return False
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False
