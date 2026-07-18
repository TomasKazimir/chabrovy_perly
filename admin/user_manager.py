#!/usr/bin/env python3
"""
User management maintenance script for SQLite database.
Manages application users and passwords.
"""

import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash


class UserManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path("instance") / "quotes.sqlite3"

        self.db_path = Path(db_path)
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Ensure database and users table exist."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
                """
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to initialize database: {e}")
            raise
        except Exception as e:
            print(f"[ERROR] Unexpected error initializing database: {e}")
            raise

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to connect to database: {e}")
            raise
        except Exception as e:
            print(f"[ERROR] Unexpected error connecting to database: {e}")
            raise

    def add_user(self, username: str, password: str) -> None:
        """Add a new user."""
        if not username:
            print("[ERROR] Username cannot be empty.")
            return

        if not password:
            print("[ERROR] Password cannot be empty.")
            return

        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                print(f"[ERROR] User '{username}' already exists.")
                return
        finally:
            conn.close()

        password_hash = generate_password_hash(password)
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            conn.commit()
            print(f"[OK] User '{username}' added.")
        finally:
            conn.close()

    def list_users(self) -> None:
        """List all users."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT id, username FROM users ORDER BY username")
            users = cursor.fetchall()

            if not users:
                print("[INFO] No users found.")
                return

            print("\n[USERS]")
            for user in users:
                print(f"  {user['id']:3} | {user['username']}")
            print()
        finally:
            conn.close()

    def change_password(self, username: str, new_password: str) -> None:
        """Change password for an existing user."""
        if not username:
            print("[ERROR] Username cannot be empty.")
            return

        if not new_password:
            print("[ERROR] Password cannot be empty.")
            return

        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()

            if not user:
                print(f"[ERROR] User '{username}' not found.")
                return
        finally:
            conn.close()

        password_hash = generate_password_hash(new_password)
        conn = self._get_conn()
        try:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (password_hash, user['id'])
            )
            conn.commit()
            print(f"[OK] Password for '{username}' changed.")
        finally:
            conn.close()

    def remove_user(self, username: str) -> None:
        """Remove a user."""
        if not username:
            print("[ERROR] Username cannot be empty.")
            return

        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if not user:
                print(f"[ERROR] User '{username}' not found.")
                return
        finally:
            conn.close()

        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM users WHERE id = ?", (user['id'],))
            conn.commit()
            print(f"[OK] User '{username}' removed.")
        finally:
            conn.close()

    def show_help(self) -> None:
        """Display help message."""
        print("\n[USER MANAGER - COMMANDS]")
        print("  add <username> <password>    Add new user")
        print("  change <username> <password> Change user password")
        print("  list                         List all users")
        print("  remove <username>            Remove user")
        print("  help                         Show this message")
        print("  exit                         Exit program")
        print()

    def run(self) -> None:
        """Run the user manager."""
        print("[USER MANAGER] Starting maintenance shell...\n")

        while True:
            try:
                command = input("user_mgmt> ").strip()

                if not command:
                    continue

                parts = command.split(maxsplit=2)
                cmd = parts[0].lower()

                if cmd == "exit":
                    print("[OK] Exiting.")
                    break
                elif cmd == "help":
                    self.show_help()
                elif cmd == "list":
                    self.list_users()
                elif cmd == "add":
                    if len(parts) < 3:
                        print("[ERROR] Usage: add <username> <password>")
                    else:
                        self.add_user(parts[1], parts[2])
                elif cmd == "change":
                    if len(parts) < 3:
                        print("[ERROR] Usage: change <username> <password>")
                    else:
                        self.change_password(parts[1], parts[2])
                elif cmd == "remove":
                    if len(parts) < 2:
                        print("[ERROR] Usage: remove <username>")
                    else:
                        self.remove_user(parts[1])
                else:
                    print(f"[ERROR] Unknown command: '{cmd}'. Type 'help' for available commands.")
            except KeyboardInterrupt:
                print("\n[OK] Interrupted. Exiting.")
                break
            except Exception as e:
                print(f"[ERROR] {e}")


if __name__ == "__main__":
    manager = UserManager()
    manager.run()
