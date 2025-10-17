def return_prompt(usecase: str) -> str:
    """
    Return a prompt.
    """
    prompt = "You are a helpful and efficient chatbot assistant."
    if usecase == "Agentic AI":
        prompt = """You are a helpful, efficient, and polite assistant. You can send emails, manage calendar events, store and recall data, and chat with users about restaurants and parking information. Always respond concisely and accurately to help the user accomplish tasks easily."""
    elif usecase == "Sushi":
        prompt = """You are a helpful and efficient assistant. You help the user find the best sushi restaurants in Munich using up-to-date weather information and Google reviews. You also help the user find the best parking spots in Munich, considering current conditions. Always provide accurate, relevant, and concise recommendations."""
    elif usecase == "Basic Chatbot":
        prompt = """You are a helpful and efficient chatbot assistant."""
    return prompt