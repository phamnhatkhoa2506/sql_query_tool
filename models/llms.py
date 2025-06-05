from langchain_google_genai import ChatGoogleGenerativeAI


def load_llm(
    model_name: str, 
    temp: float = 0.0, 
    max_tokens: int = 100
) -> any:
    """
        Load LLm Model

        Args:
            model_name(str): The name of the model
            temp(float): The temperature argument
            max_tokens(str): Max token the model can generate

        Raises:
            ValueError: The model name not found

        Return the LLM Model
    """

    if model_name == "gemini-2.0-flash":
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temp,
            max_tokens=max_tokens,
        )
    else:
        raise ValueError("###### Model is not supported ######")
