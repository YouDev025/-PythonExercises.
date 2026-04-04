#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║       HTTP Request Smuggling — Educational Simulator  v1.0          ║
║       Pure simulation — NO real network traffic                      ║
║       For learning and authorized security research ONLY             ║
╚══════════════════════════════════════════════════════════════════════╝

Theory refresher
────────────────
HTTP Request Smuggling exploits disagreements between a front-end proxy
and a back-end server about where one HTTP request ends and the next
begins.  The two headers that control body length are:

  Content-Length (CL)   – body is exactly N bytes long
  Transfer-Encoding (TE) – body is chunked; ends with a "0\r\n\r\n" chunk

When a proxy trusts CL but the back-end trusts TE (CL.TE), or vice-versa
(TE.CL), an attacker can "smuggle" a prefix of the next request into the
current one, poisoning what the back-end sees as subsequent traffic.
"""

import textwrap
import time
import sys
import os

# ──────────────────────────────────────────────────────────────────────
# ANSI COLOUR HELPERS
# ──────────────────────────────────────────────────────────────────────
if sys.platform == "win32":
    os.system("color")                        # enable VT100 on Windows

R   = "\033[91m"   # red
G   = "\033[92m"   # green
Y   = "\033[93m"   # yellow
B   = "\033[94m"   # blue
M   = "\033[95m"   # magenta
C   = "\033[96m"   # cyan
W   = "\033[97m"   # white
DIM = "\033[2m"
BLD = "\033[1m"
RST = "\033[0m"

def clr(text: str, colour: str) -> str:
    return f"{colour}{text}{RST}"

def header_line(title: str, width: int = 70, ch: str = "═") -> str:
    pad = (width - len(title) - 2) // 2
    return clr(f"{'═'*pad} {title} {'═'*(width-pad-len(title)-2)}", C)

def sub_line(title: str, width: int = 70, ch: str = "─") -> str:
    return clr(f"{'─'*3} {title} {'─'*(width-len(title)-5)}", DIM)

def pause(msg: str = "  ► Press Enter to continue…") -> None:
    input(clr(msg, Y))

def slow_print(text: str, delay: float = 0.012) -> None:
    """Print text character by character for dramatic effect."""
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()


# ──────────────────────────────────────────────────────────────────────
# RAW HTTP FORMATTING HELPERS
# ──────────────────────────────────────────────────────────────────────

def fmt_request(raw: str, label: str = "", highlight_lines: list[int] | None = None) -> str:
    """
    Pretty-print a raw HTTP request string.
    highlight_lines: 0-based line indices to colour red.
    """
    highlight_lines = highlight_lines or []
    lines = raw.split("\n")
    out = []
    if label:
        out.append(clr(f"  ┌── {label}", M))
    for i, line in enumerate(lines):
        prefix = "  │  "
        if i == 0:                                      # request line
            out.append(prefix + clr(line, BLD + W))
        elif ":" in line and i < lines.index(""):       # header (before blank)
            key, _, val = line.partition(":")
            coloured_val = clr(val, R) if i in highlight_lines else clr(val, G)
            out.append(prefix + clr(key + ":", Y) + coloured_val)
        elif line == "":
            out.append(prefix)
        else:                                            # body
            body_colour = R if i in highlight_lines else C
            out.append(prefix + clr(line, body_colour))
    if label:
        out.append(clr("  └" + "─" * 50, M))
    return "\n".join(out)


def fmt_box(title: str, lines: list[str], colour: str = C) -> str:
    """Render a titled box around a list of text lines."""
    width = max(len(title) + 4, max(len(l) for l in lines) + 4)
    top    = colour + "┌─ " + title + " " + "─" * (width - len(title) - 3) + "┐" + RST
    bottom = colour + "└" + "─" * (width + 1) + "┘" + RST
    body   = "\n".join(colour + "│ " + RST + l.ljust(width - 1) + colour + "│" + RST
                       for l in lines)
    return "\n".join([top, body, bottom])


# ──────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ──────────────────────────────────────────────────────────────────────

class HTTPRequest:
    """Represents a raw HTTP/1.1 request as a string + parsed metadata."""

    def __init__(self, method: str, path: str, headers: dict[str, str],
                 body: str = ""):
        self.method  = method
        self.path    = path
        self.headers = headers          # ordered dict
        self.body    = body

    # ── serialise ──────────────────────────────────────────────────────
    def to_raw(self) -> str:
        lines = [f"{self.method} {self.path} HTTP/1.1"]
        for k, v in self.headers.items():
            lines.append(f"{k}: {v}")
        lines.append("")               # blank line separating headers/body
        lines.append(self.body)
        return "\n".join(lines)

    # ── parsing helpers ────────────────────────────────────────────────
    def get_content_length(self) -> int | None:
        for k, v in self.headers.items():
            if k.lower() == "content-length":
                try:
                    return int(v.strip())
                except ValueError:
                    return None
        return None

    def get_transfer_encoding(self) -> str | None:
        for k, v in self.headers.items():
            if k.lower() == "transfer-encoding":
                return v.strip().lower()
        return None

    def has_header(self, name: str) -> bool:
        return any(k.lower() == name.lower() for k in self.headers)

    # ── highlight indices for fmt_request ─────────────────────────────
    def highlight_indices(self, *names: str) -> list[int]:
        """Return line indices (0-based) of headers matching *names*."""
        raw_lines = self.to_raw().split("\n")
        result = []
        for i, line in enumerate(raw_lines):
            for name in names:
                if line.lower().startswith(name.lower() + ":"):
                    result.append(i)
        return result


class SimulationResult:
    """Captures what one pipeline stage saw / did with a request."""

    def __init__(self, component: str):
        self.component   = component   # "Front-End Proxy" | "Back-End Server"
        self.consumed    = ""          # bytes this component treated as the request
        self.leftover    = ""          # bytes left in buffer (poisoned prefix)
        self.rule_used   = ""          # "Content-Length" | "Transfer-Encoding"
        self.notes: list[str] = []

    def add_note(self, note: str) -> None:
        self.notes.append(note)

    def display(self) -> None:
        colour = B if "Front" in self.component else M
        print(fmt_box(
            self.component,
            [
                f"Rule applied : {clr(self.rule_used, Y)}",
                f"Consumed     : {clr(repr(self.consumed[:80]), G)}",
                f"Leftover     : {clr(repr(self.leftover[:80]) if self.leftover else '(none)', R if self.leftover else DIM)}",
                *[f"Note         : {n}" for n in self.notes],
            ],
            colour=colour,
        ))
        print()


# ──────────────────────────────────────────────────────────────────────
# PIPELINE COMPONENTS
# ──────────────────────────────────────────────────────────────────────

class FrontEndProxy:
    """
    Simulates a load-balancer / reverse proxy.
    Typically trusts Content-Length and forwards the raw bytes onward.
    In CL.TE attacks it ignores Transfer-Encoding.
    In TE.CL attacks it trusts Transfer-Encoding.
    """

    def __init__(self, trust: str = "CL"):
        """
        trust : "CL"  → proxy uses Content-Length  (CL.TE scenario)
                "TE"  → proxy uses Transfer-Encoding (TE.CL scenario)
        """
        self.trust = trust.upper()
        self.buffer: str = ""           # simulated TCP receive buffer

    def receive(self, raw: str) -> SimulationResult:
        """Ingest a raw HTTP request string and decide what to forward."""
        self.buffer = raw
        result = SimulationResult("Front-End Proxy")

        if self.trust == "CL":
            result.rule_used = "Content-Length (ignores Transfer-Encoding)"
            cl = self._extract_cl(raw)
            body_start = raw.find("\n\n") + 2
            body = raw[body_start:]

            if cl is not None:
                # Proxy forwards exactly Content-Length bytes of body
                forwarded_body = body[:cl]
                result.consumed = raw[:body_start] + forwarded_body
                result.leftover = body[cl:]          # smuggled suffix stays in pipe
                result.add_note(
                    f"Content-Length = {cl}, forwarded {len(forwarded_body)} body bytes"
                )
            else:
                result.consumed = raw
                result.add_note("No Content-Length; forwarded entire request")

        elif self.trust == "TE":
            result.rule_used = "Transfer-Encoding: chunked (ignores Content-Length)"
            chunks, leftover = self._decode_chunks(raw)
            result.consumed = self._reassembled(raw, chunks)
            result.leftover = leftover
            result.add_note(
                f"Decoded chunked body, reassembled {len(chunks)} chunk(s)"
            )
        else:
            result.rule_used = "Unknown"
            result.consumed = raw

        return result

    # ── private helpers ────────────────────────────────────────────────
    @staticmethod
    def _extract_cl(raw: str) -> int | None:
        for line in raw.split("\n"):
            if line.lower().startswith("content-length:"):
                try:
                    return int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
        return None

    @staticmethod
    def _decode_chunks(raw: str) -> tuple[list[str], str]:
        """
        Very simplified chunked-decoding simulation.
        Returns (list_of_chunk_data, leftover_after_terminal_chunk).
        """
        body_start = raw.find("\n\n") + 2
        body = raw[body_start:]
        chunks = []
        leftover = ""
        lines = body.split("\n")
        i = 0
        while i < len(lines):
            size_line = lines[i].strip()
            try:
                size = int(size_line, 16)
            except ValueError:
                break
            if size == 0:
                # terminal chunk — everything after is leftover/smuggled
                leftover = "\n".join(lines[i + 1:]).lstrip("\n")
                break
            i += 1
            if i < len(lines):
                chunks.append(lines[i])
            i += 1
        return chunks, leftover

    @staticmethod
    def _reassembled(raw: str, chunks: list[str]) -> str:
        """Return headers + reassembled body."""
        headers_part = raw[: raw.find("\n\n") + 2]
        return headers_part + "".join(chunks)


class BackEndServer:
    """
    Simulates an origin / application server.
    In CL.TE attacks it trusts Transfer-Encoding (opposite of proxy).
    In TE.CL attacks it trusts Content-Length.
    """

    def __init__(self, trust: str = "TE"):
        self.trust  = trust.upper()
        self.buffer = ""

    def receive(self, forwarded: str, leftover: str = "") -> SimulationResult:
        """
        Ingest what the proxy forwarded PLUS any leftover bytes the proxy
        did not consume (simulating a persistent connection / pipe).
        """
        # In a real pipeline the back-end sees the proxy-forwarded bytes
        # immediately followed by the next client request.  Here we
        # represent that by appending leftover to the forwarded data.
        self.buffer = forwarded + leftover
        result = SimulationResult("Back-End Server")

        if self.trust == "TE":
            result.rule_used = "Transfer-Encoding: chunked"
            chunks, smuggled = FrontEndProxy._decode_chunks(self.buffer)
            result.consumed = FrontEndProxy._reassembled(self.buffer, chunks)
            result.leftover = smuggled
            if smuggled:
                result.add_note(
                    clr("⚠  Smuggled prefix detected in back-end buffer!", R)
                )
                result.add_note(
                    f"Back-end will prepend {clr(repr(smuggled), R)} to the NEXT request"
                )
            else:
                result.add_note("Decoded chunked body cleanly — no leftover")

        elif self.trust == "CL":
            result.rule_used = "Content-Length"
            cl = FrontEndProxy._extract_cl(self.buffer)
            body_start = self.buffer.find("\n\n") + 2
            body = self.buffer[body_start:]
            if cl is not None:
                result.consumed = self.buffer[:body_start] + body[:cl]
                result.leftover = body[cl:]
                if result.leftover:
                    result.add_note(
                        clr("⚠  Extra bytes beyond Content-Length in buffer!", R)
                    )
                    result.add_note(
                        f"Back-end will prepend {clr(repr(result.leftover), R)} to the NEXT request"
                    )
            else:
                result.consumed = self.buffer
                result.add_note("No Content-Length; consumed entire buffer")

        return result


# ──────────────────────────────────────────────────────────────────────
# SCENARIO BUILDERS
# ──────────────────────────────────────────────────────────────────────

def make_normal_request() -> HTTPRequest:
    return HTTPRequest(
        method="POST",
        path="/api/data",
        headers={
            "Host": "vulnerable-site.com",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": "11",
        },
        body="hello=world",
    )


def make_clte_smuggling_request() -> HTTPRequest:
    """
    CL.TE attack payload.
    Front-end uses Content-Length  →  sees 49 bytes of body (includes the chunk).
    Back-end  uses Transfer-Encoding → decodes chunks, stops at '0', keeps 'GPOST'
              as the start of the *next* request.
    """
    body = (
        "4\n"           # chunk size: 4 bytes
        "Wiki\n"        # chunk data
        "0\n"           # terminal chunk
        "\n"
        "GPOST / HTTP/1.1\n"    # ← smuggled request prefix
        "X-Ignored: x"
    )
    cl_value = len(body.replace("\n", "\r\n"))   # realistic byte count
    return HTTPRequest(
        method="POST",
        path="/search",
        headers={
            "Host": "vulnerable-site.com",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(cl_value),
            "Transfer-Encoding": "chunked",
        },
        body=body,
    )


def make_tecl_smuggling_request() -> HTTPRequest:
    """
    TE.CL attack payload.
    Front-end uses Transfer-Encoding → decodes up to '0' chunk, stops.
    Back-end  uses Content-Length   → reads only 4 bytes ('Wiki'), leaves
              the rest in the buffer as the next request's prefix.
    """
    body = (
        "4\n"
        "Wiki\n"
        "0\n"
        "\n"
        "X-Ignored: smuggled-header"
    )
    return HTTPRequest(
        method="POST",
        path="/search",
        headers={
            "Host": "vulnerable-site.com",
            "Content-Type": "application/x-www-form-urlencoded",
            "Transfer-Encoding": "chunked",
            "Content-Length": "4",          # only covers "Wiki" !
        },
        body=body,
    )


def make_victim_request() -> HTTPRequest:
    """A normal request from an innocent user sent after the smuggled one."""
    return HTTPRequest(
        method="GET",
        path="/inbox",
        headers={
            "Host": "vulnerable-site.com",
            "Cookie": "session=VICTIM_SESSION_TOKEN_abc123",
        },
    )


# ──────────────────────────────────────────────────────────────────────
# SIMULATION RUNNERS
# ──────────────────────────────────────────────────────────────────────

def run_normal_flow() -> None:
    """Demo: a completely normal request that both sides agree on."""
    print("\n" + header_line("NORMAL HTTP REQUEST FLOW"))
    print(clr(textwrap.dedent("""
      In normal operation:
        • Client sends a well-formed POST request
        • Front-end proxy forwards it (unchanged)
        • Back-end server processes it correctly
        • No ambiguity about where the request ends
    """), W))
    pause()

    req = make_normal_request()
    raw = req.to_raw()

    print(sub_line("Client sends"))
    print(fmt_request(raw, label="Raw HTTP Request (client → proxy → backend)"))
    print()
    pause()

    # Both sides use Content-Length and agree
    proxy   = FrontEndProxy(trust="CL")
    backend = BackEndServer(trust="CL")

    p_result = proxy.receive(raw)
    b_result = backend.receive(p_result.consumed, p_result.leftover)

    print(sub_line("Front-End Proxy interpretation"))
    p_result.display()
    pause()

    print(sub_line("Back-End Server interpretation"))
    b_result.display()
    pause()

    print(clr("\n  ✔  Both sides agree — no smuggling possible here.\n", G))
    pause()


def run_clte_attack() -> None:
    """
    Simulate a CL.TE desynchronisation attack.

    Timeline:
      1. Attacker sends a request with BOTH CL and TE headers.
      2. Front-end proxy trusts Content-Length → forwards N bytes which
         include the full chunked body (chunk data + terminal '0' + smuggled prefix).
      3. Back-end trusts Transfer-Encoding → reads chunks, stops at '0',
         leaves the smuggled prefix ('GPOST /...') in its TCP buffer.
      4. Victim's next innocent GET request is prepended with 'GPOST /...'
         → back-end sees a malformed / attacker-controlled request.
    """
    print("\n" + header_line("CL.TE ATTACK SIMULATION"))
    print(clr(textwrap.dedent("""
      Scenario
      ────────
        • Front-End proxy : trusts  Content-Length  (ignores Transfer-Encoding)
        • Back-End server : trusts  Transfer-Encoding (ignores Content-Length)

      The attacker crafts a request that satisfies CL for the proxy
      but contains a chunked body with a smuggled prefix after the
      terminal chunk.  The back-end stops reading at chunk '0' and
      leaves the smuggled bytes in the buffer, poisoning the next request.
    """), W))
    pause()

    # ── Step 1: show the attack request ───────────────────────────────
    print(sub_line("STEP 1 — Attacker's crafted request"))
    req = make_clte_smuggling_request()
    raw = req.to_raw()
    hl  = req.highlight_indices("content-length", "transfer-encoding")
    print(fmt_request(raw, label="Attacker → Front-End (CL & TE both present)", highlight_lines=hl))
    print()
    print(clr("  ↑  Both Content-Length and Transfer-Encoding are present (highlighted).", Y))
    print(clr("     This is the root cause of the desynchronisation.", Y))
    pause()

    # ── Step 2: proxy perspective ──────────────────────────────────────
    print(sub_line("STEP 2 — Front-End Proxy processes request (trusts CL)"))
    proxy    = FrontEndProxy(trust="CL")
    p_result = proxy.receive(raw)
    p_result.display()
    print(clr("  The proxy sees one complete request and forwards ALL bytes", B))
    print(clr("  (including the smuggled suffix after the '0' chunk).", B))
    pause()

    # ── Step 3: backend perspective ───────────────────────────────────
    print(sub_line("STEP 3 — Back-End Server processes request (trusts TE)"))
    backend  = BackEndServer(trust="TE")
    b_result = backend.receive(p_result.consumed, p_result.leftover)
    b_result.display()

    if b_result.leftover:
        print(clr("\n  ══ DESYNCHRONISATION EVENT ══", R + BLD))
        print(clr(f"  Back-end buffer now starts with: {repr(b_result.leftover)}", R))
        print(clr("  This will be PREPENDED to the next request!", R))
    pause()

    # ── Step 4: victim request poisoned ───────────────────────────────
    print(sub_line("STEP 4 — Innocent victim sends a normal GET request"))
    victim_req = make_victim_request()
    print(fmt_request(victim_req.to_raw(), label="Victim's GET /inbox"))
    print()
    print(clr("  The back-end concatenates its poisoned buffer with the victim's request:", R))
    print()

    poisoned = b_result.leftover + "\n" + victim_req.to_raw()
    print(fmt_request(poisoned, label="What back-end actually sees for 'victim request'",
                      highlight_lines=[0, 1]))
    print()
    print(clr("  ⚠  The victim's session token may now appear inside an attacker-controlled", R))
    print(clr("     request body — leaking credentials or triggering privilege escalation.", R))
    pause()

    # ── Step 5: impact summary ────────────────────────────────────────
    print(sub_line("STEP 5 — Impact summary"))
    print(fmt_box("CL.TE Attack Impact", [
        "Attacker controls prefix of victim's request",
        "Session tokens / auth headers may leak to attacker",
        "Back-end may process a completely different endpoint",
        "Access controls (enforced by proxy only) are bypassed",
        "Cache poisoning if responses are cached by the proxy",
    ], colour=R))
    print()
    pause()


def run_tecl_attack() -> None:
    """
    Simulate a TE.CL desynchronisation attack.

    Timeline:
      1. Attacker sends a request with BOTH TE and CL headers.
      2. Front-end trusts Transfer-Encoding → decodes chunks, reassembles
         body as plain text, passes it on.
      3. Back-end trusts Content-Length → reads only CL bytes from body,
         leaving the chunked remainder (+ extra headers) in its buffer.
      4. Back-end uses those leftover bytes as the start of the next request.
    """
    print("\n" + header_line("TE.CL ATTACK SIMULATION"))
    print(clr(textwrap.dedent("""
      Scenario
      ────────
        • Front-End proxy : trusts  Transfer-Encoding (ignores Content-Length)
        • Back-End server : trusts  Content-Length    (ignores Transfer-Encoding)

      The attacker sends a chunked request where Content-Length covers
      only the first chunk's data.  The proxy happily decodes & forwards
      the full chunked body; the back-end reads only CL bytes and treats
      the rest as the beginning of the next HTTP request.
    """), W))
    pause()

    # ── Step 1: show the attack request ───────────────────────────────
    print(sub_line("STEP 1 — Attacker's crafted request"))
    req = make_tecl_smuggling_request()
    raw = req.to_raw()
    hl  = req.highlight_indices("content-length", "transfer-encoding")
    print(fmt_request(raw, label="Attacker → Front-End (TE & CL conflict)", highlight_lines=hl))
    print()
    print(clr("  ↑  Content-Length=4 covers only 'Wiki'.", Y))
    print(clr("     The chunked body extends well beyond that.", Y))
    pause()

    # ── Step 2: proxy (trusts TE) ─────────────────────────────────────
    print(sub_line("STEP 2 — Front-End Proxy processes request (trusts TE)"))
    proxy    = FrontEndProxy(trust="TE")
    p_result = proxy.receive(raw)
    p_result.display()
    print(clr("  Proxy decoded the chunked body and forwarded the reassembled request.", B))
    print(clr("  It included ALL chunk data up to and including the terminal '0' chunk.", B))
    pause()

    # ── Step 3: backend (trusts CL) ───────────────────────────────────
    print(sub_line("STEP 3 — Back-End Server processes request (trusts CL)"))
    backend  = BackEndServer(trust="CL")
    b_result = backend.receive(p_result.consumed, p_result.leftover)
    b_result.display()

    if b_result.leftover:
        print(clr("\n  ══ DESYNCHRONISATION EVENT ══", R + BLD))
        print(clr(f"  Back-end buffer leftover: {repr(b_result.leftover)}", R))
        print(clr("  Next request will be prefixed with attacker-controlled data!", R))
    pause()

    # ── Step 4: victim request poisoned ───────────────────────────────
    print(sub_line("STEP 4 — Victim's request arrives"))
    victim_req = make_victim_request()
    print(fmt_request(victim_req.to_raw(), label="Victim's GET /inbox"))
    print()

    if b_result.leftover:
        poisoned = b_result.leftover + "\n" + victim_req.to_raw()
        print(clr("  Back-end prepends buffer to victim's request:", R))
        print()
        print(fmt_request(poisoned, label="Back-end's combined view", highlight_lines=[0]))
        print()
        print(clr("  ⚠  Extra chunk metadata is now injected as a header/body", R))
        print(clr("     in what the back-end believes is the victim's request.", R))
    pause()

    # ── Step 5: impact summary ────────────────────────────────────────
    print(sub_line("STEP 5 — Impact summary"))
    print(fmt_box("TE.CL Attack Impact", [
        "Back-end reads a different request body than the proxy validated",
        "WAF / ACL rules checked by proxy are completely bypassed",
        "Attacker can inject arbitrary headers into victim's request",
        "Request routing can be manipulated (hit internal-only endpoints)",
        "Amplification: one attacker request poisons many victims",
    ], colour=R))
    print()
    pause()


def run_concept_explainer() -> None:
    """Visual walk-through of the core parsing mechanics."""
    print("\n" + header_line("CORE CONCEPT: WHY PARSING DIFFERS"))
    print(clr(textwrap.dedent("""
      HTTP/1.1 defines TWO ways to specify body length.  RFC 7230 says:
      "If both are present, Transfer-Encoding takes priority."
      BUT not every implementation follows this consistently.
    """), W))
    pause()

    # ── CL explanation ─────────────────────────────────────────────────
    print(sub_line("Content-Length  (CL)"))
    print(fmt_request(
        "POST /upload HTTP/1.1\n"
        "Host: example.com\n"
        "Content-Length: 13\n"
        "\n"
        "Hello, World!",
        label="Simple CL request",
        highlight_lines=[2],
    ))
    print(clr(textwrap.dedent("""
      • Server reads exactly 13 bytes after the blank line.
      • Simple, stateless: one header → one integer → done.
      • Vulnerable when a proxy misuses this to delimit requests.
    """), DIM))
    pause()

    # ── TE explanation ─────────────────────────────────────────────────
    print(sub_line("Transfer-Encoding: chunked  (TE)"))
    print(fmt_request(
        "POST /upload HTTP/1.1\n"
        "Host: example.com\n"
        "Transfer-Encoding: chunked\n"
        "\n"
        "5\n"
        "Hello\n"
        "8\n"
        ", World!\n"
        "0\n",
        label="Chunked TE request",
        highlight_lines=[2],
    ))
    print(clr(textwrap.dedent("""
      • Each chunk begins with its size in hex on its own line.
      • A chunk of size 0 signals end-of-body.
      • Allows streaming; size not known in advance.
      • If a middlebox reassembles chunks and strips the TE header,
        the back-end may receive plain text with a CL header instead,
        making the total length ambiguous.
    """), DIM))
    pause()

    # ── desync diagram ─────────────────────────────────────────────────
    print(sub_line("Desynchronisation Visualised"))
    diagram = f"""
  {clr('CLIENT', G)}                {clr('FRONT-END PROXY', B)}              {clr('BACK-END SERVER', M)}
    │                         │                              │
    │  POST /search           │                              │
    │  Content-Length: 49 ──►─┤  Trusts CL                  │
    │  Transfer-Encoding:     │  Forwards 49 bytes ────────►─┤  Trusts TE
    │    chunked              │  (including smuggled prefix) │  Reads chunks → stops at 0
    │                         │                              │  Leftover in buffer: "GPOST…"
    │                         │                              │
    │                         │                              │  ← next innocent GET arrives
    │  GET /inbox ──────────►─┤  Normal request ───────────►─┤
    │  Cookie: VICTIM_TOKEN   │                              │  Sees: "GPOST…GET /inbox"
    │                         │                              │  {clr('POISONED!', R)}
    │                         │                              │
"""
    print(diagram)
    pause()


def run_mitigation_guide() -> None:
    """Print detailed mitigation strategies."""
    print("\n" + header_line("MITIGATION TECHNIQUES"))
    print(clr(textwrap.dedent("""
      Understanding how to prevent HTTP Request Smuggling is as important
      as understanding how it works.  The following strategies are used
      by modern infrastructure teams.
    """), W))

    mitigations = [
        (
            "1. Normalise requests at the proxy",
            [
                "The front-end proxy should ALWAYS re-encode requests before",
                "forwarding, stripping ambiguous headers.",
                "If both CL and TE are present → reject or use TE, remove CL.",
                "HAProxy, nginx, and modern CDNs support this mode.",
            ],
        ),
        (
            "2. Use HTTP/2 end-to-end",
            [
                "HTTP/2 has a well-defined binary framing layer.",
                "There is no ambiguity between CL and TE in HTTP/2.",
                "H2-to-H1 downgrade at origin can re-introduce smuggling,",
                "so keep HTTP/2 all the way to the back-end if possible.",
            ],
        ),
        (
            "3. Disable keep-alive / pipeline on internal hops",
            [
                "If the proxy opens a fresh TCP connection per request to",
                "the back-end, leftover bytes from one response cannot",
                "poison the next request.",
                "Trade-off: higher latency, more TCP handshakes.",
            ],
        ),
        (
            "4. Strict Content-Length validation",
            [
                "Back-end should reject any request where actual body size",
                "does not match Content-Length exactly.",
                "Return 400 Bad Request and close the connection.",
            ],
        ),
        (
            "5. WAF rules for dual-header requests",
            [
                "Block or flag any request that carries BOTH Content-Length",
                "and Transfer-Encoding simultaneously.",
                "RFC 7230 §3.3.3: servers SHOULD reject such messages.",
            ],
        ),
        (
            "6. Timeouts and connection draining",
            [
                "Configure aggressive read timeouts on the back-end.",
                "Drain and close the connection if unexpected bytes remain",
                "in the buffer after a response is sent.",
            ],
        ),
    ]

    for title, points in mitigations:
        print(fmt_box(title, points, colour=G))
        print()
        time.sleep(0.1)

    pause()


def run_quiz() -> None:
    """Simple knowledge-check quiz."""
    print("\n" + header_line("KNOWLEDGE CHECK"))

    questions = [
        {
            "q": "In a CL.TE attack, which component trusts Content-Length?",
            "options": ["a) Back-end server", "b) Front-end proxy", "c) Both", "d) Neither"],
            "answer": "b",
            "explanation": "In CL.TE, the FRONT-END proxy trusts Content-Length and "
                           "the back-end trusts Transfer-Encoding.",
        },
        {
            "q": "What byte sequence signals the end of a chunked body?",
            "options": ["a) 0xFF", "b) Content-Length: 0", "c) 0\\r\\n\\r\\n", "d) EOF"],
            "answer": "c",
            "explanation": "A terminal chunk is a chunk with size 0 (hex), followed "
                           "by the standard CRLF pair: '0\\r\\n\\r\\n'.",
        },
        {
            "q": "Which HTTP version eliminates smuggling by design?",
            "options": ["a) HTTP/1.0", "b) HTTP/1.1", "c) HTTP/2", "d) HTTP/3"],
            "answer": "c",
            "explanation": "HTTP/2 uses binary framing with explicit stream lengths, "
                           "eliminating the CL vs TE ambiguity entirely.",
        },
        {
            "q": "What is the primary danger of request smuggling to end users?",
            "options": [
                "a) Slower page loads",
                "b) An attacker can hijack/poison their requests",
                "c) Cookies are always deleted",
                "d) TLS is broken",
            ],
            "answer": "b",
            "explanation": "Smuggled bytes in the back-end buffer are prepended to "
                           "the next victim's request, potentially leaking session "
                           "tokens or triggering unintended actions.",
        },
    ]

    score = 0
    for i, q in enumerate(questions, 1):
        print(f"\n  {clr(f'Q{i}:', Y + BLD)} {q['q']}")
        for opt in q["options"]:
            print(f"       {clr(opt, W)}")
        answer = input(f"\n  Your answer (a/b/c/d): ").strip().lower()
        if answer == q["answer"]:
            print(clr("  ✔  Correct!", G))
            score += 1
        else:
            print(clr(f"  ✘  Incorrect. Answer: {q['answer'].upper()}", R))
        print(clr(f"  ℹ  {q['explanation']}", DIM))

    print(f"\n  {clr('Score:', BLD)} {clr(str(score), G)}/{len(questions)}")
    if score == len(questions):
        print(clr("  Perfect score! You understand HTTP Request Smuggling well.\n", G))
    elif score >= len(questions) // 2:
        print(clr("  Good effort — review the scenarios you missed above.\n", Y))
    else:
        print(clr("  Consider re-running the attack simulations to reinforce the concepts.\n", R))
    pause()


# ──────────────────────────────────────────────────────────────────────
# MAIN MENU
# ──────────────────────────────────────────────────────────────────────

MENU_ITEMS = [
    ("1", "Normal HTTP Request Flow",         run_normal_flow),
    ("2", "Core Concept Explainer",           run_concept_explainer),
    ("3", "CL.TE Attack Simulation",          run_clte_attack),
    ("4", "TE.CL Attack Simulation",          run_tecl_attack),
    ("5", "Mitigation Techniques",            run_mitigation_guide),
    ("6", "Knowledge Check (Quiz)",           run_quiz),
    ("0", "Exit",                             None),
]


def print_menu() -> None:
    print("\n" + header_line("MAIN MENU"))
    for key, label, _ in MENU_ITEMS:
        colour = R if key == "0" else (G if key in ("3", "4") else C)
        marker = "⚡" if key in ("3", "4") else " "
        print(f"   {clr(f'[{key}]', colour + BLD)}  {marker} {clr(label, W)}")
    print()


def banner() -> None:
    slow_print(clr(r"""
  ██╗  ██╗████████╗████████╗██████╗     ███████╗███╗   ███╗██╗   ██╗ ██████╗
  ██║  ██║╚══██╔══╝╚══██╔══╝██╔══██╗    ██╔════╝████╗ ████║██║   ██║██╔════╝
  ███████║   ██║      ██║   ██████╔╝    ███████╗██╔████╔██║██║   ██║██║  ███╗
  ██╔══██║   ██║      ██║   ██╔═══╝     ╚════██║██║╚██╔╝██║██║   ██║██║   ██║
  ██║  ██║   ██║      ██║   ██║         ███████║██║ ╚═╝ ██║╚██████╔╝╚██████╔╝
  ╚═╝  ╚═╝   ╚═╝      ╚═╝   ╚═╝         ╚══════╝╚═╝     ╚═╝ ╚═════╝  ╚═════╝
""", C), delay=0.001)
    print(clr("  HTTP Request Smuggling — Educational Simulator  v1.0", BLD + W))
    print(clr("  Pure simulation · No real network traffic · For learning only\n", DIM))
    print(clr("  ⚠  This tool exists solely to teach how HTTP Request Smuggling works.", Y))
    print(clr("     Never test on systems you do not own or have explicit permission for.\n", Y))


def main() -> None:
    banner()
    pause("  Press Enter to enter the simulator…")

    while True:
        print_menu()
        choice = input(clr("  Select option: ", Y + BLD)).strip()

        matched = False
        for key, _, fn in MENU_ITEMS:
            if choice == key:
                matched = True
                if fn is None:
                    print(clr("\n  Goodbye. Stay curious and ethical!\n", G))
                    sys.exit(0)
                try:
                    fn()
                except KeyboardInterrupt:
                    print(clr("\n\n  [interrupted — returning to menu]\n", Y))
                break

        if not matched:
            print(clr("  Invalid option — please choose from the menu.", R))


# ──────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(clr("\n\n  Simulator terminated. Stay safe!\n", Y))
        sys.exit(0)