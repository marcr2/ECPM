#!/usr/bin/env python3
"""Generate a bcrypt password hash for the ECPM admin user.

Usage:
    python scripts/create_admin.py
    # Then paste the output into ADMIN_PASSWORD_HASH in .env.local
"""

import getpass
import sys

try:
    import bcrypt
except ImportError:
    print("Error: bcrypt not installed. Run: pip install bcrypt")
    sys.exit(1)


def main() -> None:
    password = getpass.getpass("Enter admin password: ")
    confirm = getpass.getpass("Confirm admin password: ")

    if password != confirm:
        print("Error: passwords do not match.")
        sys.exit(1)

    if len(password) < 12:
        print("Warning: password should be at least 12 characters for security.")

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    print(f"\nAdd this to your .env.local:\n")
    print(f"ADMIN_PASSWORD_HASH={hashed}")


if __name__ == "__main__":
    main()
