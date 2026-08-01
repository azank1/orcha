"""TCP gossip hub — D0 spike transport (libp2p GossipSub replaces in production)."""

from __future__ import annotations

import asyncio
import json
import struct
from collections.abc import AsyncIterator

from .envelope import SignedManifestEnvelope


def _frame(message: bytes) -> bytes:
    return struct.pack("!I", len(message)) + message


async def _read_frame(reader: asyncio.StreamReader) -> bytes:
    header = await reader.readexactly(4)
    (length,) = struct.unpack("!I", header)
    return await reader.readexactly(length)


class GossipHub:
    """Simple fan-out broker: publishers connect, subscribers receive broadcasts."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9100) -> None:
        self.host = host
        self.port = port
        self._server: asyncio.Server | None = None
        self._clients: set[asyncio.StreamWriter] = set()
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        async with self._lock:
            for writer in list(self._clients):
                writer.close()
            self._clients.clear()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        async with self._lock:
            self._clients.add(writer)
        try:
            # Subscribers connect and wait for pushed envelopes (they send nothing).
            # Publishers send one framed publish message immediately after connect.
            try:
                raw = await asyncio.wait_for(_read_frame(reader), timeout=0.2)
            except asyncio.TimeoutError:
                await asyncio.Event().wait()
                return
            msg = json.loads(raw.decode())
            if msg.get("type") == "publish":
                envelope = SignedManifestEnvelope.from_dict(msg["envelope"])
                await self._broadcast(envelope, exclude=writer)
        except (asyncio.IncompleteReadError, ConnectionResetError, json.JSONDecodeError):
            pass
        finally:
            async with self._lock:
                self._clients.discard(writer)
            writer.close()
            await writer.wait_closed()

    async def _broadcast(
        self,
        envelope: SignedManifestEnvelope,
        *,
        exclude: asyncio.StreamWriter | None = None,
    ) -> None:
        payload = _frame(
            json.dumps(
                {"type": "envelope", "envelope": envelope.to_dict()}
            ).encode()
        )
        async with self._lock:
            dead: list[asyncio.StreamWriter] = []
            for writer in self._clients:
                if writer is exclude:
                    continue
                try:
                    writer.write(payload)
                    await writer.drain()
                except ConnectionError:
                    dead.append(writer)
            for writer in dead:
                self._clients.discard(writer)


async def publish_envelope(
    hub_host: str, hub_port: int, envelope: SignedManifestEnvelope
) -> None:
    reader, writer = await asyncio.open_connection(hub_host, hub_port)
    try:
        msg = json.dumps(
            {"type": "publish", "envelope": envelope.to_dict()}
        ).encode()
        writer.write(_frame(msg))
        await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


async def subscribe_once(
    hub_host: str, hub_port: int, timeout: float = 5.0
) -> SignedManifestEnvelope:
    reader, writer = await asyncio.open_connection(hub_host, hub_port)
    try:
        raw = await asyncio.wait_for(_read_frame(reader), timeout=timeout)
        msg = json.loads(raw.decode())
        if msg.get("type") != "envelope":
            raise RuntimeError(f"unexpected gossip message: {msg.get('type')}")
        return SignedManifestEnvelope.from_dict(msg["envelope"])
    finally:
        writer.close()
        await writer.wait_closed()


async def iter_envelopes(
    hub_host: str, hub_port: int
) -> AsyncIterator[SignedManifestEnvelope]:
    reader, writer = await asyncio.open_connection(hub_host, hub_port)
    try:
        while True:
            raw = await _read_frame(reader)
            msg = json.loads(raw.decode())
            if msg.get("type") == "envelope":
                yield SignedManifestEnvelope.from_dict(msg["envelope"])
    finally:
        writer.close()
        await writer.wait_closed()
