# MCP Braze Integration

A Model context Protocol (MCP) integration for Braze's REST API, allowing you to manage catalogs, emails, segments, and more through a simple interface.

## Features

- **Authentication Management**
  - Configure Braze API token and base URL
  - Automatic authentication for all API operations

- **Catalog Management**
  - Create and list catalogs
  - Add and list catalog items
  - Support for item attributes and metadata

- **Email Management**
  - Query hard bounced and unsubscribed emails
  - Update email subscription status
  - Manage spam and blocklist entries
  - Support for subscription groups

- **Segment Management**
  - List all segments with pagination
  - Get detailed segment information
  - Support for analytics tracking

## Installation

```bash
pip install mcp-braze
```

## Configuration

Before using the integration, configure your Braze API credentials:

```python
{
    "api_token": "your-braze-api-token",
    "base_url": "https://rest.iad-01.braze.com"  # Optional, defaults to US-01 instance
}
```

## Usage Examples

### Managing Catalogs

```python
# Create a catalog
{
    "name": "products",
    "description": "Our product catalog"
}

# Add items to catalog
{
    "catalog_name": "products",
    "item_id": "prod-123",
    "name": "Sample Product",
    "description": "A great product",
    "attributes": {
        "price": 99.99,
        "category": "electronics"
    }
}
```

### Managing Emails

```python
# Update email subscription
{
    "email": "user@example.com",
    "status": "subscribed",
    "subscription_group_id": "group-123"  # optional
}

# Query bounced emails
{
    "start_date": "2024-01-01",
    "end_date": "2024-03-20",
    "limit": 100,
    "offset": 0
}
```

### Managing Segments

```python
# List segments
{
    "page": 0,
    "sort_direction": "desc"
}

# Get segment details
{
    "segment_id": "your-segment-id"
}
```

## Development

1. Clone the repository:
```bash
git clone https://github.com/TMEFRT/mcp-braze.git
cd mcp-braze
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run tests:
```bash
pytest
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
