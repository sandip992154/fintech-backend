"""Widen otp_code columns to store HMAC-SHA256 hashes

Revision ID: a1b2c3d4e5f6
Revises: 834dacd3d611
Create Date: 2026-02-23

Why this migration exists:
  OTP codes are now stored as HMAC-SHA256 hex digests (64 chars) instead of
  plain 6-digit strings. The previous VARCHAR(10) and VARCHAR(6) columns are
  too narrow to hold the hash.

  Once this migration runs:
  - Any plaintext OTP rows already in the DB are stale/expired and will be
    ignored automatically (is_expired=True or expires_at in the past).
  - All new OTP records will contain the HMAC hash.

Must run BEFORE deploying the new otp_service.py / pin_reset_router.py code.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "a1b2c3d4e5f6"
down_revision = "834dacd3d611"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # otp_requests table (used by pin_reset_router + otp_service)
    with op.batch_alter_table("otp_requests") as batch_op:
        batch_op.alter_column(
            "otp_code",
            existing_type=sa.String(length=10),
            type_=sa.String(length=64),
            existing_nullable=False,
        )

    # otp_records table (used by mpin_management)
    with op.batch_alter_table("otp_records") as batch_op:
        batch_op.alter_column(
            "otp_code",
            existing_type=sa.String(length=6),
            type_=sa.String(length=64),
            existing_nullable=False,
        )


def downgrade() -> None:
    # NOTE: downgrade will truncate any hash values already stored.
    # Only safe to run if no new OTP records have been created after upgrade.
    with op.batch_alter_table("otp_requests") as batch_op:
        batch_op.alter_column(
            "otp_code",
            existing_type=sa.String(length=64),
            type_=sa.String(length=10),
            existing_nullable=False,
        )

    with op.batch_alter_table("otp_records") as batch_op:
        batch_op.alter_column(
            "otp_code",
            existing_type=sa.String(length=64),
            type_=sa.String(length=6),
            existing_nullable=False,
        )
