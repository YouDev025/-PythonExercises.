"""
Project Management System
An OOP-based system for managing projects and tasks with a CLI menu.
"""

from datetime import datetime, date, timedelta


# ─────────────────────────────────────────────
#  TASK CLASS
# ─────────────────────────────────────────────

class Task:
    """Represents a single task belonging to a project."""

    STATUS_TODO       = "To Do"
    STATUS_IN_PROGRESS = "In Progress"
    STATUS_DONE       = "Done"
    STATUS_BLOCKED    = "Blocked"
    VALID_STATUSES    = {STATUS_TODO, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_BLOCKED}

    PRIORITY_LOW    = "Low"
    PRIORITY_MEDIUM = "Medium"
    PRIORITY_HIGH   = "High"
    VALID_PRIORITIES = {PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH}

    def __init__(self, task_id: int, title: str, assigned_to: str = "Unassigned",
                 deadline: str = "", priority: str = "Medium", description: str = ""):
        self.__task_id: int       = task_id
        self.__title: str         = self._clean(title, "Title", 100)
        self.__assigned_to: str   = assigned_to.strip() or "Unassigned"
        self.__deadline: date | None = self._parse_date(deadline) if deadline.strip() else None
        self.__priority: str      = self._validate_priority(priority)
        self.__description: str   = description.strip()
        self.__status: str        = self.STATUS_TODO
        self.__created_at: str    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.__updated_at: str    = self.__created_at

    # ── Validators ──────────────────────────────

    @staticmethod
    def _clean(value: str, label: str, max_len: int = 60) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{label} cannot be empty.")
        if len(value) > max_len:
            raise ValueError(f"{label} must be {max_len} characters or fewer.")
        return value

    @staticmethod
    def _parse_date(value: str) -> date:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
        raise ValueError("Date must be in YYYY-MM-DD format.")

    @staticmethod
    def _validate_priority(p: str) -> str:
        p = p.strip().capitalize()
        if p not in Task.VALID_PRIORITIES:
            raise ValueError(f"Priority must be Low, Medium, or High.")
        return p

    def _touch(self):
        self.__updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Read-only properties ────────────────────

    @property
    def task_id(self) -> int:
        return self.__task_id

    @property
    def title(self) -> str:
        return self.__title

    @property
    def assigned_to(self) -> str:
        return self.__assigned_to

    @property
    def deadline(self) -> "date | None":
        return self.__deadline

    @property
    def priority(self) -> str:
        return self.__priority

    @property
    def description(self) -> str:
        return self.__description

    @property
    def status(self) -> str:
        return self.__status

    @property
    def created_at(self) -> str:
        return self.__created_at

    @property
    def updated_at(self) -> str:
        return self.__updated_at

    @property
    def is_overdue(self) -> bool:
        return (self.__deadline is not None
                and self.__deadline < date.today()
                and self.__status != self.STATUS_DONE)

    @property
    def days_until_deadline(self) -> "int | None":
        if self.__deadline is None:
            return None
        return (self.__deadline - date.today()).days

    # ── Mutations ───────────────────────────────

    def update_status(self, status: str):
        status = status.strip()
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Choose from: {sorted(self.VALID_STATUSES)}")
        self.__status = status
        self._touch()

    def assign(self, user: str):
        user = user.strip()
        if not user:
            raise ValueError("Assignee name cannot be empty.")
        self.__assigned_to = user
        self._touch()

    def update(self, title: str | None = None, deadline: str | None = None,
               priority: str | None = None, description: str | None = None):
        if title is not None:
            self.__title = self._clean(title, "Title", 100)
        if deadline is not None:
            self.__deadline = self._parse_date(deadline) if deadline.strip() else None
        if priority is not None:
            self.__priority = self._validate_priority(priority)
        if description is not None:
            self.__description = description.strip()
        self._touch()

    # ── Display ─────────────────────────────────

    def to_dict(self) -> dict:
        dl = self.__deadline.strftime("%Y-%m-%d") if self.__deadline else "—"
        return {
            "Task ID":    self.__task_id,
            "Title":      self.__title,
            "Assigned":   self.__assigned_to,
            "Priority":   self.__priority,
            "Deadline":   dl,
            "Status":     self.__status,
            "Description": self.__description or "—",
            "Created":    self.__created_at,
            "Updated":    self.__updated_at,
        }

    def __repr__(self) -> str:
        return f"Task(id={self.__task_id}, title='{self.__title}', status='{self.__status}')"


# ─────────────────────────────────────────────
#  PROJECT CLASS
# ─────────────────────────────────────────────

class Project:
    """Represents a project containing multiple tasks."""

    STATUS_PLANNING   = "Planning"
    STATUS_ACTIVE     = "Active"
    STATUS_ON_HOLD    = "On Hold"
    STATUS_COMPLETED  = "Completed"
    STATUS_CANCELLED  = "Cancelled"
    VALID_STATUSES    = {STATUS_PLANNING, STATUS_ACTIVE, STATUS_ON_HOLD,
                         STATUS_COMPLETED, STATUS_CANCELLED}

    def __init__(self, project_id: int, project_name: str, description: str = "",
                 start_date: str = "", end_date: str = ""):
        self.__project_id: int    = project_id
        self.__project_name: str  = self._clean(project_name, "Project name", 80)
        self.__description: str   = description.strip()
        self.__start_date: date   = (Task._parse_date(start_date) if start_date.strip()
                                     else date.today())
        self.__end_date: date | None = (Task._parse_date(end_date) if end_date.strip()
                                        else None)
        self.__status: str        = self.STATUS_PLANNING
        self.__tasks: list[Task]  = []
        self.__next_task_id: int  = 1
        self.__created_at: str    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.__end_date and self.__end_date < self.__start_date:
            raise ValueError("End date must be on or after start date.")

    @staticmethod
    def _clean(value: str, label: str, max_len: int = 80) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{label} cannot be empty.")
        if len(value) > max_len:
            raise ValueError(f"{label} must be {max_len} characters or fewer.")
        return value

    # ── Read-only properties ────────────────────

    @property
    def project_id(self) -> int:
        return self.__project_id

    @property
    def project_name(self) -> str:
        return self.__project_name

    @property
    def description(self) -> str:
        return self.__description

    @property
    def start_date(self) -> date:
        return self.__start_date

    @property
    def end_date(self) -> "date | None":
        return self.__end_date

    @property
    def status(self) -> str:
        return self.__status

    @property
    def created_at(self) -> str:
        return self.__created_at

    @property
    def task_count(self) -> int:
        return len(self.__tasks)

    @property
    def completion_pct(self) -> int:
        if not self.__tasks:
            return 0
        done = sum(1 for t in self.__tasks if t.status == Task.STATUS_DONE)
        return round(done / len(self.__tasks) * 100)

    # ── Status mutation ─────────────────────────

    def update_status(self, status: str):
        status = status.strip()
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Choose from: {sorted(self.VALID_STATUSES)}")
        self.__status = status

    def update_details(self, project_name: str | None = None,
                       description: str | None = None,
                       end_date: str | None = None):
        if project_name is not None:
            self.__project_name = self._clean(project_name, "Project name", 80)
        if description is not None:
            self.__description = description.strip()
        if end_date is not None:
            parsed = Task._parse_date(end_date) if end_date.strip() else None
            if parsed and parsed < self.__start_date:
                raise ValueError("End date cannot be before start date.")
            self.__end_date = parsed

    # ── Task management ─────────────────────────

    def _next_tid(self) -> int:
        tid = self.__next_task_id
        self.__next_task_id += 1
        return tid

    def add_task(self, title: str, assigned_to: str = "Unassigned",
                 deadline: str = "", priority: str = "Medium",
                 description: str = "") -> "Task | None":
        try:
            task = Task(self._next_tid(), title, assigned_to, deadline, priority, description)
            self.__tasks.append(task)
            return task
        except ValueError as exc:
            print(f"  [!] {exc}")
            return None

    def remove_task(self, task_id: int) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        self.__tasks.remove(task)
        return True

    def get_task(self, task_id: int) -> "Task | None":
        return next((t for t in self.__tasks if t.task_id == task_id), None)

    def get_tasks(self, status: str | None = None) -> list[Task]:
        if status:
            return [t for t in self.__tasks if t.status == status]
        return list(self.__tasks)

    def get_overdue_tasks(self) -> list[Task]:
        return [t for t in self.__tasks if t.is_overdue]

    def get_tasks_by_user(self, user: str) -> list[Task]:
        return [t for t in self.__tasks if t.assigned_to.lower() == user.strip().lower()]

    # ── Stats ────────────────────────────────────

    def task_stats(self) -> dict:
        tasks = self.__tasks
        return {
            s: sum(1 for t in tasks if t.status == s)
            for s in Task.VALID_STATUSES
        }


# ─────────────────────────────────────────────
#  PROJECT MANAGER CLASS
# ─────────────────────────────────────────────

class ProjectManager:
    """Top-level manager for all projects."""

    def __init__(self):
        self.__projects: dict[int, Project] = {}
        self.__next_id: int = 1

    def _next_id(self) -> int:
        uid = self.__next_id
        self.__next_id += 1
        return uid

    def _get(self, pid: int) -> "Project | None":
        return self.__projects.get(pid)

    def _all(self) -> list[Project]:
        return list(self.__projects.values())

    # ── Project CRUD ─────────────────────────────

    def create_project(self, project_name: str, description: str = "",
                       start_date: str = "", end_date: str = "") -> "Project | None":
        try:
            p = Project(self._next_id(), project_name, description, start_date, end_date)
            self.__projects[p.project_id] = p
            print(f"  [✓] Project #{p.project_id} '{p.project_name}' created.")
            return p
        except ValueError as exc:
            print(f"  [!] {exc}")
            return None

    def update_project(self, pid: int, project_name: str | None = None,
                       description: str | None = None,
                       end_date: str | None = None,
                       status: str | None = None) -> bool:
        p = self._get(pid)
        if not p:
            print(f"  [!] Project #{pid} not found.")
            return False
        try:
            p.update_details(project_name, description, end_date)
            if status:
                p.update_status(status)
            print(f"  [✓] Project #{pid} updated.")
            return True
        except ValueError as exc:
            print(f"  [!] {exc}")
            return False

    def delete_project(self, pid: int) -> bool:
        if pid not in self.__projects:
            print(f"  [!] Project #{pid} not found.")
            return False
        name = self.__projects[pid].project_name
        del self.__projects[pid]
        print(f"  [✓] Project '{name}' deleted.")
        return True

    # ── Task operations ──────────────────────────

    def add_task(self, pid: int, title: str, assigned_to: str = "Unassigned",
                 deadline: str = "", priority: str = "Medium",
                 description: str = "") -> "Task | None":
        p = self._get(pid)
        if not p:
            print(f"  [!] Project #{pid} not found.")
            return None
        task = p.add_task(title, assigned_to, deadline, priority, description)
        if task:
            print(f"  [✓] Task #{task.task_id} '{task.title}' added to project #{pid}.")
        return task

    def update_task_status(self, pid: int, task_id: int, status: str) -> bool:
        p = self._get(pid)
        if not p:
            print(f"  [!] Project #{pid} not found.")
            return False
        task = p.get_task(task_id)
        if not task:
            print(f"  [!] Task #{task_id} not found in project #{pid}.")
            return False
        try:
            task.update_status(status)
            print(f"  [✓] Task #{task_id} status → '{status}'.")
            return True
        except ValueError as exc:
            print(f"  [!] {exc}")
            return False

    def assign_task(self, pid: int, task_id: int, user: str) -> bool:
        p = self._get(pid)
        if not p:
            print(f"  [!] Project #{pid} not found.")
            return False
        task = p.get_task(task_id)
        if not task:
            print(f"  [!] Task #{task_id} not found in project #{pid}.")
            return False
        try:
            task.assign(user)
            print(f"  [✓] Task #{task_id} assigned to '{user}'.")
            return True
        except ValueError as exc:
            print(f"  [!] {exc}")
            return False

    def update_task(self, pid: int, task_id: int, title: str | None = None,
                    deadline: str | None = None, priority: str | None = None,
                    description: str | None = None) -> bool:
        p = self._get(pid)
        if not p:
            print(f"  [!] Project #{pid} not found.")
            return False
        task = p.get_task(task_id)
        if not task:
            print(f"  [!] Task #{task_id} not found in project #{pid}.")
            return False
        try:
            task.update(title, deadline, priority, description)
            print(f"  [✓] Task #{task_id} updated.")
            return True
        except ValueError as exc:
            print(f"  [!] {exc}")
            return False

    def remove_task(self, pid: int, task_id: int) -> bool:
        p = self._get(pid)
        if not p:
            print(f"  [!] Project #{pid} not found.")
            return False
        if p.remove_task(task_id):
            print(f"  [✓] Task #{task_id} removed from project #{pid}.")
            return True
        print(f"  [!] Task #{task_id} not found in project #{pid}.")
        return False

    # ── Search & reports ─────────────────────────

    def search_projects(self, keyword: str) -> list[Project]:
        kw = keyword.strip().lower()
        return [p for p in self._all()
                if kw in p.project_name.lower() or kw in p.description.lower()]

    def all_overdue_tasks(self) -> list[tuple[Project, Task]]:
        result = []
        for p in self._all():
            for t in p.get_overdue_tasks():
                result.append((p, t))
        return result

    def tasks_by_user(self, user: str) -> list[tuple[Project, Task]]:
        result = []
        for p in self._all():
            for t in p.get_tasks_by_user(user):
                result.append((p, t))
        return result

    def global_stats(self) -> dict:
        projects = self._all()
        all_tasks = [t for p in projects for t in p.get_tasks()]
        by_status = {s: sum(1 for t in all_tasks if t.status == s)
                     for s in Task.VALID_STATUSES}
        proj_status = {s: sum(1 for p in projects if p.status == s)
                       for s in Project.VALID_STATUSES}
        return {
            "projects":       len(projects),
            "proj_by_status": proj_status,
            "total_tasks":    len(all_tasks),
            "task_by_status": by_status,
            "overdue":        sum(1 for t in all_tasks if t.is_overdue),
        }

    # ── Display ──────────────────────────────────

    TASK_STATUS_ICONS = {
        Task.STATUS_TODO:        "⬜",
        Task.STATUS_IN_PROGRESS: "🔵",
        Task.STATUS_DONE:        "✅",
        Task.STATUS_BLOCKED:     "🚫",
    }
    PRIORITY_ICONS = {
        Task.PRIORITY_LOW:    "🟢",
        Task.PRIORITY_MEDIUM: "🟡",
        Task.PRIORITY_HIGH:   "🔴",
    }
    PROJECT_STATUS_ICONS = {
        Project.STATUS_PLANNING:  "📐",
        Project.STATUS_ACTIVE:    "🚀",
        Project.STATUS_ON_HOLD:   "⏸️ ",
        Project.STATUS_COMPLETED: "🏁",
        Project.STATUS_CANCELLED: "❌",
    }

    def display_project(self, pid: int, show_tasks: bool = True):
        _today = date.today()  # computed once for entire render
        p = self._get(pid)
        if not p:
            print(f"  [!] Project #{pid} not found.")
            return
        picon = self.PROJECT_STATUS_ICONS.get(p.status, "•")
        end   = p.end_date.strftime("%Y-%m-%d") if p.end_date else "—"
        bar   = self._progress_bar(p.completion_pct)
        stats = p.task_stats()

        print(f"""
  ┌─ Project #{p.project_id} {'─' * 44}
  │  {picon} {p.project_name}  [{p.status}]
  │  📅 {p.start_date} → {end}
  │  📝 {p.description or '(no description)'}
  │  Progress: {bar} {p.completion_pct}%
  │  Tasks: {p.task_count}  ⬜{stats['To Do']} 🔵{stats['In Progress']} ✅{stats['Done']} 🚫{stats['Blocked']}""")

        if show_tasks:
            tasks = p.get_tasks()
            if tasks:
                print(f"  │  {'─' * 52}")
                for t in tasks:
                    ticon = self.TASK_STATUS_ICONS.get(t.status, "•")
                    prio  = self.PRIORITY_ICONS.get(t.priority, "")
                    dl    = t.deadline.strftime("%Y-%m-%d") if t.deadline else "—"
                    overdue = "  ⚠️  OVERDUE" if t.is_overdue else ""
                    print(f"  │  {ticon} #{t.task_id:<3} {prio} {t.title:<30} "
                          f"→ {t.assigned_to:<15} 📅{dl}{overdue}")
            else:
                print("  │  (no tasks yet)")
        print(f"  └{'─' * 56}")

    def display_all(self, show_tasks: bool = True):
        projects = self._all()
        if not projects:
            print("  [~] No projects found.")
            return
        for p in projects:
            self.display_project(p.project_id, show_tasks)

    def display_summary(self):
        st = self.global_stats()
        bs = st["task_by_status"]
        ps = st["proj_by_status"]
        print(f"""
  ┌─ Global Summary {'─' * 42}
  │  PROJECTS ({st['projects']})
  │    📐 Planning   : {ps.get('Planning', 0):>3}
  │    🚀 Active     : {ps.get('Active', 0):>3}
  │    ⏸️  On Hold    : {ps.get('On Hold', 0):>3}
  │    🏁 Completed  : {ps.get('Completed', 0):>3}
  │    ❌ Cancelled  : {ps.get('Cancelled', 0):>3}
  │  {'─' * 40}
  │  TASKS ({st['total_tasks']})
  │    ⬜ To Do       : {bs.get('To Do', 0):>3}
  │    🔵 In Progress : {bs.get('In Progress', 0):>3}
  │    ✅ Done        : {bs.get('Done', 0):>3}
  │    🚫 Blocked     : {bs.get('Blocked', 0):>3}
  │    ⚠️  Overdue     : {st['overdue']:>3}
  └{'─' * 58}""")

    @staticmethod
    def _progress_bar(pct: int, width: int = 20) -> str:
        filled = round(pct / 100 * width)
        return "[" + "█" * filled + "░" * (width - filled) + "]"

    def list_project_names(self) -> list[str]:
        return [f"#{p.project_id} {p.project_name}" for p in self._all()]


# ─────────────────────────────────────────────
#  CLI HELPERS
# ─────────────────────────────────────────────

def _clear():
    # ANSI escape: instant, no subprocess spawn
    print("\033[2J\033[H", end="", flush=True)

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

def _banner(pm: ProjectManager):
    st = pm.global_stats()
    print(f"""
╔══════════════════════════════════════════════════════════╗
║           📁  Project Management System                  ║
╚══════════════════════════════════════════════════════════╝
  Projects: {st['projects']}  │  Tasks: {st['total_tasks']}  │  \
✅ Done: {st['task_by_status'].get('Done', 0)}  │  \
🔵 In Progress: {st['task_by_status'].get('In Progress', 0)}  │  \
⚠️  Overdue: {st['overdue']}""")

def _get_id(label: str) -> "int | None":
    raw = _inp(f"  {label}: ")
    if not raw.isdigit():
        print("  [!] Please enter a valid numeric ID.")
        return None
    return int(raw)

def _date_hint() -> str:
    return f"YYYY-MM-DD, e.g. {date.today().strftime('%Y-%m-%d')}"

def _pick_status(options: set, label: str = "Status") -> "str | None":
    sorted_opts = sorted(options)
    for i, s in enumerate(sorted_opts, 1):
        print(f"    [{i}] {s}")
    raw = _inp(f"  {label}: ")
    if raw.isdigit() and 1 <= int(raw) <= len(sorted_opts):
        return sorted_opts[int(raw) - 1]
    if raw in options:
        return raw
    print(f"  [!] Invalid choice.")
    return None


# ─────────────────────────────────────────────
#  MENU HANDLERS
# ─────────────────────────────────────────────

def menu_create_project(pm: ProjectManager):
    print("\n  ── Create Project ───────────────────────────────")
    name  = _inp("  Project name  : ")
    desc  = _inp("  Description   : ")
    start = _inp(f"  Start date ({_date_hint()}) [Enter=today]: ")
    end   = _inp(f"  End date   ({_date_hint()}) [Enter=none] : ")
    pm.create_project(name, desc, start, end)


def menu_update_project(pm: ProjectManager):
    print("\n  ── Update Project ───────────────────────────────")
    names = pm.list_project_names()
    if names:
        print("  Projects: " + "  |  ".join(names))
    pid = _get_id("Project ID")
    if pid is None:
        return
    print("  Leave blank to keep current value.")
    name  = _inp("  New project name : ") or None
    desc  = _inp("  New description  : ") or None
    end   = _inp(f"  New end date ({_date_hint()}): ") or None
    print("  New status:")
    status = _pick_status(Project.VALID_STATUSES)
    pm.update_project(pid, name, desc, end, status)


def menu_delete_project(pm: ProjectManager):
    print("\n  ── Delete Project ───────────────────────────────")
    pm.display_all(show_tasks=False)
    pid = _get_id("Project ID to delete")
    if pid is None:
        return
    confirm = _inp(f"  Delete project #{pid} and all its tasks? (y/n): ").lower()
    if confirm == "y":
        pm.delete_project(pid)
    else:
        print("  [~] Cancelled.")


def menu_add_task(pm: ProjectManager):
    print("\n  ── Add Task ─────────────────────────────────────")
    names = pm.list_project_names()
    if names:
        print("  Projects: " + "  |  ".join(names))
    pid = _get_id("Project ID")
    if pid is None:
        return
    title   = _inp("  Task title    : ")
    user    = _inp("  Assign to     : ")
    dl      = _inp(f"  Deadline ({_date_hint()}) [Enter=none]: ")
    print("  Priority: [1] Low  [2] Medium  [3] High")
    p_map   = {"1": "Low", "2": "Medium", "3": "High"}
    prio    = p_map.get(_inp("  Choice [default Medium]: "), "Medium")
    desc    = _inp("  Description   : ")
    pm.add_task(pid, title, user, dl, prio, desc)


def menu_update_task_status(pm: ProjectManager):
    print("\n  ── Update Task Status ───────────────────────────")
    names = pm.list_project_names()
    if names:
        print("  Projects: " + "  |  ".join(names))
    pid = _get_id("Project ID")
    if pid is None:
        return
    p = pm._get(pid)
    if not p:
        print(f"  [!] Project #{pid} not found.")
        return
    pm.display_project(pid)
    tid = _get_id("Task ID")
    if tid is None:
        return
    print("  New status:")
    status = _pick_status(Task.VALID_STATUSES)
    if status:
        pm.update_task_status(pid, tid, status)


def menu_assign_task(pm: ProjectManager):
    print("\n  ── Assign Task ──────────────────────────────────")
    names = pm.list_project_names()
    if names:
        print("  Projects: " + "  |  ".join(names))
    pid = _get_id("Project ID")
    if pid is None:
        return
    pm.display_project(pid)
    tid  = _get_id("Task ID")
    if tid is None:
        return
    user = _inp("  Assign to     : ")
    pm.assign_task(pid, tid, user)


def menu_update_task(pm: ProjectManager):
    print("\n  ── Edit Task Details ────────────────────────────")
    names = pm.list_project_names()
    if names:
        print("  Projects: " + "  |  ".join(names))
    pid = _get_id("Project ID")
    if pid is None:
        return
    pm.display_project(pid)
    tid = _get_id("Task ID")
    if tid is None:
        return
    print("  Leave blank to keep current value.")
    title = _inp("  New title      : ") or None
    dl    = _inp(f"  New deadline   : ") or None
    print("  New priority: [1] Low  [2] Medium  [3] High  (blank=keep)")
    p_map = {"1": "Low", "2": "Medium", "3": "High"}
    prio  = p_map.get(_inp("  Choice         : "), None)
    desc  = _inp("  New description: ") or None
    pm.update_task(pid, tid, title, dl, prio, desc)


def menu_remove_task(pm: ProjectManager):
    print("\n  ── Remove Task ──────────────────────────────────")
    names = pm.list_project_names()
    if names:
        print("  Projects: " + "  |  ".join(names))
    pid = _get_id("Project ID")
    if pid is None:
        return
    pm.display_project(pid)
    tid = _get_id("Task ID to remove")
    if tid is None:
        return
    confirm = _inp(f"  Remove task #{tid}? (y/n): ").lower()
    if confirm == "y":
        pm.remove_task(pid, tid)
    else:
        print("  [~] Cancelled.")


def menu_search(pm: ProjectManager):
    print("""
  ── Search ────────────────────────────────────────
    [1] Search projects by keyword
    [2] View all overdue tasks
    [3] Tasks assigned to a user""")
    choice = _inp("  Choice: ")
    print()

    if choice == "1":
        kw = _inp("  Keyword: ")
        results = pm.search_projects(kw)
        if not results:
            print("  [~] No matching projects.")
        else:
            for p in results:
                pm.display_project(p.project_id)

    elif choice == "2":
        overdue = pm.all_overdue_tasks()
        if not overdue:
            print("  [✓] No overdue tasks.")
        else:
            print(f"  ⚠️  {len(overdue)} overdue task(s):\n")
            for proj, task in overdue:
                days = abs(task.days_until_deadline or 0)
                print(f"  🔴 [{proj.project_name}]  Task #{task.task_id}: {task.title}"
                      f"  →  {task.assigned_to}  (overdue by {days}d)")

    elif choice == "3":
        user = _inp("  Username: ")
        results = pm.tasks_by_user(user)
        if not results:
            print(f"  [~] No tasks assigned to '{user}'.")
        else:
            print(f"  Tasks for '{user}' ({len(results)}):\n")
            for proj, task in results:
                ticon = ProjectManager.TASK_STATUS_ICONS.get(task.status, "•")
                dl    = task.deadline.strftime("%Y-%m-%d") if task.deadline else "—"
                print(f"  {ticon} [{proj.project_name}]  #{task.task_id}: {task.title}"
                      f"  [{task.status}]  📅{dl}")
    else:
        print("  [!] Invalid choice.")


# ─────────────────────────────────────────────
#  SEED DATA
# ─────────────────────────────────────────────

def _seed(pm: ProjectManager):
    import io, sys
    _real_stdout = sys.stdout
    sys.stdout = io.StringIO()   # suppress all seed output
    today = date.today()

    p1 = pm.create_project(
        "Website Redesign",
        "Redesign the company website with a modern UI",
        str(today - timedelta(days=30)),
        str(today + timedelta(days=60))
    )
    if p1:
        pm.update_project(p1.project_id, status="Active")
        pm.add_task(p1.project_id, "Wireframe homepage",    "alice",   str(today - timedelta(days=5)),  "High",   "Initial wireframes")
        pm.add_task(p1.project_id, "Design colour palette", "bob",     str(today + timedelta(days=10)), "Medium", "Brand colours")
        pm.add_task(p1.project_id, "Develop nav component", "carol",   str(today + timedelta(days=20)), "High",   "Responsive navbar")
        pm.add_task(p1.project_id, "Write copy for About",  "dave",    str(today + timedelta(days=15)), "Low",    "About Us page text")
        pm.update_task_status(p1.project_id, 1, Task.STATUS_DONE)
        pm.update_task_status(p1.project_id, 2, Task.STATUS_IN_PROGRESS)

    p2 = pm.create_project(
        "Mobile App Launch",
        "Launch the iOS and Android apps for Q3",
        str(today - timedelta(days=10)),
        str(today + timedelta(days=45))
    )
    if p2:
        pm.update_project(p2.project_id, status="Active")
        pm.add_task(p2.project_id, "Set up CI/CD pipeline",  "eve",     str(today + timedelta(days=5)),  "High",   "GitHub Actions")
        pm.add_task(p2.project_id, "Write unit tests",        "alice",   str(today + timedelta(days=12)), "High",   "Core modules")
        pm.add_task(p2.project_id, "Beta testing round 1",    "frank",   str(today - timedelta(days=2)),  "Medium", "Internal testers")
        pm.add_task(p2.project_id, "App Store submission",    "eve",     str(today + timedelta(days=40)), "High",   "Both stores")
        pm.update_task_status(p2.project_id, 3, Task.STATUS_BLOCKED)

    p3 = pm.create_project(
        "Data Migration",
        "Migrate legacy database to PostgreSQL",
        str(today - timedelta(days=60)),
        str(today - timedelta(days=5))
    )
    if p3:
        pm.update_project(p3.project_id, status="Completed")
        pm.add_task(p3.project_id, "Schema mapping",   "carol", str(today - timedelta(days=30)), "High")
        pm.add_task(p3.project_id, "ETL script",       "dave",  str(today - timedelta(days=20)), "High")
        pm.add_task(p3.project_id, "Validation tests", "bob",   str(today - timedelta(days=10)), "Medium")
        for tid in [1, 2, 3]:
            pm.update_task_status(p3.project_id, tid, Task.STATUS_DONE)
    sys.stdout = _real_stdout   # restore stdout


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

MAIN_MENU = """
  ── Main Menu ──────────────────────────────────────
    [1]  Create project
    [2]  Update project
    [3]  Delete project
    ─────────────────────────────────────────────────
    [4]  Add task to project
    [5]  Update task status
    [6]  Assign task to user
    [7]  Edit task details
    [8]  Remove task
    ─────────────────────────────────────────────────
    [9]  Display all projects & tasks
    [10] Display project detail
    [11] Search / reports
    [12] Global summary
    [0]  Exit
  ─────────────────────────────────────────────────"""


def main():
    pm = ProjectManager()
    _seed(pm)

    while True:
        _clear()
        _banner(pm)
        print(MAIN_MENU)
        _divider()
        choice = _inp("  Choice: ")
        print()

        if   choice == "1":  menu_create_project(pm)
        elif choice == "2":  menu_update_project(pm)
        elif choice == "3":  menu_delete_project(pm)
        elif choice == "4":  menu_add_task(pm)
        elif choice == "5":  menu_update_task_status(pm)
        elif choice == "6":  menu_assign_task(pm)
        elif choice == "7":  menu_update_task(pm)
        elif choice == "8":  menu_remove_task(pm)
        elif choice == "9":  pm.display_all()
        elif choice == "10":
            names = pm.list_project_names()
            if names:
                print("  Projects: " + "  |  ".join(names))
            pid = _get_id("Project ID")
            if pid:
                pm.display_project(pid)
        elif choice == "11": menu_search(pm)
        elif choice == "12": pm.display_summary()
        elif choice == "0":
            print("  Goodbye! 👋\n")
            break
        else:
            print("  [!] Invalid option. Please choose from the menu.")

        _pause()


if __name__ == "__main__":
    main()