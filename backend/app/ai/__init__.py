"""Thin AI layer. Receives STRUCTURED resume JSON, never raw PDF text.

Keep this small on purpose. The project's value is the parser; the LLM only
critiques and rewrites what the parser already understood.
"""
