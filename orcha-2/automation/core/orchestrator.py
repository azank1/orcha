from mcp.search.indexer import MenuIndexer
from mcp.search.engine import SearchEngine
from mcp.models.base import Category, MenuItem, SizePrice


class ConversationOrchestrator:
    def __init__(self, llm_client, state_manager):
        self.llm = llm_client
        self.state = state_manager

    def _get_demo_engine(self):
        # Simple demo menu; replace with real data source later
        categories = [
            Category(category="Pizza", items=[
                MenuItem(item="Margherita Pizza", sizePrices=[SizePrice(size="Regular", price=12.99)]),
                MenuItem(item="Pepperoni Pizza", sizePrices=[SizePrice(size="Regular", price=14.99)]),
                MenuItem(item="Hawaiian Pizza", sizePrices=[SizePrice(size="Regular", price=15.99)]),
            ])
        ]
        indexer = MenuIndexer(categories)
        return SearchEngine(indexer)

    async def process_user_intent(self, text: str, session_id: str):
        # Parse intent using hybrid LLM client
        intent = await self.llm.parse_intent(text)
        intent_type = intent.get("type", "unknown")
        source = intent.get("source", "unknown")
        raw = intent.get("raw")

        if intent_type == "search":
            engine = self._get_demo_engine()
            results_items = engine.search(text, top_k=5)
            results = [item.item for item in results_items]
            return {"type": "search", "results": results, "llm_source": source, "llm_raw": raw}
        elif intent_type == "order":
            # Prepare, validate, and submit order (stub)
            draft = {"order": "draft"}
            valid = True
            if valid:
                return {"type": "order", "status": "submitted", "details": draft, "llm_source": source, "llm_raw": raw}
        return {"message": "Sorry, I didn’t understand.", "llm_source": source, "llm_raw": raw}
