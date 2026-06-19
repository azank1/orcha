"""gRPC servicer implementation for Registry service."""

from typing import Any

import grpc
from common.database.src.generated_client import Prisma
from google.protobuf.struct_pb2 import Struct
from google.protobuf.timestamp_pb2 import Timestamp

from common.proto.src import registry_pb2, registry_pb2_grpc


class RegistryServicer(registry_pb2_grpc.RegistryServiceServicer):
    """Implementation of RegistryService gRPC service."""

    def __init__(self, db: Prisma):
        """
        Initialize servicer.

        Args:
            db: Prisma database client
        """
        self.db = db

    async def UpdateAgentHealth(
        self,
        request: registry_pb2.UpdateHealthRequest,
        context: grpc.aio.ServicerContext,
    ) -> registry_pb2.UpdateHealthResponse:
        """
        Update agent health status (called by health monitoring cron job).

        Args:
            request: UpdateHealthRequest with agent_id and status
            context: gRPC context

        Returns:
            UpdateHealthResponse
        """
        try:
            # Map proto enum to Prisma enum
            status_map = {
                registry_pb2.HEALTH_STATUS_HEALTHY: "HEALTHY",
                registry_pb2.HEALTH_STATUS_UNHEALTHY: "UNHEALTHY",
                registry_pb2.HEALTH_STATUS_UNKNOWN: "UNKNOWN",
            }

            db_status = status_map.get(request.status, "UNKNOWN")

            # Update agent
            await self.db.agent.update(
                where={"id": request.agent_id},
                data={
                    "health_status": db_status,
                    "last_health_check": request.checked_at.ToDatetime(),
                    "health_failures": {
                        "increment": (
                            1
                            if request.status == registry_pb2.HEALTH_STATUS_UNHEALTHY
                            else 0
                        )
                    },
                },
            )

            return registry_pb2.UpdateHealthResponse(
                success=True, message="Health updated successfully"
            )

        except Exception as e:
            return registry_pb2.UpdateHealthResponse(
                success=False, message=f"Error: {str(e)}"
            )

    async def GetAgentManifest(
        self,
        request: registry_pb2.GetManifestRequest,
        context: grpc.aio.ServicerContext,
    ) -> registry_pb2.UniversalManifest:
        """
        Retrieve full agent manifest.

        Args:
            request: GetManifestRequest with agent_id
            context: gRPC context

        Returns:
            UniversalManifest
        """
        try:
            agent = await self.db.agent.find_unique(
                where={"id": request.agent_id},
                include={
                    "transport": True,
                    "security": {"include": {"auth_strategies": True}},
                    "payment": True,
                    "capabilities": {"include": {"auth_strategies": True}},
                },
            )

            if not agent:
                await context.abort(grpc.StatusCode.NOT_FOUND, "Agent not found")

            return self._agent_to_proto(agent)

        except Exception as e:
            await context.abort(grpc.StatusCode.INTERNAL, f"Error: {str(e)}")

    async def GetMultipleManifests(
        self,
        request: registry_pb2.GetMultipleManifestsRequest,
        context: grpc.aio.ServicerContext,
    ) -> registry_pb2.GetMultipleManifestsResponse:
        """
        Retrieve multiple agent manifests (batch endpoint).

        Args:
            request: GetMultipleManifestsRequest with agent_ids
            context: gRPC context

        Returns:
            GetMultipleManifestsResponse
        """
        try:
            manifests = []

            for agent_id in request.agent_ids:
                agent = await self.db.agent.find_unique(
                    where={"id": agent_id},
                    include={
                        "transport": True,
                        "security": {"include": {"auth_strategies": True}},
                        "payment": True,
                        "capabilities": {"include": {"auth_strategies": True}},
                    },
                )

                if agent:
                    manifests.append(self._agent_to_proto(agent))

            return registry_pb2.GetMultipleManifestsResponse(manifests=manifests)

        except Exception as e:
            await context.abort(grpc.StatusCode.INTERNAL, f"Error: {str(e)}")

    def _agent_to_proto(self, agent: Any) -> registry_pb2.UniversalManifest:
        """
        Convert Prisma agent model to protobuf message.

        Args:
            agent: Prisma agent object with relations

        Returns:
            UniversalManifest protobuf message
        """
        # Build identity info
        identity = registry_pb2.IdentityInfo(
            id=agent.id,
            name=agent.name,
            version=agent.version,
            provider=agent.provider,
            owner_contact=agent.owner_contact,
            description=agent.description,
            tags=agent.tags or [],
        )

        # Build metadata info
        indexed_timestamp = Timestamp()
        indexed_timestamp.FromDatetime(agent.indexed_at)

        health_status_map = {
            "HEALTHY": registry_pb2.HEALTH_STATUS_HEALTHY,
            "UNHEALTHY": registry_pb2.HEALTH_STATUS_UNHEALTHY,
            "UNKNOWN": registry_pb2.HEALTH_STATUS_UNKNOWN,
        }

        metadata = registry_pb2.MetadataInfo(
            indexed_at=indexed_timestamp,
            health_status=health_status_map.get(
                agent.health_status, registry_pb2.HEALTH_STATUS_UNKNOWN
            ),
            health_endpoint=agent.health_endpoint,
        )

        # Build transport info
        transport_info = registry_pb2.TransportInfo(
            type=agent.transport.type.lower() if agent.transport else "",
            endpoint=agent.transport.endpoint or "" if agent.transport else "",
            command=agent.transport.command or "" if agent.transport else "",
            args=agent.transport.args or [] if agent.transport else [],
        )

        # Build protocol info
        protocol = registry_pb2.ProtocolInfo(
            type=agent.protocol_type.lower(),
            version=agent.protocol_version,
            transport=transport_info,
        )

        # Build security info
        tls_config = None
        if agent.security and agent.security.transport_layer_type == "MTLS":
            tls_config = registry_pb2.MTLSConfig(
                cert_vault_key=agent.security.mtls_cert_vault_key or "",
                key_vault_key=agent.security.mtls_key_vault_key or "",
                ca_vault_key=agent.security.mtls_ca_vault_key or "",
            )

        transport_layer = registry_pb2.TransportLayerSecurity(
            type=(
                agent.security.transport_layer_type.lower()
                if agent.security
                else "none"
            ),
            mtls_config=tls_config,
        )

        auth_strategies = []
        if agent.security:
            for auth in agent.security.auth_strategies:
                config_struct = Struct()
                config_struct.update(auth.config)
                auth_strategies.append(
                    registry_pb2.AuthStrategy(
                        id=auth.strategy_id,
                        type=auth.type.lower(),
                        config=config_struct,
                    )
                )

        security = registry_pb2.SecurityInfo(
            transport_layer=transport_layer, auth_strategies=auth_strategies
        )

        # Build payment info
        payment_config = None
        if agent.payment:
            payment_config = registry_pb2.PaymentConfig(
                enabled=agent.payment.enabled,
                chain_id=agent.payment.chain_id or "",
                recipient_address=agent.payment.recipient_address or "",
                asset=agent.payment.asset or "",
                token_address=agent.payment.token_address or "",
                default_price=agent.payment.default_price or "",
                currency=agent.payment.currency or "",
                facilitator_url=agent.payment.facilitator_url or "",
            )

        payment = registry_pb2.PaymentInfo(
            type=agent.payment.type.lower() if agent.payment else "none",
            config=payment_config,
        )

        # Build capabilities
        capabilities = []
        for cap in agent.capabilities:
            # Convert JSON to Struct
            input_schema = Struct()
            if cap.input_schema:
                input_schema.update(cap.input_schema)

            output_schema = Struct()
            if cap.output_schema:
                output_schema.update(cap.output_schema)

            arguments_struct = Struct()
            if cap.arguments:
                arguments_struct.update({"args": cap.arguments})

            # Get per-capability auth strategies (for A2A)
            cap_auth_strategies = []
            for auth in cap.auth_strategies or []:
                config_struct = Struct()
                config_struct.update(auth.config)
                cap_auth_strategies.append(
                    registry_pb2.AuthStrategy(
                        id=auth.strategy_id,
                        type=auth.type.lower(),
                        config=config_struct,
                    )
                )

            capability = registry_pb2.Capability(
                type=cap.type.lower(),
                id=cap.capability_id,
                name=cap.name,
                description=cap.description,
                input_schema=input_schema if cap.input_schema else None,
                output_schema=output_schema if cap.output_schema else None,
                uri_template=cap.uri_template or "",
                mime_type=cap.mime_type or "",
                arguments=arguments_struct if cap.arguments else None,
                x402_price="",
                x402_asset="",
                auth_strategies=cap_auth_strategies,
            )
            capabilities.append(capability)

        # Build complete manifest
        return registry_pb2.UniversalManifest(
            identity=identity,
            metadata=metadata,
            protocol=protocol,
            security=security,
            payment=payment,
            capabilities=capabilities,
        )
