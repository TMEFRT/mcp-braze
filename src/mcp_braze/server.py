import asyncio
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from datetime import datetime

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl, BaseModel
import mcp.server.stdio

# Store notes as a simple key-value dict to demonstrate state management
notes: dict[str, str] = {}

# Braze API configuration
class BrazeConfig:
    def __init__(self):
        self.api_token: Optional[str] = None
        self.base_url: str = "https://rest.iad-01.braze.com"  # Default to US-01 instance

    def is_configured(self) -> bool:
        return self.api_token is not None

braze_config = BrazeConfig()

# Braze catalog data structures
class CatalogItem(BaseModel):
    id: str
    name: str
    description: Optional[str]
    attributes: Dict[str, Any]

catalogs: Dict[str, Dict[str, Any]] = {}
catalog_items: Dict[str, Dict[str, CatalogItem]] = {}

server = Server("mcp-braze")

# Email subscription status enum
class EmailSubscriptionStatus(str, Enum):
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    OPTED_IN = "opted_in"

# Email data structures
class EmailSubscription(BaseModel):
    email: str
    status: EmailSubscriptionStatus
    subscription_group_id: Optional[str] = None

# Segment data structures
class Segment(BaseModel):
    id: str
    name: str
    analytics_tracking_enabled: bool
    tags: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    description: Optional[str] = None
    text_description: Optional[str] = None
    teams: List[str] = []

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available note resources.
    Each note is exposed as a resource with a custom note:// URI scheme.
    """
    return [
        types.Resource(
            uri=AnyUrl(f"note://internal/{name}"),
            name=f"Note: {name}",
            description=f"A simple note named {name}",
            mimeType="text/plain",
        )
        for name in notes
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific note's content by its URI.
    The note name is extracted from the URI host component.
    """
    if uri.scheme != "note":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    name = uri.path
    if name is not None:
        name = name.lstrip("/")
        return notes[name]
    raise ValueError(f"Note not found: {name}")

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts.
    Each prompt can have optional arguments to customize its behavior.
    """
    return [
        types.Prompt(
            name="summarize-notes",
            description="Creates a summary of all notes",
            arguments=[
                types.PromptArgument(
                    name="style",
                    description="Style of the summary (brief/detailed)",
                    required=False,
                )
            ],
        )
    ]

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate a prompt by combining arguments with server state.
    The prompt includes all current notes and can be customized via arguments.
    """
    if name != "summarize-notes":
        raise ValueError(f"Unknown prompt: {name}")

    style = (arguments or {}).get("style", "brief")
    detail_prompt = " Give extensive details." if style == "detailed" else ""

    return types.GetPromptResult(
        description="Summarize the current notes",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Here are the current notes to summarize:{detail_prompt}\n\n"
                    + "\n".join(
                        f"- {name}: {content}"
                        for name, content in notes.items()
                    ),
                ),
            )
        ],
    )

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="configure-braze",
            description="Configure Braze API settings including authentication token",
            inputSchema={
                "type": "object",
                "properties": {
                    "api_token": {"type": "string", "description": "Braze API token"},
                    "base_url": {
                        "type": "string", 
                        "description": "Braze API base URL (optional, defaults to US-01 instance)",
                        "default": "https://rest.iad-01.braze.com"
                    },
                },
                "required": ["api_token"],
            },
        ),
        types.Tool(
            name="add-note",
            description="Add a new note",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["name", "content"],
            },
        ),
        types.Tool(
            name="create-catalog",
            description="Create a new Braze catalog",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the catalog"},
                    "description": {"type": "string", "description": "Description of the catalog"},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="list-catalogs",
            description="List all Braze catalogs",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="create-catalog-item",
            description="Create a new item in a Braze catalog",
            inputSchema={
                "type": "object",
                "properties": {
                    "catalog_name": {"type": "string", "description": "Name of the catalog"},
                    "item_id": {"type": "string", "description": "Unique identifier for the item"},
                    "name": {"type": "string", "description": "Name of the item"},
                    "description": {"type": "string", "description": "Description of the item"},
                    "attributes": {"type": "object", "description": "Additional attributes for the item"},
                },
                "required": ["catalog_name", "item_id", "name"],
            },
        ),
        types.Tool(
            name="list-catalog-items",
            description="List items in a Braze catalog",
            inputSchema={
                "type": "object",
                "properties": {
                    "catalog_name": {"type": "string", "description": "Name of the catalog"},
                },
                "required": ["catalog_name"],
            },
        ),
        types.Tool(
            name="get-hard-bounced-emails",
            description="Query list of hard bounced email addresses",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "Start date in YYYY-MM-DD format (optional)"},
                    "end_date": {"type": "string", "description": "End date in YYYY-MM-DD format (optional)"},
                    "limit": {"type": "integer", "description": "Maximum number of email addresses to return (optional)"},
                    "offset": {"type": "integer", "description": "Number of email addresses to skip (optional)"},
                },
            },
        ),
        types.Tool(
            name="get-unsubscribed-emails",
            description="Query list of unsubscribed email addresses",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "Start date in YYYY-MM-DD format (optional)"},
                    "end_date": {"type": "string", "description": "End date in YYYY-MM-DD format (optional)"},
                    "limit": {"type": "integer", "description": "Maximum number of email addresses to return (optional)"},
                    "offset": {"type": "integer", "description": "Number of email addresses to skip (optional)"},
                },
            },
        ),
        types.Tool(
            name="update-email-subscription",
            description="Change email subscription status",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email address to update"},
                    "status": {
                        "type": "string",
                        "enum": ["subscribed", "unsubscribed", "opted_in"],
                        "description": "New subscription status"
                    },
                    "subscription_group_id": {
                        "type": "string",
                        "description": "Optional subscription group ID"
                    }
                },
                "required": ["email", "status"],
            },
        ),
        types.Tool(
            name="remove-hard-bounced-email",
            description="Remove email address from hard bounce list",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email address to remove"},
                },
                "required": ["email"],
            },
        ),
        types.Tool(
            name="remove-from-spam",
            description="Remove email address from spam list",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email address to remove"},
                },
                "required": ["email"],
            },
        ),
        types.Tool(
            name="blocklist-email",
            description="Add email address to blocklist",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email address to blocklist"},
                },
                "required": ["email"],
            },
        ),
        types.Tool(
            name="list-segments",
            description="Export a list of segments with their details",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "The page of segments to return (defaults to 0)",
                        "minimum": 0
                    },
                    "sort_direction": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "Sort creation time (asc=oldest to newest, desc=newest to oldest)"
                    }
                }
            },
        ),
        types.Tool(
            name="get-segment-details",
            description="Get detailed information about a specific segment",
            inputSchema={
                "type": "object",
                "properties": {
                    "segment_id": {
                        "type": "string",
                        "description": "The Segment API identifier"
                    }
                },
                "required": ["segment_id"]
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can modify server state and notify clients of changes.
    """
    if name == "configure-braze":
        if not arguments:
            raise ValueError("Missing arguments")

        api_token = arguments.get("api_token")
        if not api_token:
            raise ValueError("API token is required")

        base_url = arguments.get("base_url", braze_config.base_url)
        
        # Update configuration
        braze_config.api_token = api_token
        braze_config.base_url = base_url

        return [
            types.TextContent(
                type="text",
                text=f"Braze API configured successfully with base URL: {base_url}"
            )
        ]

    # Add auth check for all Braze-related operations
    if name in [
        "create-catalog", "list-catalogs", "create-catalog-item", "list-catalog-items",
        "get-hard-bounced-emails", "get-unsubscribed-emails", "update-email-subscription",
        "remove-hard-bounced-email", "remove-from-spam", "blocklist-email",
        "list-segments", "get-segment-details"
    ]:
        if not braze_config.is_configured():
            raise ValueError("Braze API is not configured. Please use configure-braze tool first.")

    if name == "add-note":
        if not arguments:
            raise ValueError("Missing arguments")

        note_name = arguments.get("name")
        content = arguments.get("content")

        if not note_name or not content:
            raise ValueError("Missing name or content")

        # Update server state
        notes[note_name] = content

        # Notify clients that resources have changed
        await server.request_context.session.send_resource_list_changed()

        return [
            types.TextContent(
                type="text",
                text=f"Added note '{note_name}' with content: {content}",
            )
        ]
    
    elif name == "create-catalog":
        if not arguments:
            raise ValueError("Missing arguments")
        
        catalog_name = arguments.get("name")
        description = arguments.get("description", "")

        if catalog_name in catalogs:
            raise ValueError(f"Catalog '{catalog_name}' already exists")

        catalogs[catalog_name] = {
            "name": catalog_name,
            "description": description,
            "created_at": asyncio.get_event_loop().time(),
        }
        catalog_items[catalog_name] = {}

        return [
            types.TextContent(
                type="text",
                text=f"Created catalog '{catalog_name}' with description: {description}",
            )
        ]

    elif name == "list-catalogs":
        if not catalogs:
            return [types.TextContent(type="text", text="No catalogs found")]

        catalog_list = "\n".join([
            f"- {name}: {data['description']}"
            for name, data in catalogs.items()
        ])
        return [types.TextContent(type="text", text=f"Available catalogs:\n{catalog_list}")]

    elif name == "create-catalog-item":
        if not arguments:
            raise ValueError("Missing arguments")

        catalog_name = arguments.get("catalog_name")
        if catalog_name not in catalogs:
            raise ValueError(f"Catalog '{catalog_name}' does not exist")

        item_id = arguments.get("item_id")
        name = arguments.get("name")
        description = arguments.get("description", "")
        attributes = arguments.get("attributes", {})

        if item_id in catalog_items[catalog_name]:
            raise ValueError(f"Item '{item_id}' already exists in catalog '{catalog_name}'")

        item = CatalogItem(
            id=item_id,
            name=name,
            description=description,
            attributes=attributes
        )
        catalog_items[catalog_name][item_id] = item

        return [
            types.TextContent(
                type="text",
                text=f"Created item '{item_id}' in catalog '{catalog_name}'"
            )
        ]

    elif name == "list-catalog-items":
        if not arguments:
            raise ValueError("Missing arguments")

        catalog_name = arguments.get("catalog_name")
        if catalog_name not in catalogs:
            raise ValueError(f"Catalog '{catalog_name}' does not exist")

        if not catalog_items[catalog_name]:
            return [types.TextContent(type="text", text=f"No items found in catalog '{catalog_name}'")]

        items_list = "\n".join([
            f"- {item.id}: {item.name} ({item.description})"
            for item in catalog_items[catalog_name].values()
        ])
        return [types.TextContent(type="text", text=f"Items in catalog '{catalog_name}':\n{items_list}")]

    elif name == "get-hard-bounced-emails":
        if not arguments:
            arguments = {}
        
        # Here you would make an actual API call to Braze
        # For now, return a sample response
        return [
            types.TextContent(
                type="text",
                text="Retrieved hard bounced emails with parameters:\n" + 
                     f"Start Date: {arguments.get('start_date', 'not specified')}\n" +
                     f"End Date: {arguments.get('end_date', 'not specified')}\n" +
                     f"Limit: {arguments.get('limit', 'not specified')}\n" +
                     f"Offset: {arguments.get('offset', 'not specified')}"
            )
        ]

    elif name == "get-unsubscribed-emails":
        if not arguments:
            arguments = {}
        
        return [
            types.TextContent(
                type="text",
                text="Retrieved unsubscribed emails with parameters:\n" + 
                     f"Start Date: {arguments.get('start_date', 'not specified')}\n" +
                     f"End Date: {arguments.get('end_date', 'not specified')}\n" +
                     f"Limit: {arguments.get('limit', 'not specified')}\n" +
                     f"Offset: {arguments.get('offset', 'not specified')}"
            )
        ]

    elif name == "update-email-subscription":
        if not arguments:
            raise ValueError("Missing arguments")

        email = arguments.get("email")
        status = arguments.get("status")
        subscription_group_id = arguments.get("subscription_group_id")

        if not email or not status:
            raise ValueError("Email and status are required")

        subscription = EmailSubscription(
            email=email,
            status=EmailSubscriptionStatus(status),
            subscription_group_id=subscription_group_id
        )

        return [
            types.TextContent(
                type="text",
                text=f"Updated subscription status for {email} to {status}" +
                     (f" in group {subscription_group_id}" if subscription_group_id else "")
            )
        ]

    elif name == "remove-hard-bounced-email":
        if not arguments or "email" not in arguments:
            raise ValueError("Email address is required")

        email = arguments["email"]
        return [
            types.TextContent(
                type="text",
                text=f"Removed {email} from hard bounce list"
            )
        ]

    elif name == "remove-from-spam":
        if not arguments or "email" not in arguments:
            raise ValueError("Email address is required")

        email = arguments["email"]
        return [
            types.TextContent(
                type="text",
                text=f"Removed {email} from spam list"
            )
        ]

    elif name == "blocklist-email":
        if not arguments or "email" not in arguments:
            raise ValueError("Email address is required")

        email = arguments["email"]
        return [
            types.TextContent(
                type="text",
                text=f"Added {email} to blocklist"
            )
        ]

    elif name == "list-segments":
        if not arguments:
            arguments = {}

        page = arguments.get("page", 0)
        sort_direction = arguments.get("sort_direction", "asc")

        # Here you would make an actual API call to Braze
        # For demonstration, return a sample response
        sample_segments = [
            Segment(
                id="segment1",
                name="Active Users",
                analytics_tracking_enabled=True,
                tags=["engagement", "active"],
            ),
            Segment(
                id="segment2",
                name="Churned Users",
                analytics_tracking_enabled=True,
                tags=["retention", "inactive"],
            )
        ]

        segments_list = "\n".join([
            f"- {segment.name} (ID: {segment.id})\n  Tags: {', '.join(segment.tags)}\n  Analytics Enabled: {segment.analytics_tracking_enabled}"
            for segment in sample_segments
        ])

        return [
            types.TextContent(
                type="text",
                text=f"Segments (Page {page}, Sort: {sort_direction}):\n{segments_list}"
            )
        ]

    elif name == "get-segment-details":
        if not arguments or "segment_id" not in arguments:
            raise ValueError("segment_id is required")

        segment_id = arguments["segment_id"]

        # Here you would make an actual API call to Braze
        # For demonstration, return a sample response
        sample_segment = Segment(
            id=segment_id,
            name="Sample Segment",
            analytics_tracking_enabled=True,
            tags=["sample", "test"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            description="Users who match specific criteria",
            text_description="This is a sample segment description",
            teams=["Marketing", "Product"]
        )

        return [
            types.TextContent(
                type="text",
                text=f"Segment Details for {segment_id}:\n" +
                     f"Name: {sample_segment.name}\n" +
                     f"Created: {sample_segment.created_at}\n" +
                     f"Updated: {sample_segment.updated_at}\n" +
                     f"Description: {sample_segment.description}\n" +
                     f"Text Description: {sample_segment.text_description}\n" +
                     f"Tags: {', '.join(sample_segment.tags)}\n" +
                     f"Teams: {', '.join(sample_segment.teams)}\n" +
                     f"Analytics Tracking: {sample_segment.analytics_tracking_enabled}"
            )
        ]

    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-braze",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )