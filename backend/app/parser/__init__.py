"""The parser package.

IMPORTANT: nothing in here may import FastAPI. These are pure functions over the
schemas in app.schemas. That keeps the core logic testable in isolation and is the
part of the project that actually demonstrates engineering ability.

Pipeline order:
    extract -> lines -> sections -> entries -> bullets -> fields -> assemble
"""
