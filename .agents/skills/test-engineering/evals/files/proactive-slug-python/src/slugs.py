def slugify(label: str) -> str:
    """Convert a display label into a route segment."""
    return label.strip().lower().replace(" ", "-")
