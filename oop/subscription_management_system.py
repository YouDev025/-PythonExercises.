"""
Subscription Management System
An OOP-based system for managing user subscriptions with a CLI menu.
"""

import os
from datetime import datetime, date, timedelta


# ─────────────────────────────────────────────
#  SUBSCRIPTION CLASS
# ─────────────────────────────────────────────

class Subscription:
    """Represents a single user subscription with encapsulated data."""

    STATUS_ACTIVE   = "Active"
    STATUS_INACTIVE = "Inactive"
    STATUS_EXPIRED  = "Expired"
    STATUS_CANCELLED = "Cancelled"

    VALID_STATUSES = {STATUS_ACTIVE, STATUS_INACTIVE, STATUS_EXPIRED, STATUS_CANCELLED}

    def __init__(self, subscription_id: int, user_name: str, service_name: str,
                 start_date: str, end_date: str, price: float):
        self.__subscription_id: int  = subscription_id
        self.__user_name: str        = self._clean(user_name,    "User name")
        self.__service_name: str     = self._clean(service_name, "Service name")
        self.__start_date: date      = self._parse_date(start_date, "Start date")
        self.__end_date: date        = self._parse_date(end_date,   "End date")
        self.__price: float          = self._clean_price(price)
        self.__status: str           = self.STATUS_ACTIVE
        self.__created_at: str       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.__end_date < self.__start_date:
            raise ValueError("End date must be on or after start date.")

        # Auto-expire if end date is already in the past
        if self.__end_date < date.today():
            self.__status = self.STATUS_EXPIRED

    # ── Static validators ───────────────────────

    @staticmethod
    def _clean(value: str, label: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{label} cannot be empty.")
        if len(value) > 60:
            raise ValueError(f"{label} must be 60 characters or fewer.")
        return value

    @staticmethod
    def _parse_date(value: str, label: str) -> date:
        value = value.strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"{label} must be in YYYY-MM-DD format (e.g. 2025-01-31).")

    @staticmethod
    def _clean_price(value: float) -> float:
        if value < 0:
            raise ValueError("Price cannot be negative.")
        return round(value, 2)

    # ── Read-only properties ────────────────────

    @property
    def subscription_id(self) -> int:
        return self.__subscription_id

    @property
    def user_name(self) -> str:
        return self.__user_name

    @property
    def service_name(self) -> str:
        return self.__service_name

    @property
    def start_date(self) -> date:
        return self.__start_date

    @property
    def end_date(self) -> date:
        return self.__end_date

    @property
    def price(self) -> float:
        return self.__price

    @property
    def status(self) -> str:
        return self.__status

    @property
    def created_at(self) -> str:
        return self.__created_at

    @property
    def days_remaining(self) -> int:
        """Days until expiry; negative if already expired."""
        return (self.__end_date - date.today()).days

    @property
    def is_active(self) -> bool:
        return self.__status == self.STATUS_ACTIVE

    # ── State mutations ─────────────────────────

    def cancel(self):
        self.__status = self.STATUS_CANCELLED

    def expire(self):
        self.__status = self.STATUS_EXPIRED

    def renew(self, new_end_date: str, new_price: float | None = None):
        parsed = self._parse_date(new_end_date, "New end date")
        if parsed <= date.today():
            raise ValueError("Renewal end date must be in the future.")
        self.__end_date = parsed
        if new_price is not None:
            self.__price = self._clean_price(new_price)
        self.__status = self.STATUS_ACTIVE

    def update(self, service_name: str | None = None,
               end_date: str | None = None,
               price: float | None = None):
        if service_name is not None:
            self.__service_name = self._clean(service_name, "Service name")
        if end_date is not None:
            parsed = self._parse_date(end_date, "End date")
            if parsed < self.__start_date:
                raise ValueError("End date cannot be before start date.")
            self.__end_date = parsed
        if price is not None:
            self.__price = self._clean_price(price)

    # ── Display ─────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "ID":           self.__subscription_id,
            "User":         self.__user_name,
            "Service":      self.__service_name,
            "Start Date":   self.__start_date.strftime("%Y-%m-%d"),
            "End Date":     self.__end_date.strftime("%Y-%m-%d"),
            "Price":        f"${self.__price:,.2f}/mo",
            "Status":       self.__status,
            "Days Left":    self.days_remaining,
            "Created At":   self.__created_at,
        }

    def __repr__(self) -> str:
        return (f"Subscription(id={self.__subscription_id}, user='{self.__user_name}', "
                f"service='{self.__service_name}', status='{self.__status}')")


# ─────────────────────────────────────────────
#  SUBSCRIPTION MANAGER CLASS
# ─────────────────────────────────────────────

class SubscriptionManager:
    """Manages all subscriptions."""

    def __init__(self):
        self.__subscriptions: dict[int, Subscription] = {}
        self.__next_id: int = 1

    # ── Internal helpers ────────────────────────

    def _next_id(self) -> int:
        uid = self.__next_id
        self.__next_id += 1
        return uid

    def _get(self, sub_id: int) -> "Subscription | None":
        return self.__subscriptions.get(sub_id)

    def _all(self) -> list[Subscription]:
        return list(self.__subscriptions.values())

    # ── Core CRUD ───────────────────────────────

    def create_subscription(self, user_name: str, service_name: str,
                             start_date: str, end_date: str,
                             price: float) -> "Subscription | None":
        try:
            sub = Subscription(self._next_id(), user_name, service_name,
                               start_date, end_date, price)
            self.__subscriptions[sub.subscription_id] = sub
            print(f"  [✓] Subscription #{sub.subscription_id} created for "
                  f"'{user_name}' → '{service_name}'.")
            return sub
        except ValueError as exc:
            print(f"  [!] {exc}")
            return None

    def update_subscription(self, sub_id: int,
                             service_name: str | None = None,
                             end_date: str | None = None,
                             price: float | None = None) -> bool:
        sub = self._get(sub_id)
        if not sub:
            print(f"  [!] Subscription #{sub_id} not found.")
            return False
        if sub.status in (Subscription.STATUS_CANCELLED, Subscription.STATUS_EXPIRED):
            print(f"  [!] Cannot update a {sub.status.lower()} subscription.")
            return False
        try:
            sub.update(service_name, end_date, price)
            print(f"  [✓] Subscription #{sub_id} updated.")
            return True
        except ValueError as exc:
            print(f"  [!] {exc}")
            return False

    def cancel_subscription(self, sub_id: int) -> bool:
        sub = self._get(sub_id)
        if not sub:
            print(f"  [!] Subscription #{sub_id} not found.")
            return False
        if sub.status == Subscription.STATUS_CANCELLED:
            print(f"  [~] Subscription #{sub_id} is already cancelled.")
            return False
        sub.cancel()
        print(f"  [✓] Subscription #{sub_id} cancelled.")
        return True

    def renew_subscription(self, sub_id: int, new_end_date: str,
                            new_price: float | None = None) -> bool:
        sub = self._get(sub_id)
        if not sub:
            print(f"  [!] Subscription #{sub_id} not found.")
            return False
        if sub.status == Subscription.STATUS_ACTIVE:
            print(f"  [~] Subscription #{sub_id} is already active. "
                  "Extending end date…")
        try:
            sub.renew(new_end_date, new_price)
            print(f"  [✓] Subscription #{sub_id} renewed until {new_end_date}.")
            return True
        except ValueError as exc:
            print(f"  [!] {exc}")
            return False

    def delete_subscription(self, sub_id: int) -> bool:
        if sub_id not in self.__subscriptions:
            print(f"  [!] Subscription #{sub_id} not found.")
            return False
        del self.__subscriptions[sub_id]
        print(f"  [✓] Subscription #{sub_id} permanently deleted.")
        return True

    # ── Expiry checker ───────────────────────────

    def check_expired(self) -> list[Subscription]:
        """Mark and return all subscriptions whose end date has passed."""
        expired = []
        for sub in self._all():
            if sub.status == Subscription.STATUS_ACTIVE and sub.days_remaining < 0:
                sub.expire()
                expired.append(sub)
        return expired

    def expiring_soon(self, days: int = 7) -> list[Subscription]:
        """Return active subscriptions expiring within `days` days."""
        return [s for s in self._all()
                if s.is_active and 0 <= s.days_remaining <= days]

    # ── Search ───────────────────────────────────

    def search_by_user(self, user_name: str) -> list[Subscription]:
        kw = user_name.strip().lower()
        return [s for s in self._all() if kw in s.user_name.lower()]

    def search_by_service(self, service_name: str) -> list[Subscription]:
        kw = service_name.strip().lower()
        return [s for s in self._all() if kw in s.service_name.lower()]

    def search_by_status(self, status: str) -> list[Subscription]:
        return [s for s in self._all() if s.status.lower() == status.strip().lower()]

    # ── Revenue & stats ──────────────────────────

    @property
    def total_revenue(self) -> float:
        """Sum of monthly prices for all active subscriptions."""
        return round(sum(s.price for s in self._all() if s.is_active), 2)

    @property
    def total_count(self) -> int:
        return len(self.__subscriptions)

    def stats(self) -> dict:
        all_subs  = self._all()
        by_status = {s: sum(1 for x in all_subs if x.status == s)
                     for s in Subscription.VALID_STATUSES}
        return {
            "total":          len(all_subs),
            "by_status":      by_status,
            "active_revenue": self.total_revenue,
            "services":       len({s.service_name for s in all_subs}),
            "users":          len({s.user_name     for s in all_subs}),
        }

    # ── Display ──────────────────────────────────

    STATUS_ICONS = {
        Subscription.STATUS_ACTIVE:    "🟢",
        Subscription.STATUS_INACTIVE:  "🟡",
        Subscription.STATUS_EXPIRED:   "🔴",
        Subscription.STATUS_CANCELLED: "⚫",
    }

    def _print_subscriptions(self, subs: list[Subscription], title: str = "Subscriptions"):
        if not subs:
            print("  [~] No subscriptions found.")
            return
        print(f"\n  ┌─ {title} ({len(subs)}) {'─' * 35}")
        for s in subs:
            icon = self.STATUS_ICONS.get(s.status, "❓")
            dr   = s.days_remaining
            dr_label = (f"{dr}d left" if dr >= 0 else f"expired {abs(dr)}d ago")
            print(f"  │")
            print(f"  │  {icon} #{s.subscription_id:<4}  {s.user_name:<20}  "
                  f"${s.price:>8,.2f}/mo  [{s.status}]")
            print(f"  │       Service  : {s.service_name}")
            print(f"  │       Period   : {s.start_date} → {s.end_date}  ({dr_label})")
        print("  └" + "─" * 60)

    def display_all(self):
        self._print_subscriptions(self._all(), "All Subscriptions")

    def display_summary(self):
        st = self.stats()
        bs = st["by_status"]
        print(f"""
  ┌─ System Summary {'─' * 42}
  │   Total Subscriptions : {st['total']}
  │   ─────────────────────────────────
  │   🟢 Active    : {bs['Active']:>4}
  │   🟡 Inactive  : {bs['Inactive']:>4}
  │   🔴 Expired   : {bs['Expired']:>4}
  │   ⚫ Cancelled : {bs['Cancelled']:>4}
  │   ─────────────────────────────────
  │   Unique Users    : {st['users']}
  │   Unique Services : {st['services']}
  │   Monthly Revenue : ${st['active_revenue']:>10,.2f}
  └{'─' * 58}""")


# ─────────────────────────────────────────────
#  CLI HELPERS
# ─────────────────────────────────────────────

def _clear():
    os.system("cls" if os.name == "nt" else "clear")

def _inp(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""

def _pause():
    input("\n  Press Enter to continue...")

def _divider():
    print("  " + "─" * 54)

def _banner(sm: SubscriptionManager):
    st = sm.stats()
    print(f"""
╔════════════════════════════════════════════════════════╗
║        📋  Subscription Management System              ║
╚════════════════════════════════════════════════════════╝
  Total: {st['total']}  │  🟢 Active: {st['by_status']['Active']}  │  \
🔴 Expired: {st['by_status']['Expired']}  │  \
⚫ Cancelled: {st['by_status']['Cancelled']}
  Monthly Revenue: ${st['active_revenue']:,.2f}  │  \
Users: {st['users']}  │  Services: {st['services']}""")

def _get_float(prompt: str) -> "float | None":
    raw = _inp(prompt)
    try:
        val = float(raw.replace("$", "").replace(",", ""))
        if val < 0:
            print("  [!] Value cannot be negative.")
            return None
        return val
    except ValueError:
        print("  [!] Please enter a valid number.")
        return None

def _get_id(prompt: str = "Subscription ID") -> "int | None":
    raw = _inp(f"  {prompt}: ")
    if not raw.isdigit():
        print("  [!] Please enter a valid numeric ID.")
        return None
    return int(raw)

def _date_hint() -> str:
    return f"(YYYY-MM-DD, e.g. {date.today().strftime('%Y-%m-%d')})"


# ─────────────────────────────────────────────
#  MENU HANDLERS
# ─────────────────────────────────────────────

def menu_create(sm: SubscriptionManager):
    print("\n  ── Create Subscription ─────────────────────────")
    user    = _inp("  User name      : ")
    service = _inp("  Service name   : ")
    start   = _inp(f"  Start date {_date_hint()}: ")
    end     = _inp(f"  End date   {_date_hint()}: ")
    price   = _get_float("  Monthly price ($): ")
    if price is None:
        return
    sm.create_subscription(user, service, start, end, price)


def menu_update(sm: SubscriptionManager):
    print("\n  ── Update Subscription ─────────────────────────")
    sm.display_all()
    sid = _get_id()
    if sid is None:
        return
    print("  Leave blank to keep current value.")
    service = _inp("  New service name   : ") or None
    end     = _inp(f"  New end date {_date_hint()}: ") or None
    raw_p   = _inp("  New price ($)      : ")
    price   = None
    if raw_p:
        try:
            price = float(raw_p.replace("$", "").replace(",", ""))
        except ValueError:
            print("  [!] Invalid price — skipping price update.")
    sm.update_subscription(sid, service, end, price)


def menu_cancel(sm: SubscriptionManager):
    print("\n  ── Cancel Subscription ─────────────────────────")
    sm.display_all()
    sid = _get_id()
    if sid is None:
        return
    confirm = _inp(f"  Cancel subscription #{sid}? (y/n): ").lower()
    if confirm == "y":
        sm.cancel_subscription(sid)
    else:
        print("  [~] Cancelled.")


def menu_renew(sm: SubscriptionManager):
    print("\n  ── Renew Subscription ──────────────────────────")
    subs = sm.search_by_status("expired") + sm.search_by_status("cancelled") + \
           sm.search_by_status("active")
    sm._print_subscriptions(subs, "Renewable Subscriptions")
    sid = _get_id()
    if sid is None:
        return
    new_end = _inp(f"  New end date {_date_hint()}: ")
    raw_p   = _inp("  New price (blank = keep current): ")
    price   = None
    if raw_p:
        try:
            price = float(raw_p.replace("$", "").replace(",", ""))
        except ValueError:
            print("  [!] Invalid price — keeping current price.")
    sm.renew_subscription(sid, new_end, price)


def menu_search(sm: SubscriptionManager):
    print("""
  ── Search Subscriptions ────────────────────────
    [1] By user name
    [2] By service name
    [3] By status""")
    choice = _inp("  Choice: ")
    print()

    if choice == "1":
        kw = _inp("  User name keyword: ")
        sm._print_subscriptions(sm.search_by_user(kw), f"Results for user '{kw}'")
    elif choice == "2":
        kw = _inp("  Service name keyword: ")
        sm._print_subscriptions(sm.search_by_service(kw), f"Results for service '{kw}'")
    elif choice == "3":
        print("  Statuses: Active / Inactive / Expired / Cancelled")
        st = _inp("  Status: ")
        sm._print_subscriptions(sm.search_by_status(st), f"{st} Subscriptions")
    else:
        print("  [!] Invalid choice.")


def menu_expiry(sm: SubscriptionManager):
    print("\n  ── Expiry Check ────────────────────────────────")
    expired = sm.check_expired()
    if expired:
        print(f"  [!] {len(expired)} subscription(s) newly marked as expired:")
        for s in expired:
            print(f"      • #{s.subscription_id}  {s.user_name} → {s.service_name}")
    else:
        print("  [✓] No newly expired subscriptions.")

    days_raw = _inp("  Check expiring within how many days? [default 7]: ")
    days = int(days_raw) if days_raw.isdigit() else 7
    soon = sm.expiring_soon(days)
    if soon:
        print(f"\n  ⚠️  {len(soon)} subscription(s) expiring within {days} day(s):")
        sm._print_subscriptions(soon, f"Expiring Within {days} Days")
    else:
        print(f"  [✓] No active subscriptions expiring within {days} day(s).")


def menu_delete(sm: SubscriptionManager):
    print("\n  ── Delete Subscription (Permanent) ─────────────")
    sm.display_all()
    sid = _get_id()
    if sid is None:
        return
    confirm = _inp(f"  Permanently delete #{sid}? This cannot be undone. (y/n): ").lower()
    if confirm == "y":
        sm.delete_subscription(sid)
    else:
        print("  [~] Cancelled.")


# ─────────────────────────────────────────────
#  SEED DATA
# ─────────────────────────────────────────────

def _seed(sm: SubscriptionManager):
    today = date.today()
    data = [
        ("alice",   "Netflix",    "2025-01-01", (today + timedelta(days=25)).strftime("%Y-%m-%d"), 15.99),
        ("alice",   "Spotify",    "2025-02-01", (today + timedelta(days=60)).strftime("%Y-%m-%d"), 9.99),
        ("bob",     "YouTube",    "2025-01-15", (today + timedelta(days=5)).strftime("%Y-%m-%d"),  13.99),
        ("bob",     "Adobe CC",   "2025-03-01", (today + timedelta(days=90)).strftime("%Y-%m-%d"), 54.99),
        ("carol",   "Microsoft",  "2025-01-01", (today - timedelta(days=10)).strftime("%Y-%m-%d"), 9.99),
        ("carol",   "Dropbox",    "2025-02-01", (today + timedelta(days=45)).strftime("%Y-%m-%d"), 11.99),
        ("dave",    "GitHub Pro", "2025-01-01", (today - timedelta(days=5)).strftime("%Y-%m-%d"),  4.00),
        ("dave",    "Figma",      "2025-03-01", (today + timedelta(days=120)).strftime("%Y-%m-%d"),15.00),
        ("eve",     "Canva Pro",  "2025-01-01", (today + timedelta(days=3)).strftime("%Y-%m-%d"),  12.99),
        ("frank",   "Notion",     "2025-02-01", (today + timedelta(days=80)).strftime("%Y-%m-%d"), 8.00),
    ]
    for user, service, start, end, price in data:
        sm.create_subscription(user, service, start, end, price)
    # Run initial expiry check silently
    sm.check_expired()


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

MAIN_MENU = """
  ── Main Menu ────────────────────────────────────
    [1] Create subscription
    [2] Update subscription
    [3] Cancel subscription
    [4] Renew subscription
    [5] Search subscriptions
    [6] Display all subscriptions
    [7] Check expired / expiring soon
    [8] Display summary & revenue
    [9] Delete subscription (permanent)
    [0] Exit
  ─────────────────────────────────────────────────"""


def main():
    sm = SubscriptionManager()
    _seed(sm)

    while True:
        _clear()
        _banner(sm)
        print(MAIN_MENU)
        _divider()
        choice = _inp("  Choice: ")
        print()

        if   choice == "1": menu_create(sm)
        elif choice == "2": menu_update(sm)
        elif choice == "3": menu_cancel(sm)
        elif choice == "4": menu_renew(sm)
        elif choice == "5": menu_search(sm)
        elif choice == "6": sm.display_all()
        elif choice == "7": menu_expiry(sm)
        elif choice == "8": sm.display_summary()
        elif choice == "9": menu_delete(sm)
        elif choice == "0":
            print("  Goodbye! 👋\n")
            break
        else:
            print("  [!] Invalid option. Please choose from the menu.")

        _pause()


if __name__ == "__main__":
    main()