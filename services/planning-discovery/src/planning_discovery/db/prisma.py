"""Global Prisma client instance for the Planning & Discovery Service."""

from common.database.src.generated_client import Prisma

# Single shared client — connected/disconnected in main.py lifespan
prisma = Prisma()
