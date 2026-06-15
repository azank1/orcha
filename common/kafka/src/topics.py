"""Kafka topic name constants shared across all Metaorcha services."""


class KafkaTopics:
    # Registry Service → Planning & Discovery Service
    REGISTRY_AGENT_REGISTERED = "registry.agent.registered"

    # Gateway Service → Planning & Discovery Service
    GATEWAY_USER_QUERY = "gateway.user.query"

    # Planning & Discovery Service → downstream consumers
    PLANNING_MANIFEST_CREATED = "planning.manifest.created"
    PLANNING_VALIDATION_FAILED = "planning.validation.failed"
    PLANNING_METRICS = "planning.metrics"

    # SuperAgent → validator nodes (DAN Phase D1)
    EXECUTION_STEP_COMPLETE = "execution.step_complete"
