"""Command-line tool to create a login user.

Run with ``uv run adamfit-create-user <username>``. There is deliberately no
sign-up page, so this is the only way to add users.
"""

import argparse
import getpass
import logging
import sys

# The database helpers use Streamlit's cache, which logs a harmless warning
# when used outside a running Streamlit app. Silence it for this tool.
logging.getLogger("streamlit").setLevel(logging.ERROR)

from adamfit import users  # noqa: E402
from adamfit.auth import hash_password  # noqa: E402

MIN_PASSWORD_LENGTH = 8


def main() -> None:
    """
    Prompt for a password and create the user named on the command line.
    """
    parser = argparse.ArgumentParser(description="Create an AdamFit login user.")
    parser.add_argument("username", help="Username (3+ characters, stored in lowercase)")
    args = parser.parse_args()

    if users.get_login_record(args.username):
        sys.exit(f"User '{args.username}' already exists.")

    password = getpass.getpass("Password: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if getpass.getpass("Confirm password: ") != password:
        sys.exit("Passwords do not match.")

    user_id = users.create_user(args.username, hash_password(password))
    print(f"Created user '{args.username.lower()}' (id {user_id}).")


if __name__ == "__main__":
    main()
