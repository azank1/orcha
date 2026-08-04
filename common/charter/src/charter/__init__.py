"""AAC charter — signed scope charters and delegation attenuation (RFC 0002).

Pure library: no DB, HTTP, or web framework. Signing reuses the
``emerge_node.envelope`` crypto implementation — one canonicalisation scheme
and one Ed25519 verify path across the repo.
"""
