"""Notion page creation tool"""
import structlog
from typing import Dict, Any, List, Optional
from notion_client import AsyncClient
from ..config import settings

logger = structlog.get_logger()


async def create_research_note(
    title: str,
    topic: str,
    workspace_id: str,
    sections: Optional[List[Dict[str, str]]] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a research note in Notion with structured content
    
    Args:
        title: Page title
        topic: Research topic/subject
        workspace_id: Notion database/parent page ID
        sections: List of sections with headings and content
        tags: Tags for categorization
        
    Returns:
        Dict with page_id and url
    """
    logger.info("create_notion_note", title=title, topic=topic)
    
    # Initialize Notion client
    notion = AsyncClient(auth=settings.notion_api_key)
    
    try:
        # Build page properties
        properties = {
            "Name": {"title": [{"text": {"content": title}}]},
        }
        
        if tags:
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in tags]
            }
        
        # Build page content blocks
        children = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"text": {"content": topic}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "text": {
                            "content": f"Created: {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
                        }
                    }]
                }
            }
        ]
        
        # Add sections if provided
        if sections:
            for section in sections:
                # Section heading
                children.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": section["heading"]}}]
                    }
                })
                
                # Section content (split into paragraphs)
                paragraphs = section["content"].split("\n\n")
                for para in paragraphs:
                    if para.strip():
                        children.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"text": {"content": para.strip()}}]
                            }
                        })
        
        # Create the page
        page = await notion.pages.create(
            parent={"database_id": workspace_id} if len(workspace_id) == 32 else {"page_id": workspace_id},
            properties=properties,
            children=children
        )
        
        logger.info("notion_note_created", page_id=page["id"])
        
        return {
            "page_id": page["id"],
            "url": page["url"],
            "title": title,
            "status": "created"
        }
        
    except Exception as e:
        logger.error("notion_note_error", error=str(e))
        raise Exception(f"Failed to create Notion note: {str(e)}")
