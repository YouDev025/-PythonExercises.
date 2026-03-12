"""
Simple Encryption System
========================
A Caesar cipher-based encryption/decryption tool built with OOP principles.
"""

from __future__ import annotations
import re


# ─────────────────────────────────────────────
#  Message – data holder with encapsulation
# ─────────────────────────────────────────────
class Message:
    """Stores an original text and its encrypted counterpart."""

    def __init__(self, original_text: str) -> None:
        self._original_text: str = original_text
        self._encrypted_text: str = ""
        self._shift_used: int | None = None

    # ── getters ──────────────────────────────
    @property
    def original_text(self) -> str:
        return self._original_text

    @property
    def encrypted_text(self) -> str:
        return self._encrypted_text

    @property
    def shift_used(self) -> int | None:
        return self._shift_used

    # ── setters (used by EncryptionEngine) ───
    @encrypted_text.setter
    def encrypted_text(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Encrypted text must be a string.")
        self._encrypted_text = value

    @shift_used.setter
    def shift_used(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("Shift must be an integer.")
        self._shift_used = value

    def __repr__(self) -> str:
        return (
            f"Message(original={self._original_text!r}, "
            f"encrypted={self._encrypted_text!r}, "
            f"shift={self._shift_used})"
        )


# ─────────────────────────────────────────────
#  EncryptionEngine – all cipher logic
# ─────────────────────────────────────────────
class EncryptionEngine:
    """
    Performs Caesar cipher encryption and decryption.

    Rules:
    • Letters (A-Z / a-z) are shifted; case is preserved.
    • Digits (0-9) are shifted within the 0-9 range.
    • All other characters (spaces, punctuation, …) pass through unchanged.
    """

    ALPHA_SIZE = 26
    DIGIT_SIZE = 10

    # ── public API ────────────────────────────
    def encrypt(self, message: Message, shift: int) -> Message:
        """Encrypt *message* in-place using *shift* and return it."""
        self._validate_shift(shift)
        cipher = self._apply_shift(message.original_text, shift)
        message.encrypted_text = cipher
        message.shift_used = shift
        return message

    def decrypt(self, ciphertext: str, shift: int) -> str:
        """Return the plaintext obtained by reversing *shift* on *ciphertext*."""
        self._validate_shift(shift)
        return self._apply_shift(ciphertext, -shift)

    def decrypt_message(self, message: Message) -> str:
        """Decrypt a *Message* object that has already been encrypted."""
        if not message.encrypted_text:
            raise ValueError("This message has not been encrypted yet.")
        if message.shift_used is None:
            raise ValueError("No shift value recorded in this message.")
        return self.decrypt(message.encrypted_text, message.shift_used)

    # ── private helpers ───────────────────────
    @staticmethod
    def _validate_shift(shift: int) -> None:
        if not isinstance(shift, int):
            raise TypeError(f"Shift must be an integer, got {type(shift).__name__}.")

    @classmethod
    def _shift_char(cls, char: str, shift: int) -> str:
        """Shift a single character according to Caesar rules."""
        if char.isalpha():
            base = ord("A") if char.isupper() else ord("a")
            return chr((ord(char) - base + shift) % cls.ALPHA_SIZE + base)
        if char.isdigit():
            return chr((ord(char) - ord("0") + shift) % cls.DIGIT_SIZE + ord("0"))
        return char  # spaces, punctuation, etc.

    @classmethod
    def _apply_shift(cls, text: str, shift: int) -> str:
        return "".join(cls._shift_char(ch, shift) for ch in text)


# ─────────────────────────────────────────────
#  Input helpers
# ─────────────────────────────────────────────
def _get_nonempty_string(prompt: str) -> str:
    """Prompt until the user enters a non-blank string."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("  ⚠  Input cannot be empty. Please try again.")


def _get_shift(prompt: str = "  Enter shift value (integer): ") -> int:
    """Prompt until the user provides a valid integer shift."""
    while True:
        raw = input(prompt).strip()
        try:
            return int(raw)
        except ValueError:
            print("  ⚠  Invalid shift – please enter a whole number (e.g. 3 or -7).")


def _get_choice(prompt: str, valid: set[str]) -> str:
    """Prompt until the user picks one of the *valid* options (case-insensitive)."""
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid:
            return choice
        print(f"  ⚠  Please enter one of: {', '.join(sorted(valid))}")


# ─────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────
BANNER = r"""
╔══════════════════════════════════════════════╗
║       Simple Encryption System v1.0          ║
║        Caesar Cipher  •  Python OOP          ║
╚══════════════════════════════════════════════╝
"""

MENU = """
  [E] Encrypt a message
  [D] Decrypt a message
  [H] Help / how it works
  [Q] Quit
"""

HELP_TEXT = """
  ── How it works ─────────────────────────────
  Caesar cipher shifts every letter in the alphabet
  by a fixed number of positions.  Digits 0-9 are
  also shifted within their own range.  All other
  characters (spaces, punctuation) stay unchanged.

  Example  – shift 3:
    'Hello, World! 9' → 'Khoor, Zruog! 2'

  To decrypt, use the same shift you encrypted with.
  Negative shifts are perfectly valid!
  ─────────────────────────────────────────────
"""


def run_encrypt(engine: EncryptionEngine) -> None:
    print("\n── Encrypt ──────────────────────────────────")
    text = _get_nonempty_string("  Enter message to encrypt: ")
    shift = _get_shift()

    msg = Message(text)
    engine.encrypt(msg, shift)

    print(f"\n  Original  : {msg.original_text}")
    print(f"  Shift     : {msg.shift_used}")
    print(f"  Encrypted : {msg.encrypted_text}")


def run_decrypt(engine: EncryptionEngine) -> None:
    print("\n── Decrypt ──────────────────────────────────")
    ciphertext = _get_nonempty_string("  Enter encrypted message: ")
    shift = _get_shift()

    try:
        plaintext = engine.decrypt(ciphertext, shift)
    except (TypeError, ValueError) as exc:
        print(f"\n  ✗ Error: {exc}")
        return

    print(f"\n  Encrypted : {ciphertext}")
    print(f"  Shift     : {shift}")
    print(f"  Decrypted : {plaintext}")


def main() -> None:
    print(BANNER)
    engine = EncryptionEngine()

    while True:
        print(MENU)
        choice = _get_choice("  Your choice: ", {"e", "d", "h", "q"})

        if choice == "e":
            run_encrypt(engine)
        elif choice == "d":
            run_decrypt(engine)
        elif choice == "h":
            print(HELP_TEXT)
        elif choice == "q":
            print("\n  Goodbye! 👋\n")
            break


if __name__ == "__main__":
    main()