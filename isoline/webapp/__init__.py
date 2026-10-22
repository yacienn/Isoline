"""Isoline web application, organised as a clean architecture.

    domain          business rules (verdicts, risk, findings) - pure Python, no I/O
    application     use cases and the ports (interfaces) they need
    infrastructure  adapters that implement the ports (subprocess scanner, temp files)
    interface       HTTP: controllers, presenters, static files, stdlib server adapter
    container.py    composition root: the ONLY place that wires the layers together

Dependencies point inwards only:  interface/infrastructure -> application -> domain.
tests/test_architecture.py enforces this.
"""
