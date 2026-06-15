"""X402 payment header parser utility."""

from typing import Any


def parse_x402_header(header_value: str) -> dict[str, Any]:
    """
    Parse X-Microtransaction header for x402 payment metadata.

    Format: "price=10;asset=USDC;recipient=0x...;chain=eip155:8453"

    Args:
        header_value: The X-Microtransaction header value

    Returns:
        Dictionary with parsed payment metadata
    """
    result = {
        "price": None,
        "asset": None,
        "recipient": None,
        "chain_id": None,
        "token_address": None,
    }

    if not header_value:
        return result

    try:
        # Split by semicolon
        parts = header_value.split(";")

        for part in parts:
            part = part.strip()
            if "=" not in part:
                continue

            key, value = part.split("=", 1)
            key = key.strip().lower()
            value = value.strip()

            if key == "price":
                result["price"] = value
            elif key == "asset":
                result["asset"] = value
            elif key == "recipient":
                result["recipient"] = value
            elif key == "chain":
                result["chain_id"] = value
            elif key == "token" or key == "token_address":
                result["token_address"] = value

    except Exception:  # noqa: S110
        # Return partial results if parsing fails
        pass

    return result


def build_x402_header(
    price: str | None = None,
    asset: str | None = None,
    recipient: str | None = None,
    chain_id: str | None = None,
    token_address: str | None = None,
) -> str:
    """
    Build X-Microtransaction header from payment metadata.

    Args:
        price: Price amount
        asset: Asset symbol (e.g., "USDC")
        recipient: Recipient address
        chain_id: Chain ID (e.g., "eip155:8453")
        token_address: Token contract address

    Returns:
        Formatted header string
    """
    parts = []

    if price:
        parts.append(f"price={price}")
    if asset:
        parts.append(f"asset={asset}")
    if recipient:
        parts.append(f"recipient={recipient}")
    if chain_id:
        parts.append(f"chain={chain_id}")
    if token_address:
        parts.append(f"token={token_address}")

    return ";".join(parts)
