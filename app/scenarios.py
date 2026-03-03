"""
Shared benchmark scenarios used by both benchmarking.py and the test suite.
Adding or editing a scenario here propagates the change everywhere automatically.
"""

SCENARIOS: dict[str, str] = {
    "E-commerce backend": (
        "A highly scalable e-commerce platform that needs to handle 10,000 concurrent users "
        "during flash sales. Needs product catalog, user carts, checkout, payment gateway "
        "integration, and order management."
    ),
    "EdTech exam platform": (
        "An online examination platform for students. Needs real-time question delivery, "
        "automated grading, secure student sessions to prevent cheating, and a teacher "
        "dashboard for analytics."
    ),
    "AI SaaS product": (
        "A B2B SaaS application that allows users to upload large PDF documents, extracts "
        "text asynchronously using an AI model, stores embeddings for vector search, and "
        "provides a chat interface to query the documents."
    ),
}
