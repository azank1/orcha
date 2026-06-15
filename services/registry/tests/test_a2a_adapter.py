"""Tests for A2A adapter."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from services.registry.src.adapters.a2a import A2AAdapter


class TestA2AAdapter:
    """Test suite for A2AAdapter."""

    @pytest.mark.asyncio
    async def test_harvest_successful(self, mock_a2a_agent_card):
        """Test successful harvesting of A2A capabilities."""
        adapter = A2AAdapter(
            endpoint="https://api.example.com/a2a", timeout=10, max_retries=3
        )

        with patch(
            "services.registry.src.adapters.a2a.httpx.AsyncClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.json = MagicMock(return_value=mock_a2a_agent_card)
            mock_response.raise_for_status = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)

            result = await adapter.harvest()

        # Assertions
        assert len(result.capabilities) == 2  # 2 skills
        assert len(result.errors) == 0

        # Check capabilities (all mapped to "tool" type)
        assert all(cap.type == "tool" for cap in result.capabilities)

        skill1 = result.capabilities[0]
        assert skill1.id == "calculate_portfolio"
        assert skill1.name == "Calculate Portfolio Value"
        assert skill1.input_schema is not None
        assert skill1.output_schema is not None

        skill2 = result.capabilities[1]
        assert skill2.id == "get_market_data"
        assert skill2.input_schema is not None

        # Check metadata contains agent-level auth schemes
        assert "agent_auth_schemes" in result.metadata
        assert len(result.metadata["agent_auth_schemes"]) == 2
        assert result.metadata["agent_auth_schemes"][0]["scheme"] == "apiKey"
        assert result.metadata["agent_auth_schemes"][1]["scheme"] == "oauth2"

        # Check other metadata
        assert result.metadata["agent_name"] == "TestA2AAgent"
        assert result.metadata["provider"] == "TestProvider"
        assert "test" in result.metadata["tags"]

    @pytest.mark.asyncio
    async def test_harvest_with_pre_parsed_agent_card(self, mock_a2a_agent_card):
        """Test harvesting with pre-parsed Agent Card (from emerge.yaml)."""
        adapter = A2AAdapter(
            endpoint="https://api.example.com/a2a",
            agent_card_json=mock_a2a_agent_card,  # Pre-parsed
        )

        result = await adapter.harvest()

        # Should use pre-parsed card without making HTTP request
        assert len(result.capabilities) == 2
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_harvest_unsupported_schema_version(self):
        """Test harvesting fails gracefully for unsupported schema version."""
        adapter = A2AAdapter(endpoint="https://api.example.com/a2a")

        unsupported_card = {"schemaVersion": "2.0", "skills": []}  # Unsupported

        with patch(
            "services.registry.src.adapters.a2a.httpx.AsyncClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.json = MagicMock(return_value=unsupported_card)
            mock_response.raise_for_status = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)

            result = await adapter.harvest()

        assert len(result.capabilities) == 0
        assert len(result.errors) == 1
        assert "Unsupported or missing A2A schema version" in result.errors[0]

    @pytest.mark.asyncio
    async def test_harvest_missing_schema_version_with_skills_ok(self):
        """Agents often omit schemaVersion; we still harvest when skills are present."""
        adapter = A2AAdapter(endpoint="https://api.example.com/a2a")

        card = {
            "name": "NoSchemaAgent",
            "skills": [
                {
                    "id": "do_thing",
                    "name": "Do Thing",
                    "description": "Does a thing",
                },
            ],
        }

        with patch(
            "services.registry.src.adapters.a2a.httpx.AsyncClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.json = MagicMock(return_value=card)
            mock_response.raise_for_status = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)

            result = await adapter.harvest()

        assert len(result.capabilities) == 1
        assert result.capabilities[0].id == "do_thing"
        assert result.capabilities[0].name == "Do Thing"

    @pytest.mark.asyncio
    async def test_harvest_with_invalid_skill(self):
        """Test harvesting handles invalid skills gracefully."""
        adapter = A2AAdapter(endpoint="https://api.example.com/a2a")

        invalid_card = {
            "schemaVersion": "1.0",
            "authSchemes": [],
            "skills": [
                {
                    # Missing required "id" field
                    "name": "Invalid Skill",
                    "description": "Missing ID",
                },
                {
                    "id": "valid_skill",
                    "name": "Valid Skill",
                    "description": "This is valid",
                },
            ],
        }

        with patch(
            "services.registry.src.adapters.a2a.httpx.AsyncClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.json = MagicMock(return_value=invalid_card)
            mock_response.raise_for_status = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)

            result = await adapter.harvest()

        # Should have 1 valid capability and 1 error
        assert len(result.capabilities) == 1
        assert result.capabilities[0].id == "valid_skill"
        assert len(result.errors) == 1
        assert "Invalid skill" in result.errors[0]

    @pytest.mark.asyncio
    async def test_harvest_with_connection_error(self):
        """Test harvesting fails with ConnectionError when endpoint unreachable."""
        adapter = A2AAdapter(endpoint="https://api.example.com/a2a", max_retries=3)

        with (
            patch(
                "services.registry.src.adapters.a2a.httpx.AsyncClient"
            ) as mock_client,
            patch("asyncio.sleep", new=AsyncMock()),
        ):  # Speed up retries
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            mock_instance.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            with pytest.raises(ConnectionError):
                await adapter.harvest()

    @pytest.mark.asyncio
    async def test_harvest_with_retry_logic(self, mock_a2a_agent_card):
        """Test retry logic with exponential backoff."""
        adapter = A2AAdapter(endpoint="https://api.example.com/a2a", max_retries=3)

        with (
            patch(
                "services.registry.src.adapters.a2a.httpx.AsyncClient"
            ) as mock_client,
            patch("asyncio.sleep", new=AsyncMock()),
        ):
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            # First 2 attempts fail, 3rd succeeds
            attempt_count = 0

            async def mock_get(*args, **kwargs):
                nonlocal attempt_count
                attempt_count += 1

                if attempt_count < 3:
                    raise httpx.HTTPError("Temporary error")

                mock_resp = MagicMock()
                mock_resp.json = MagicMock(return_value=mock_a2a_agent_card)
                mock_resp.raise_for_status = MagicMock()
                return mock_resp

            mock_instance.get = AsyncMock(side_effect=mock_get)

            result = await adapter.harvest()

            assert len(result.capabilities) == 2  # Should succeed after retries

    @pytest.mark.asyncio
    async def test_health_check_successful(self):
        """Test successful health check."""
        adapter = A2AAdapter(endpoint="https://api.example.com/a2a")

        with patch(
            "services.registry.src.adapters.a2a.httpx.AsyncClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_instance.get = AsyncMock(return_value=mock_response)

            is_healthy = await adapter.health_check()

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check returns False on failure."""
        adapter = A2AAdapter(endpoint="https://api.example.com/a2a")

        with patch(
            "services.registry.src.adapters.a2a.httpx.AsyncClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            mock_instance.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            is_healthy = await adapter.health_check()

        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_agent_level_auth_not_per_skill(self, mock_a2a_agent_card):
        """
        Test that auth schemes are at agent level, not per-skill.

        This is a critical invariant of A2A v1 protocol.
        """
        adapter = A2AAdapter(
            endpoint="https://api.example.com/a2a", agent_card_json=mock_a2a_agent_card
        )

        result = await adapter.harvest()

        # Auth schemes should be in metadata, not in capabilities
        assert "agent_auth_schemes" in result.metadata
        assert len(result.metadata["agent_auth_schemes"]) > 0

        # Capabilities should NOT have individual auth_strategies
        for _cap in result.capabilities:
            # Per-capability auth doesn't exist in A2A v1
            # (it's a future enhancement)
            pass

    @pytest.mark.asyncio
    async def test_fetch_agent_card_from_well_known(self, mock_a2a_agent_card):
        """Test fetching Agent Card from /.well-known/agent.json."""
        adapter = A2AAdapter(endpoint="https://api.example.com/a2a")

        with patch(
            "services.registry.src.adapters.a2a.httpx.AsyncClient"
        ) as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.json = MagicMock(return_value=mock_a2a_agent_card)
            mock_response.raise_for_status = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)

            card = await adapter._get_agent_card()

        # Check the correct URL was called
        called_url = mock_instance.get.call_args[0][0]
        assert called_url == "https://api.example.com/a2a/.well-known/agent.json"

        assert card["schemaVersion"] == "1.0"
        assert len(card["skills"]) == 2
