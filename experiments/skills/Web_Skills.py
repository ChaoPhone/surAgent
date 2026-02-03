from duckduckgo_search import DDGS


def web_search(query: str, max_results: int = 3):
    """
    进行联网搜索。用于获取最新的文档、库的使用方法或修复未知Bug。
    Args:
        query: 搜索关键词
        max_results: 返回结果数量
    """
    try:
        print(f"🌍 Searching web for: {query}...")
        results = DDGS().text(query, max_results=max_results)

        if not results:
            return "No results found."

        formatted_results = ""
        for i, res in enumerate(results):
            formatted_results += f"Result {i + 1}:\n"
            formatted_results += f"Title: {res.get('title')}\n"
            formatted_results += f"Snippet: {res.get('body')}\n"
            formatted_results += f"Link: {res.get('href')}\n\n"

        return formatted_results
    except Exception as e:
        return f"Search Engine Error: {str(e)}"