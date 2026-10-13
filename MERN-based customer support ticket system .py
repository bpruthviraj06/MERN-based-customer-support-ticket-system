from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import uuid

app = FastAPI(
    title="Customer Support Ticket System",
    description="Backend API for managing customer support tickets",
    version="1.0.0"
)

security = HTTPBearer()

# --- In-Memory Database Simulation ---
FAKE_USERS_DB = {
    "token_customer": {"id": "user_001", "role": "customer", "username": "alice"},
    "token_agent": {"id": "user_002", "role": "agent", "username": "bob_support"}
}

TICKETS_DB = {}

# --- Pydantic Models (Input / Output Validation) ---
class TicketCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=100, description="Brief summary of the issue")
    description: str = Field(..., min_length=10, description="Detailed explanation of the problem")
    priority: Optional[str] = Field("Medium", description="Low, Medium, or High")
    category: str = Field(..., description="Billing, Technical, General, etc.")

class TicketUpdateStatus(BaseModel):
    status: str = Field(..., description="Open, In Progress, Resolved, or Closed")

class TicketResponse(BaseModel):
    id: str
    customer_id: str
    title: str
    description: str
    status: str
    priority: str
    category: str
    created_at: datetime

class TicketCreateResponse(BaseModel):
    success: bool
    ticket: TicketResponse

class TicketUpdateResponse(BaseModel):
    success: bool
    message: str
    ticket: TicketResponse

# --- Authentication Dependency ---
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = FAKE_USERS_DB.get(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        )
    return user

# --- API Endpoints ---

@app.post("/api/tickets", response_model=TicketCreateResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(ticket_data: TicketCreate, current_user: dict = Depends(get_current_user)):
    """
    Create a new support ticket. Only accessible by authenticated customers.
    """
    if current_user["role"] != "customer":
        raise HTTPException(status_code=403, detail="Only customers can create tickets.")

    ticket_id = str(uuid.uuid4())
    new_ticket = {
        "id": ticket_id,
        "customer_id": current_user["id"],
        "title": ticket_data.title,
        "description": ticket_data.description,
        "status": "Open",
        "priority": ticket_data.priority,
        "category": ticket_data.category,
        "created_at": datetime.now(timezone.utc)
    }
    
    TICKETS_DB[ticket_id] = new_ticket
    return {"success": True, "ticket": new_ticket}

@app.get("/api/tickets", response_model=List[TicketResponse])
def get_tickets(current_user: dict = Depends(get_current_user)):
    """
    Retrieve tickets. Customers see their own tickets; Agents see all tickets.
    """
    tickets = list(TICKETS_DB.values())
    
    if current_user["role"] == "customer":
        tickets = [t for t in tickets if t["customer_id"] == current_user["id"]]
        
    return tickets

@app.patch("/api/tickets/{ticket_id}/status", response_model=TicketUpdateResponse)
def update_ticket_status(ticket_id: str, update_data: TicketUpdateStatus, current_user: dict = Depends(get_current_user)):
    """
    Update ticket status. Restricted to support agents.
    """
    if current_user["role"] != "agent":
        raise HTTPException(status_code=403, detail="Only support agents can update ticket statuses.")
        
    ticket = TICKETS_DB.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
        
    valid_statuses = ["Open", "In Progress", "Resolved", "Closed"]
    if update_data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Choose from {valid_statuses}")
        
    ticket["status"] = update_data.status
    TICKETS_DB[ticket_id] = ticket
    
    return {
        "success": True, 
        "message": f"Ticket status updated to {update_data.status}", 
        "ticket": ticket
    }

# --- Optional: Run directly using python Hackathon.py ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("Hackathon:app", host="127.0.0.1", port=8000, reload=True)