"""Utility functions for domain parsing and validation."""


def parse_excluded_domains(domains_str):
    """
    Parse and normalize a comma-separated list of excluded domains.

    Args:
        domains_str: Comma-separated string of domain names, or None

    Returns:
        List of normalized domain strings with whitespace trimmed and empty entries removed

    Examples:
        >>> parse_excluded_domains("ebay.com.au,amazon.com.au")
        ['ebay.com.au', 'amazon.com.au']

        >>> parse_excluded_domains(" ebay.com.au , amazon.com.au ")
        ['ebay.com.au', 'amazon.com.au']

        >>> parse_excluded_domains("ebay.com.au,,amazon.com.au, ,temu.com")
        ['ebay.com.au', 'amazon.com.au', 'temu.com']

        >>> parse_excluded_domains("")
        []

        >>> parse_excluded_domains(None)
        []
    """
    if not domains_str:
        return []

    # Split by comma, strip whitespace, filter empty strings
    domains = [d.strip() for d in domains_str.split(",") if d.strip()]

    # Filter out invalid entries (e.g., those starting with http:// or https://)
    valid_domains = []
    for domain in domains:
        # Skip if it looks like a full URL
        if domain.startswith(("http://", "https://", "ftp://")):
            continue
        # Skip if it contains path separators
        if "/" in domain:
            continue
        valid_domains.append(domain)

    return valid_domains
