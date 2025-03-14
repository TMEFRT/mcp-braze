# Braze Messaging Endpoints

This document provides an overview of the Braze Messaging API endpoints that can be used with the MCP Braze integration.

## Overview

The Braze Messaging API provides two distinct options for sending messages to your users:

1. **Direct Message Content**: Provide the message contents and configuration in the API request with the `/messages/send` and `/messages/schedule` endpoints.
2. **API-Triggered Campaigns**: Manage the details of your message with an API-triggered campaign in the Braze dashboard and control when and to whom it is sent with the `/campaigns/trigger/send` and `/campaigns/trigger/schedule` endpoints.

Similar to other campaigns, you can limit the number of times a particular user can receive a messaging API campaign by configuring re-eligibility settings in the Braze dashboard.

## Endpoint Categories

### Schedule Messages Endpoints

- **GET: List Upcoming Scheduled Campaigns and Canvases**
- **POST: Delete Scheduled Messages**
- **POST: Delete Scheduled API-Triggered Campaigns**
- **POST: Delete Scheduled API-Triggered Canvases**
- **POST: Schedule Messages**
- **POST: Schedule API-Triggered Campaign Messages**
- **POST: Schedule API-Triggered Canvas Messages**
- **POST: Update Scheduled Messages**
- **POST: Update Scheduled API-Triggered Campaign Messages**
- **POST: Update Scheduled API-Triggered Canvas Messages**

### Send Messages Endpoints

- **POST: Create Send IDs**
- **POST: Send Messages Immediately**
- **POST: Send API-Triggered Campaign Messages Immediately**
- **POST: Send API-Triggered Canvas Messages Immediately**

### Live Activity Endpoints

- **POST: Update Live Activity**

## Implementation in MCP Braze

The MCP Braze integration provides tools to interact with these endpoints. Here's how you can use them:

### Configuring Braze API

Before using any messaging endpoints, you need to configure the Braze API with your credentials:

```python
{
    "api_token": "your-braze-api-token",
    "base_url": "https://rest.iad-01.braze.com"  # Optional, defaults to US-01 instance
}
```

### Sending Messages

To send messages using the MCP Braze integration, you can use the following pattern:

```python
# Example of sending an immediate message
{
    "recipients": {
        "external_user_ids": ["user1", "user2"]
    },
    "message": {
        "email": {
            "subject": "Your Subject",
            "body": "Your email content here"
        }
    }
}
```

### Scheduling Messages

To schedule messages for future delivery:

```python
# Example of scheduling a message
{
    "recipients": {
        "external_user_ids": ["user1", "user2"]
    },
    "schedule": {
        "time": "2023-12-25T15:00:00Z"
    },
    "message": {
        "email": {
            "subject": "Holiday Greetings",
            "body": "Happy Holidays from our team!"
        }
    }
}
```

## Additional Resources

For more detailed information about the Braze Messaging API, refer to the [official Braze API documentation](https://www.braze.com/docs/api/endpoints/messaging).

## References

This documentation is based on information from:
- [Braze Messaging Endpoints](https://www.braze.com/docs/api/endpoints/messaging)