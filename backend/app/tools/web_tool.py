import requests
from app.tools.base import BaseTool


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search internet for information (requires search API key — currently returns placeholder)"
    parameters = {
        "query": {"type": "string", "description": "Search query"},
        "num_results": {"type": "integer", "description": "Number of results to return", "default": 5},
    }

    def execute(self, query: str, num_results: int = 5) -> str:
        # Placeholder — integrate a real search API (e.g. DuckDuckGo, SerpAPI) to enable
        return f"Web search is not configured. Query was: '{query}'. Integrate a search API to enable this tool."


class HttpRequestTool(BaseTool):
    name = "http_request"
    description = "Make HTTP request to external API"
    parameters = {
        "url": {"type": "string", "description": "URL to call"},
        "method": {"type": "string", "description": "HTTP method (GET, POST)", "default": "GET"},
        "headers": {"type": "object", "description": "Request headers"},
        "data": {"type": "object", "description": "Request data for POST requests"},
    }

    def execute(self, url: str, method: str = "GET", headers: dict = None, data: dict = None) -> str:
        try:
            if method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                response = requests.get(url, headers=headers, timeout=30)
            
            return f"Status: {response.status_code}\nContent: {response.text[:1000]}"
        except Exception as e:
            return f"Error: {e}"
