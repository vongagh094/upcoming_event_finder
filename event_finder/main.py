# main.py
from contextlib import asynccontextmanager
from typing import Optional, Literal
from fastapi import FastAPI, Query, HTTPException
from event_finder.schemas import EventsResponse
from event_finder.services.workflow import find_upcoming_events



# The first part of the function, before the yield, will
# be executed before the application starts.
# https://fastapi.tiangolo.com/advanced/events/#lifespan-function
@asynccontextmanager
async def lifespan(app: FastAPI):
	print("Starting the application..")
	yield



app = FastAPI(lifespan=lifespan)




@app.get("/events", response_model=EventsResponse)
async def get_events(
	name: str = Query(..., description="Person or speaker name to search for"),
	event_type: Optional[Literal["in_person", "online"]] = Query(None, description="Filter by event type"),
):
	"""
	Search for events by name with optional event type filtering.
	"""
	if not name or not name.strip():
		raise HTTPException(status_code=400, detail="Parameter 'name' is required")
	if event_type and event_type not in ["in_person", "online"]:
		raise HTTPException(status_code=400, detail="Parameter 'event_type' must be 'in_person' or 'online'")
	try:
		response = await find_upcoming_events(user_query=name, filter_event_type=event_type)
		return response
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


