"""
peer_to_peer_file_sharing_system.py
Simulates a P2P file-sharing network with chunk-based transfers,
multi-peer parallel downloads, peer discovery, and fault tolerance.
"""

from __future__ import annotations
import uuid
import math
import hashlib
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum, auto
from collections import defaultdict


# ══════════════════════════════════════════════════════════════
# Enums
# ══════════════════════════════════════════════════════════════

class PeerStatus(Enum):
    ONLINE  = auto()
    OFFLINE = auto()
    BUSY    = auto()


class TransferStatus(Enum):
    PENDING    = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE   = "COMPLETE"
    FAILED     = "FAILED"
    CANCELLED  = "CANCELLED"


class ChunkStatus(Enum):
    MISSING    = auto()
    REQUESTED  = auto()
    RECEIVED   = auto()
    VERIFIED   = auto()


# ══════════════════════════════════════════════════════════════
# Exceptions
# ══════════════════════════════════════════════════════════════

class P2PError(Exception):
    """Base exception."""

class PeerNotFoundError(P2PError):
    pass

class FileNotFoundError(P2PError):
    pass

class ChunkError(P2PError):
    pass

class TransferError(P2PError):
    pass

class PeerOfflineError(P2PError):
    pass

class InvalidInputError(P2PError):
    pass


# ══════════════════════════════════════════════════════════════
# FileChunk
# ══════════════════════════════════════════════════════════════

class FileChunk:
    """
    Represents a single chunk of a file.
    Carries index, raw data (simulated as bytes), and a checksum.
    """

    def __init__(self, file_id: str, index: int, data: bytes, total_chunks: int):
        if index < 0:
            raise InvalidInputError("Chunk index must be >= 0.")
        if not data:
            raise InvalidInputError("Chunk data cannot be empty.")
        self.chunk_id: str      = f"{file_id}-chunk{index:04d}"
        self.file_id: str       = file_id
        self.index: int         = index
        self.data: bytes        = data
        self.size: int          = len(data)
        self.total_chunks: int  = total_chunks
        self.checksum: str      = self._compute_checksum()
        self.status: ChunkStatus = ChunkStatus.MISSING

    def _compute_checksum(self) -> str:
        return hashlib.md5(self.data).hexdigest()[:10]

    def verify(self) -> bool:
        ok = self._compute_checksum() == self.checksum
        self.status = ChunkStatus.VERIFIED if ok else ChunkStatus.MISSING
        return ok

    def __repr__(self) -> str:
        return (
            f"FileChunk(file={self.file_id}, "
            f"idx={self.index}/{self.total_chunks - 1}, "
            f"size={self.size}B, cksum={self.checksum})"
        )


# ══════════════════════════════════════════════════════════════
# SharedFile  (metadata record kept by each peer)
# ══════════════════════════════════════════════════════════════

@dataclass
class SharedFile:
    file_id:      str
    filename:     str
    size_bytes:   int
    total_chunks: int
    chunk_size:   int
    checksum:     str                          # full-file MD5
    chunks:       dict[int, FileChunk] = field(default_factory=dict)
    owner_id:     str = ""

    @property
    def is_complete(self) -> bool:
        verified = sum(
            1 for c in self.chunks.values()
            if c.status == ChunkStatus.VERIFIED
        )
        return verified == self.total_chunks

    @property
    def completion_pct(self) -> float:
        if self.total_chunks == 0:
            return 0.0
        verified = sum(
            1 for c in self.chunks.values()
            if c.status == ChunkStatus.VERIFIED
        )
        return verified / self.total_chunks * 100

    def missing_indices(self) -> list[int]:
        have = {i for i, c in self.chunks.items() if c.status == ChunkStatus.VERIFIED}
        return [i for i in range(self.total_chunks) if i not in have]

    def __repr__(self) -> str:
        return (
            f"SharedFile({self.filename!r} "
            f"[{self.file_id[:8]}] "
            f"{self.size_bytes}B "
            f"{self.completion_pct:.0f}% complete)"
        )


# ══════════════════════════════════════════════════════════════
# FileManager
# ══════════════════════════════════════════════════════════════

class FileManager:
    """
    Responsible for:
    - Splitting a simulated file into chunks
    - Assembling chunks back into a complete file
    - Managing per-peer file storage
    """

    DEFAULT_CHUNK_SIZE = 256   # bytes (small for demo clarity)

    def __init__(self, peer_id: str):
        self.peer_id = peer_id
        self._storage: dict[str, SharedFile] = {}   # file_id → SharedFile

    # ── public API ──────────────────────────────────────────────

    def add_file(
        self,
        filename: str,
        content: bytes,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> SharedFile:
        """Simulate adding a local file by splitting it into chunks."""
        if not filename.strip():
            raise InvalidInputError("Filename cannot be empty.")
        if not content:
            raise InvalidInputError("File content cannot be empty.")

        file_id     = str(uuid.uuid4())[:10]
        checksum    = hashlib.md5(content).hexdigest()[:12]
        total       = math.ceil(len(content) / chunk_size)

        sf = SharedFile(
            file_id      = file_id,
            filename     = filename,
            size_bytes   = len(content),
            total_chunks = total,
            chunk_size   = chunk_size,
            checksum     = checksum,
            owner_id     = self.peer_id,
        )

        for i in range(total):
            raw   = content[i * chunk_size : (i + 1) * chunk_size]
            chunk = FileChunk(file_id, i, raw, total)
            chunk.status = ChunkStatus.VERIFIED   # locally owned → already verified
            sf.chunks[i] = chunk

        self._storage[file_id] = sf
        return sf

    def create_empty_file(self, metadata: SharedFile) -> SharedFile:
        """Create a placeholder for a file we want to download."""
        sf = SharedFile(
            file_id      = metadata.file_id,
            filename     = metadata.filename,
            size_bytes   = metadata.size_bytes,
            total_chunks = metadata.total_chunks,
            chunk_size   = metadata.chunk_size,
            checksum     = metadata.checksum,
            owner_id     = metadata.owner_id,
        )
        self._storage[metadata.file_id] = sf
        return sf

    def store_chunk(self, chunk: FileChunk) -> bool:
        """Store a received chunk after verification."""
        sf = self._storage.get(chunk.file_id)
        if sf is None:
            raise ChunkError(
                f"No file record for file_id={chunk.file_id}"
            )
        if not chunk.verify():
            raise ChunkError(
                f"Checksum mismatch for chunk {chunk.chunk_id}"
            )
        sf.chunks[chunk.index] = chunk
        return True

    def assemble(self, file_id: str) -> Optional[bytes]:
        """Reconstruct file bytes from verified chunks."""
        sf = self._get_file(file_id)
        if not sf.is_complete:
            missing = sf.missing_indices()
            raise ChunkError(
                f"Cannot assemble {sf.filename!r} – "
                f"{len(missing)} chunk(s) missing: {missing[:5]}…"
            )
        data = b"".join(sf.chunks[i].data for i in range(sf.total_chunks))
        actual = hashlib.md5(data).hexdigest()[:12]
        if actual != sf.checksum:
            raise ChunkError(
                f"File checksum mismatch for {sf.filename!r}"
            )
        return data

    def get_file(self, file_id: str) -> SharedFile:
        return self._get_file(file_id)

    def get_chunk(self, file_id: str, index: int) -> FileChunk:
        sf = self._get_file(file_id)
        chunk = sf.chunks.get(index)
        if chunk is None or chunk.status != ChunkStatus.VERIFIED:
            raise ChunkError(
                f"Chunk {index} of file {file_id} not available."
            )
        return chunk

    def list_files(self) -> list[SharedFile]:
        return list(self._storage.values())

    def has_chunk(self, file_id: str, index: int) -> bool:
        sf = self._storage.get(file_id)
        if sf is None:
            return False
        chunk = sf.chunks.get(index)
        return chunk is not None and chunk.status == ChunkStatus.VERIFIED

    def has_file(self, file_id: str) -> bool:
        return file_id in self._storage

    # ── private ─────────────────────────────────────────────────

    def _get_file(self, file_id: str) -> SharedFile:
        sf = self._storage.get(file_id)
        if sf is None:
            raise FileNotFoundError(
                f"File {file_id!r} not found in local storage."
            )
        return sf


# ══════════════════════════════════════════════════════════════
# TransferRecord
# ══════════════════════════════════════════════════════════════

@dataclass
class TransferRecord:
    transfer_id:  str
    file_id:      str
    filename:     str
    direction:    str          # "upload" | "download"
    peer_id:      str          # remote peer
    total_chunks: int
    chunks_done:  int = 0
    status:       TransferStatus = TransferStatus.PENDING
    started_at:   Optional[datetime] = None
    finished_at:  Optional[datetime] = None
    bytes_transferred: int = 0

    @property
    def progress_pct(self) -> float:
        if self.total_chunks == 0:
            return 0.0
        return self.chunks_done / self.total_chunks * 100

    def start(self) -> None:
        self.status     = TransferStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def finish(self) -> None:
        self.status      = TransferStatus.COMPLETE
        self.finished_at = datetime.now()

    def fail(self) -> None:
        self.status      = TransferStatus.FAILED
        self.finished_at = datetime.now()

    def elapsed(self) -> str:
        if not self.started_at:
            return "–"
        end = self.finished_at or datetime.now()
        return f"{(end - self.started_at).total_seconds():.2f}s"


# ══════════════════════════════════════════════════════════════
# TransferManager
# ══════════════════════════════════════════════════════════════

class TransferManager:
    """
    Handles sending and receiving file chunks between peers.
    Supports parallel multi-peer downloads by splitting chunk
    ranges across available seeders.
    """

    def __init__(self, peer_id: str, file_manager: FileManager):
        self.peer_id      = peer_id
        self._fm          = file_manager
        self._transfers: dict[str, TransferRecord] = {}

    # ── upload side ─────────────────────────────────────────────

    def serve_chunk(
        self, requester_id: str, file_id: str, chunk_index: int
    ) -> FileChunk:
        """Return a chunk to a requesting peer (simulates upload)."""
        try:
            chunk = self._fm.get_chunk(file_id, chunk_index)
        except (FileNotFoundError, ChunkError) as exc:
            raise TransferError(
                f"Peer {self.peer_id} cannot serve chunk "
                f"{chunk_index} of {file_id}: {exc}"
            ) from exc

        rec = self._get_or_create_transfer(
            file_id   = file_id,
            filename  = self._fm.get_file(file_id).filename,
            direction = "upload",
            peer_id   = requester_id,
            total     = self._fm.get_file(file_id).total_chunks,
        )
        rec.chunks_done      += 1
        rec.bytes_transferred += chunk.size
        if rec.status == TransferStatus.PENDING:
            rec.start()
        return chunk

    # ── download side ────────────────────────────────────────────

    def download_from_peers(
        self,
        metadata: SharedFile,
        seeders: list["Peer"],
        simulate_delay: bool = False,
    ) -> bool:
        """
        Download all chunks of a file from one or more seeders.
        Distributes chunk ranges evenly across available seeders.
        Returns True if the file is fully assembled.
        """
        if not seeders:
            raise TransferError("No seeders available for download.")

        # create placeholder if needed
        if not self._fm.has_file(metadata.file_id):
            self._fm.create_empty_file(metadata)

        local_file = self._fm.get_file(metadata.file_id)
        missing    = local_file.missing_indices()

        if not missing:
            print(f"     ℹ  {metadata.filename!r} already complete.")
            return True

        # build per-seeder records
        transfer_records: dict[str, TransferRecord] = {}
        for seeder in seeders:
            rec = self._get_or_create_transfer(
                file_id   = metadata.file_id,
                filename  = metadata.filename,
                direction = "download",
                peer_id   = seeder.peer_id,
                total     = metadata.total_chunks,
            )
            rec.start()
            transfer_records[seeder.peer_id] = rec

        # distribute missing chunks round-robin across seeders
        assignments: dict[str, list[int]] = defaultdict(list)
        for i, chunk_idx in enumerate(missing):
            seeder = seeders[i % len(seeders)]
            assignments[seeder.peer_id].append(chunk_idx)

        print(
            f"     ↓  Downloading {metadata.filename!r} "
            f"({len(missing)} chunks) from "
            f"{len(seeders)} seeder(s): "
            f"{[s.username for s in seeders]}"
        )

        # simulate transfer
        failed_chunks = 0
        for seeder in seeders:
            rec     = transfer_records[seeder.peer_id]
            indices = assignments.get(seeder.peer_id, [])
            for idx in indices:
                if seeder.status == PeerStatus.OFFLINE:
                    print(
                        f"       ⚠  Seeder {seeder.username} "
                        f"went offline mid-transfer – skipping chunk {idx}"
                    )
                    failed_chunks += 1
                    continue
                try:
                    chunk = seeder.transfer_manager.serve_chunk(
                        self.peer_id, metadata.file_id, idx
                    )
                    if simulate_delay:
                        time.sleep(0.01)
                    self._fm.store_chunk(chunk)
                    rec.chunks_done      += 1
                    rec.bytes_transferred += chunk.size
                except (TransferError, ChunkError) as exc:
                    print(f"       ✘  Chunk {idx} failed: {exc}")
                    failed_chunks += 1

        for rec in transfer_records.values():
            if failed_chunks == 0:
                rec.finish()
            else:
                rec.fail()

        local_file = self._fm.get_file(metadata.file_id)
        if local_file.is_complete:
            print(
                f"     ✔  {metadata.filename!r} fully assembled "
                f"({metadata.size_bytes} bytes)."
            )
            return True
        remaining = len(local_file.missing_indices())
        print(
            f"     ⚠  {metadata.filename!r} incomplete – "
            f"{remaining} chunk(s) still missing."
        )
        return False

    # ── history / stats ─────────────────────────────────────────

    def list_transfers(self) -> list[TransferRecord]:
        return list(self._transfers.values())

    def print_summary(self) -> None:
        transfers = self.list_transfers()
        if not transfers:
            print("     (no transfers)")
            return
        for t in transfers:
            icon = {"COMPLETE": "✔", "FAILED": "✘",
                    "IN_PROGRESS": "↻", "PENDING": "…",
                    "CANCELLED": "✖"}
            arrow = "↑" if t.direction == "upload" else "↓"
            print(
                f"     {icon.get(t.status.value,'?')}{arrow} "
                f"{t.filename!r} ↔ {t.peer_id[:8]} "
                f"[{t.status.value}] "
                f"{t.progress_pct:.0f}% "
                f"{t.bytes_transferred}B "
                f"({t.elapsed()})"
            )

    # ── private ─────────────────────────────────────────────────

    def _get_or_create_transfer(
        self,
        file_id: str,
        filename: str,
        direction: str,
        peer_id: str,
        total: int,
    ) -> TransferRecord:
        key = f"{direction}-{file_id}-{peer_id}"
        if key not in self._transfers:
            self._transfers[key] = TransferRecord(
                transfer_id  = str(uuid.uuid4())[:8],
                file_id      = file_id,
                filename     = filename,
                direction    = direction,
                peer_id      = peer_id,
                total_chunks = total,
            )
        return self._transfers[key]


# ══════════════════════════════════════════════════════════════
# NetworkNode  –  peer discovery & connection management
# ══════════════════════════════════════════════════════════════

class NetworkNode:
    """
    Handles the overlay network:
    - Maintaining a list of known peers
    - Peer discovery (flood search)
    - Advertising and querying file availability
    """

    def __init__(self, peer_id: str):
        self.peer_id = peer_id
        self._known_peers: dict[str, "Peer"] = {}   # peer_id → Peer

    # ── connection management ────────────────────────────────────

    def connect_peer(self, peer: "Peer") -> None:
        if peer.peer_id == self.peer_id:
            return
        self._known_peers[peer.peer_id] = peer

    def disconnect_peer(self, peer_id: str) -> None:
        self._known_peers.pop(peer_id, None)

    def known_peers(self) -> list["Peer"]:
        return list(self._known_peers.values())

    def online_peers(self) -> list["Peer"]:
        return [
            p for p in self._known_peers.values()
            if p.status == PeerStatus.ONLINE
        ]

    # ── file discovery ───────────────────────────────────────────

    def search_file(
        self, query: str, visited: Optional[set[str]] = None
    ) -> list[tuple["Peer", SharedFile]]:
        """
        Flood search: ask all known peers; each peer propagates
        the query one hop further (visited set prevents loops).
        Returns list of (seeder_peer, SharedFile) matches.
        """
        if visited is None:
            visited = set()
        visited.add(self.peer_id)

        results: list[tuple["Peer", SharedFile]] = []
        for peer in self.online_peers():
            if peer.peer_id in visited:
                continue
            # direct check
            matches = peer.file_manager.list_files()
            for sf in matches:
                if (
                    query.lower() in sf.filename.lower()
                    and sf.is_complete
                ):
                    results.append((peer, sf))
            # propagate one hop
            deeper = peer.network_node.search_file(query, visited)
            results.extend(deeper)
        return results

    def find_seeders(
        self, file_id: str, visited: Optional[set[str]] = None
    ) -> list["Peer"]:
        """Find all reachable peers that have a complete copy of file_id."""
        if visited is None:
            visited = set()
        visited.add(self.peer_id)

        seeders: list["Peer"] = []
        for peer in self.online_peers():
            if peer.peer_id in visited:
                continue
            visited.add(peer.peer_id)
            sf = peer.file_manager._storage.get(file_id)
            if sf and sf.is_complete:
                seeders.append(peer)
            deeper = peer.network_node.find_seeders(file_id, visited)
            seeders.extend(deeper)
        return seeders


# ══════════════════════════════════════════════════════════════
# Peer  –  the main actor
# ══════════════════════════════════════════════════════════════

class Peer:
    """
    Represents a node in the P2P network.
    Owns a FileManager, TransferManager, and NetworkNode.
    """

    def __init__(self, username: str, ip_address: str):
        if not username.strip():
            raise InvalidInputError("Username cannot be empty.")
        if not ip_address.strip():
            raise InvalidInputError("IP address cannot be empty.")

        self.peer_id:    str        = str(uuid.uuid4())[:10]
        self.username:   str        = username.strip()
        self.ip_address: str        = ip_address.strip()
        self.status:     PeerStatus = PeerStatus.ONLINE

        self.file_manager:    FileManager    = FileManager(self.peer_id)
        self.transfer_manager: TransferManager = TransferManager(
            self.peer_id, self.file_manager
        )
        self.network_node: NetworkNode = NetworkNode(self.peer_id)

    # ── network ──────────────────────────────────────────────────

    def connect_to(self, other: "Peer") -> None:
        """Bidirectional handshake."""
        self.network_node.connect_peer(other)
        other.network_node.connect_peer(self)

    def go_offline(self) -> None:
        self.status = PeerStatus.OFFLINE
        print(f"  💤  {self.username} went OFFLINE.")

    def come_online(self) -> None:
        self.status = PeerStatus.ONLINE
        print(f"  🟢  {self.username} is back ONLINE.")

    # ── file sharing ─────────────────────────────────────────────

    def share_file(self, filename: str, content: bytes) -> SharedFile:
        if self.status != PeerStatus.ONLINE:
            raise PeerOfflineError(f"{self.username} is offline.")
        sf = self.file_manager.add_file(filename, content)
        print(
            f"  📂  {self.username} shared {filename!r} "
            f"({sf.size_bytes}B, {sf.total_chunks} chunks)"
        )
        return sf

    def search(self, query: str) -> list[tuple["Peer", SharedFile]]:
        if self.status != PeerStatus.ONLINE:
            raise PeerOfflineError(f"{self.username} is offline.")
        results = self.network_node.search_file(query)
        print(
            f"  🔍  {self.username} searched {query!r} "
            f"→ {len(results)} result(s)"
        )
        for peer, sf in results:
            print(
                f"       • {sf.filename!r} [{sf.file_id[:8]}] "
                f"{sf.size_bytes}B @ {peer.username}"
            )
        return results

    def download(self, metadata: SharedFile) -> bool:
        if self.status != PeerStatus.ONLINE:
            raise PeerOfflineError(f"{self.username} is offline.")
        seeders = self.network_node.find_seeders(metadata.file_id)
        if not seeders:
            print(
                f"  ✘  {self.username}: No seeders found "
                f"for {metadata.filename!r}."
            )
            return False
        return self.transfer_manager.download_from_peers(metadata, seeders)

    # ── display ──────────────────────────────────────────────────

    def print_status(self) -> None:
        files   = self.file_manager.list_files()
        peers   = self.network_node.known_peers()
        print(
            f"\n  Peer: {self.username} [{self.peer_id[:8]}] "
            f"{self.ip_address}  [{self.status.name}]"
        )
        print(f"    Known peers ({len(peers)}): "
              f"{[p.username for p in peers]}")
        print(f"    Files ({len(files)}):")
        for sf in files:
            bar = self._progress_bar(sf.completion_pct)
            print(
                f"      {bar} {sf.filename!r} "
                f"{sf.size_bytes}B "
                f"({sf.total_chunks} chunks) "
                f"[{sf.completion_pct:.0f}%]"
            )
        print(f"    Transfers:")
        self.transfer_manager.print_summary()

    @staticmethod
    def _progress_bar(pct: float, width: int = 10) -> str:
        filled = int(pct / 100 * width)
        return "[" + "█" * filled + "░" * (width - filled) + "]"

    def __repr__(self) -> str:
        return (
            f"Peer({self.username!r} [{self.peer_id[:8]}] "
            f"{self.ip_address} {self.status.name})"
        )


# ══════════════════════════════════════════════════════════════
# P2PNetwork  –  top-level coordinator / registry
# ══════════════════════════════════════════════════════════════

class P2PNetwork:
    """
    Optional high-level registry for bootstrapping.
    In a real P2P system this role is filled by a DHT or tracker;
    here it just wires up peers and provides a network overview.
    """

    def __init__(self, name: str = "P2PNet"):
        self.name = name
        self._peers: dict[str, Peer] = {}   # peer_id → Peer

    def add_peer(self, peer: Peer) -> None:
        self._peers[peer.peer_id] = peer
        # bootstrap: connect to all existing peers
        for existing in self._peers.values():
            if existing.peer_id != peer.peer_id:
                peer.connect_to(existing)
        print(f"  ✚  {peer.username} joined {self.name}.")

    def remove_peer(self, peer_id: str) -> None:
        self._peers.pop(peer_id, None)

    def get_peer(self, username: str) -> Optional[Peer]:
        return next(
            (p for p in self._peers.values() if p.username == username),
            None,
        )

    def print_overview(self) -> None:
        print(f"\n{'═'*62}")
        print(f"  Network: {self.name}  ({len(self._peers)} peer(s))")
        print(f"{'═'*62}")
        for peer in self._peers.values():
            peer.print_status()
        print(f"{'═'*62}\n")


# ══════════════════════════════════════════════════════════════
# Simulation helpers
# ══════════════════════════════════════════════════════════════

def _sep(title: str = "") -> None:
    w = 62
    if title:
        pad = w - len(title) - 6
        print(f"\n{'─'*4}  {title}  {'─'*pad}")
    else:
        print(f"\n{'─'*w}")


def _make_content(label: str, size: int = 800) -> bytes:
    """Generate deterministic pseudo-random bytes for a simulated file."""
    seed = label.encode()
    data = bytearray()
    val  = int.from_bytes(hashlib.md5(seed).digest(), "big")
    while len(data) < size:
        val  = (val * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        data += val.to_bytes(8, "big")
    return bytes(data[:size])


# ══════════════════════════════════════════════════════════════
# Main simulation
# ══════════════════════════════════════════════════════════════

def run_simulation() -> None:
    print("=" * 62)
    print("  PEER-TO-PEER FILE SHARING SYSTEM  –  Simulation")
    print("=" * 62)

    network = P2PNetwork("DemoNet")

    # ── 1. Create & join peers ───────────────────────────────────
    _sep("Step 1 · Peers join the network")
    alice  = Peer("Alice",  "192.168.1.10")
    bob    = Peer("Bob",    "192.168.1.20")
    carol  = Peer("Carol",  "192.168.1.30")
    dave   = Peer("Dave",   "192.168.1.40")
    eve    = Peer("Eve",    "192.168.1.50")

    for p in [alice, bob, carol, dave, eve]:
        network.add_peer(p)

    # ── 2. Peers share files ─────────────────────────────────────
    _sep("Step 2 · Peers share local files")
    sf_movie   = alice.share_file("holiday_movie.mp4",  _make_content("movie",   1200))
    sf_song    = alice.share_file("favourite_song.mp3", _make_content("song",     512))
    sf_pdf     = bob.share_file("research_paper.pdf",   _make_content("pdf",      900))
    sf_img     = carol.share_file("vacation_photo.jpg", _make_content("photo",    400))
    sf_archive = dave.share_file("project_code.zip",    _make_content("zipcode", 1500))

    # ── 3. Search for files ──────────────────────────────────────
    _sep("Step 3 · Peers search for files")
    results_movie  = eve.search("movie")
    results_paper  = bob.search("research")      # Bob searches for his own file (edge case)
    results_photo  = alice.search("photo")
    results_code   = carol.search("code")

    # ── 4. Simple single-seeder download ────────────────────────
    _sep("Step 4 · Simple downloads")

    # Eve downloads the movie from Alice
    print(f"\n  Eve ← Alice: holiday_movie.mp4")
    eve.download(sf_movie)

    # Carol downloads the research paper from Bob
    print(f"\n  Carol ← Bob: research_paper.pdf")
    carol.download(sf_pdf)

    # ── 5. Multi-peer parallel download ─────────────────────────
    _sep("Step 5 · Multi-peer parallel download")

    # Make the archive available on two peers so Dave & Alice
    # can seed it simultaneously to Eve.
    sf_archive_alice = alice.share_file("project_code.zip", _make_content("zipcode", 1500))

    # Use the same file_id so both map to the same logical file.
    # We clone metadata from Dave's copy and re-register under
    # the same ID on Alice manually (simulating a prior download).
    alice.file_manager._storage[sf_archive.file_id] = \
        alice.file_manager._storage.pop(sf_archive_alice.file_id)
    alice.file_manager._storage[sf_archive.file_id].file_id = sf_archive.file_id
    for chunk in alice.file_manager._storage[sf_archive.file_id].chunks.values():
        chunk.file_id = sf_archive.file_id

    print(
        "\n  Eve downloads project_code.zip from "
        "BOTH Dave AND Alice in parallel:"
    )
    eve.download(sf_archive)

    # ── 6. Fault tolerance: seeder goes offline mid-network ──────
    _sep("Step 6 · Fault tolerance – seeder goes offline")

    sf_song2 = bob.share_file("favourite_song.mp3", _make_content("song", 512))
    # Ensure same file_id as Alice's copy for multi-seeder test
    bob.file_manager._storage[sf_song.file_id] = \
        bob.file_manager._storage.pop(sf_song2.file_id)
    bob.file_manager._storage[sf_song.file_id].file_id = sf_song.file_id
    for chunk in bob.file_manager._storage[sf_song.file_id].chunks.values():
        chunk.file_id = sf_song.file_id

    print("\n  Dave wants to download favourite_song.mp3 "
          "(Alice + Bob both seed).")
    print("  Simulating Bob going offline mid-transfer…")
    bob.go_offline()

    # Dave finds seeders – only Alice should respond (Bob offline)
    dave.download(sf_song)

    bob.come_online()

    # ── 7. Peer disconnects then reconnects ──────────────────────
    _sep("Step 7 · Peer disconnect / reconnect")
    carol.go_offline()
    try:
        carol.download(sf_movie)
    except PeerOfflineError as exc:
        print(f"  ✘  Expected error: {exc}")
    carol.come_online()
    print("  Carol reconnected – resuming download:")
    carol.download(sf_movie)

    # ── 8. File not found ────────────────────────────────────────
    _sep("Step 8 · Search for non-existent file")
    missing = dave.search("nonexistent_file_xyz.bin")
    if not missing:
        print("  ℹ  No results – file not available on the network.")

    # ── 9. Full network overview ─────────────────────────────────
    _sep("Step 9 · Full network overview")
    network.print_overview()

    _sep()
    print("  Simulation complete.")
    print("=" * 62)


# ══════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    run_simulation()