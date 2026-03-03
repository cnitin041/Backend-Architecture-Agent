from typing import List, Optional
from pydantic import BaseModel, Field


class TechStack(BaseModel):
    language: str = Field(..., description="The primary programming language.")
    framework: str = Field(..., description="The primary web framework (e.g., FastAPI, Express).")
    database: str = Field(..., description="The primary database technology (e.g., PostgreSQL, MongoDB).")
    cache: Optional[str] = Field(None, description="Caching technology, if applicable (e.g., Redis).")
    message_queue: Optional[str] = Field(None, description="Message queue technology, if applicable.")


class APIRoute(BaseModel):
    method: str = Field(..., description="HTTP Method (GET, POST, PUT, DELETE, PATCH).")
    path: str = Field(..., description="The endpoint path (e.g., /api/v1/users).")
    description: str = Field(..., description="A brief description of the route's purpose.")


class DatabaseField(BaseModel):
    name: str = Field(..., description="Field name.")
    type: str = Field(..., description="Data type (e.g., UUID, VARCHAR, INTEGER, TIMESTAMP).")
    is_primary: bool = Field(False, description="Is this a primary key?")
    is_foreign: bool = Field(False, description="Is this a foreign key?")
    description: Optional[str] = Field(None, description="Purpose of this field.")


class DatabaseEntity(BaseModel):
    name: str = Field(..., description="Table or Collection name.")
    fields: List[DatabaseField] = Field(..., description="List of columns/fields.")
    relationships: List[str] = Field(
        default_factory=list,
        description="Description of relationships (e.g., 'One-to-Many with User table via user_id')."
    )


class ArchitectureBlueprint(BaseModel):
    """The final output schema expected from the Backend Architecture Agent."""

    recommended_stack: TechStack = Field(..., description="The recommended backend technology stack.")
    api_routes: List[APIRoute] = Field(..., description="A proposed list of foundational API routes.")
    database_schema: List[DatabaseEntity] = Field(..., description="The proposed database entities and relationships.")
    folder_structure: List[str] = Field(
        ..., description="Suggested core folder structure (e.g., ['app/', 'app/models/', 'app/routers/'])."
    )
    deployment_recommendations: str = Field(
        ..., description="Detailed advice on deployment (e.g., Docker, AWS ECS, K8s)."
    )
    scaling_recommendations: str = Field(
        ..., description="Detailed advice on scaling (e.g., caching strategies, replication, CDN)."
    )
