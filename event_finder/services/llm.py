import requests 
from openai import OpenAI
from pydantic import BaseModel
from event_finder.core.models import Event
from typing import List

class EventList(BaseModel):
    events: List[Event]


class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        if not api_key:
            raise ValueError("API key is required")
        
        if not model:
            raise ValueError("Model is required")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    async def parse_structured_output(self, user_prompt: str) -> EventList:
        """
        Parse a structured output with pydantic model and return a ExtractedContent object.

        """
        try:
            completion = self.client.responses.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts event details from a webpage."},
                    {"role": "user", "content": user_prompt}
                ],
                text_format=EventList,
            )
            
            event_list = completion.output_parsed
            return event_list

        except requests.exceptions.JSONDecodeError:
            raise ValueError("Invalid JSON in API response")
    

    
def get_openai_client(api_key: str, model: str = "gpt-4o-mini") -> OpenAIClient:
    return OpenAIClient(api_key, model)






