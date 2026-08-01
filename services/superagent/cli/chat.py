"""SuperAgent CLI chat client.

Usage:
    uv run python cli/chat.py --port 8002 --user dev-user-001

Supports SSE streaming, interrupt handling (auth / approval / clarify),
and automatic resume after HITL.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import uuid

import httpx


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SuperAgent CLI")
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=8002)
    p.add_argument("--user", default="dev_user")
    p.add_argument("--session", default=None, help="Resume an existing session ID")
    return p.parse_args()


async def _stream_sse(
    client: httpx.AsyncClient,
    url: str,
    payload: dict,
) -> str | None:
    """
    POST to url with payload, consume SSE stream.

    Returns the interrupt_id if an interrupt event is received, else None.
    """
    interrupt_info: dict | None = None

    async with client.stream("POST", url, json=payload) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line.startswith("data:"):
                continue
            raw = line[5:].strip()
            if not raw:
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue

            event_type = event.get("type", "")

            if event_type == "token":
                content = event.get("content", "")
                print(content, end="", flush=True)

            elif event_type == "progress":
                content = event.get("content", "")
                print(f"\n[…] {content}", flush=True)

            elif event_type == "invocation_start":
                tn = event.get("tool_name", "")
                aid = event.get("agent_id", "")
                print(f"\n[invoke] {tn} · {aid}", flush=True)

            elif event_type == "invocation_progress":
                st = event.get("status", "")
                msg = event.get("message", "")
                print(f"\n[… {st}] {msg}", flush=True)

            elif event_type == "invocation_result":
                st = event.get("status", "")
                print(f"\n[invoke done] {st}", flush=True)

            elif event_type == "interrupt":
                interrupt_info = event
                print(
                    f"\n\n[INTERRUPT — {event.get('interrupt_type', 'unknown')}]",
                    flush=True,
                )
                print(f"  {event.get('message', '')}", flush=True)

            elif event_type == "done":
                print()  # newline after final token

    return interrupt_info


async def main() -> None:
    args = _parse_args()
    base_url = f"http://{args.host}:{args.port}"

    async with httpx.AsyncClient(
        base_url=base_url, timeout=httpx.Timeout(120.0)
    ) as client:
        # Create or reuse session
        session_id: str
        if args.session:
            session_id = args.session
            print(f"Resuming session: {session_id}")
        else:
            resp = await client.post("/sessions", json={"user_id": args.user})
            resp.raise_for_status()
            session_id = resp.json()["session_id"]
            print(f"Session: {session_id}")

        print(f"User: {args.user}")
        print("Type your message. Ctrl+C or 'exit' to quit.\n")

        while True:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("You: ")
                )
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye.")
                break

            if user_input.strip().lower() in ("exit", "quit", "bye"):
                print("Goodbye.")
                break

            if not user_input.strip():
                continue

            # Handle __RESUME__ token from previous interrupt
            if user_input.startswith("__RESUME__"):
                parts = user_input.split("__")
                if len(parts) >= 4:
                    _, _, interrupt_id, resume_value = (
                        parts[0],
                        parts[1],
                        parts[2],
                        "__".join(parts[3:]),
                    )
                    interrupt_info = await _stream_sse(
                        client,
                        f"/sessions/{session_id}/resume",
                        {
                            "user_id": args.user,
                            "interrupt_id": interrupt_id,
                            "resume_value": resume_value,
                        },
                    )
                    await _handle_interrupt(
                        client, session_id, args.user, interrupt_info
                    )
                    continue

            print("Agent: ", end="", flush=True)
            interrupt_info = await _stream_sse(
                client,
                f"/sessions/{session_id}/message",
                {"user_id": args.user, "message": user_input},
            )

            await _handle_interrupt(client, session_id, args.user, interrupt_info)


async def _handle_interrupt(
    client: httpx.AsyncClient,
    session_id: str,
    user_id: str,
    interrupt_info: dict | None,
) -> None:
    if interrupt_info is None:
        return

    interrupt_id = interrupt_info.get("interrupt_id", str(uuid.uuid4()))
    interrupt_type = interrupt_info.get("interrupt_type", "unknown")

    if interrupt_type == "auth":
        print(
            "\n[AUTH REQUIRED] Agent needs authentication. "
            "Please complete auth in your browser, then press Enter."
        )
        await asyncio.get_event_loop().run_in_executor(
            None, input, "Press Enter when done: "
        )
        resume_value = "auth_completed"
    elif interrupt_type == "approval":
        message = interrupt_info.get("message", "Approve this action?")
        answer = await asyncio.get_event_loop().run_in_executor(
            None, lambda: input(f"\n[APPROVAL] {message} (yes/no): ")
        )
        resume_value = (
            "approved" if answer.strip().lower() in ("y", "yes") else "rejected"
        )
    elif interrupt_type == "clarify":
        question = interrupt_info.get("message", "The agent needs more information:")
        resume_value = await asyncio.get_event_loop().run_in_executor(
            None, lambda: input(f"\n[CLARIFY] {question}\nYour answer: ")
        )
    else:
        resume_value = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: input(
                f"\n[INPUT REQUIRED] {interrupt_info.get('message', '')}\n> "
            ),
        )

    print("Agent: ", end="", flush=True)
    next_interrupt = await _stream_sse(
        client,
        f"/sessions/{session_id}/resume",
        {
            "user_id": user_id,
            "interrupt_id": interrupt_id,
            "resume_value": resume_value,
        },
    )
    # Recurse if another interrupt fires
    if next_interrupt:
        await _handle_interrupt(client, session_id, user_id, next_interrupt)


if __name__ == "__main__":
    asyncio.run(main())
