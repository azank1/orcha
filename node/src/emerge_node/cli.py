"""emerge-node CLI — D0 spike."""

from __future__ import annotations

import argparse
import asyncio
import sys

from .gossip import GossipHub


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="emerge-node",
        description="Experimental gossip sidecar (TCP spike)",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9100)
    args = parser.parse_args(argv)

    async def run() -> None:
        hub = GossipHub(host=args.host, port=args.port)
        await hub.start()
        print(f"emerge-node listening on {args.host}:{args.port}", flush=True)
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            pass
        finally:
            await hub.stop()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
