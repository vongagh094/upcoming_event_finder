import requests 
from openai import OpenAI
from event_finder.core.models import ListEvent
from event_finder.config.settings import OPENAI_API_KEY


_openai_client = None
class OpenAIClient:
    def __init__(self, model: str = "gpt-4o-mini"):
        if not model:
            raise ValueError("Model is required")
        self.client = OpenAI(api_key=str(OPENAI_API_KEY))
        self.model = model
        
    async def parse_structured_output(self, user_prompt: str) -> ListEvent:
        """
        Parse a structured output with pydantic model and return a ExtractedContent object.

        """
        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts event details from a webpage."},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=ListEvent,
            )
            
            event_list = completion.choices[0].message.parsed
            return event_list

        except Exception as e:
            raise ValueError(f"OpenAI API error: {str(e)}")
    

    
def get_openai_client(model: str = "gpt-4o-mini") -> OpenAIClient:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient(model=model)
    return _openai_client    






