"""
IP Address Validator
====================
A modular, OOP-based IPv4 address validation tool.
"""


class IPAddress:
    """
    Represents an IPv4 address and provides methods to
    decompose and inspect its components.
    """

    def __init__(self, address: str):
        self.__address = address.strip()

    @property
    def address(self) -> str:
        """Return the encapsulated IP address string."""
        return self.__address

    def get_octets(self) -> list[str]:
        """Split the address into its dot-separated parts."""
        return self.__address.split(".")

    def octet_count(self) -> int:
        """Return the number of dot-separated parts."""
        return len(self.get_octets())

    def __str__(self) -> str:
        return self.__address


class IPValidator:
    """
    Validates whether an IPAddress instance conforms to
    the IPv4 format (four octets, each in range 0–255).
    """

    OCTET_COUNT = 4
    OCTET_MIN = 0
    OCTET_MAX = 255

    def __init__(self, ip: IPAddress):
        self.__ip = ip
        self.__errors: list[str] = []

    @property
    def errors(self) -> list[str]:
        """Return validation error messages (read-only)."""
        return list(self.__errors)

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def __reset(self) -> None:
        self.__errors = []

    def __check_octet_count(self) -> bool:
        if self.__ip.octet_count() != self.OCTET_COUNT:
            self.__errors.append(
                f"Expected {self.OCTET_COUNT} octets separated by dots, "
                f"but found {self.__ip.octet_count()}."
            )
            return False
        return True

    def __check_octet_values(self) -> bool:
        valid = True
        for index, part in enumerate(self.__ip.get_octets(), start=1):
            # Must be numeric (no leading zeros allowed for values > 0)
            if not part.isdigit():
                self.__errors.append(
                    f"Octet {index} ('{part}') is not a valid integer."
                )
                valid = False
                continue

            value = int(part)
            if not (self.OCTET_MIN <= value <= self.OCTET_MAX):
                self.__errors.append(
                    f"Octet {index} ({value}) is out of range "
                    f"[{self.OCTET_MIN}–{self.OCTET_MAX}]."
                )
                valid = False

        return valid

    # ------------------------------------------------------------------ #
    #  Public interface                                                    #
    # ------------------------------------------------------------------ #

    def is_valid(self) -> bool:
        """
        Run all validation checks.
        Returns True if the IP address is valid, False otherwise.
        Populates self.errors with human-readable messages on failure.
        """
        self.__reset()

        if not self.__ip.address:
            self.__errors.append("IP address cannot be empty.")
            return False

        count_ok = self.__check_octet_count()
        # Only check values when the octet count is correct
        values_ok = self.__check_octet_values() if count_ok else False

        return count_ok and values_ok


# ------------------------------------------------------------------ #
#  Command-line interface                                              #
# ------------------------------------------------------------------ #

BANNER = """
╔══════════════════════════════════════════╗
║       IPv4 Address Validator  v1.0       ║
║  Type an IP address to validate it.      ║
║  Type  'q'  or  'quit'  to exit.         ║
╚══════════════════════════════════════════╝
"""

DIVIDER = "─" * 44


def run_cli() -> None:
    """Interactive command-line loop."""
    print(BANNER)

    while True:
        try:
            raw = input("Enter IP address: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if raw.lower() in {"q", "quit", "exit"}:
            print("Goodbye!")
            break

        ip = IPAddress(raw)
        validator = IPValidator(ip)

        print(DIVIDER)
        if validator.is_valid():
            print(f"  ✅  '{ip}' is a VALID IPv4 address.")
        else:
            print(f"  ❌  '{ip}' is INVALID.")
            for error in validator.errors:
                print(f"      • {error}")
        print(DIVIDER + "\n")


if __name__ == "__main__":
    run_cli()