from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict

from patas_backend.auth.dependencies import get_current_user
from patas_backend.models.adoption import InvalidTransition
from patas_backend.models.conversation import InvalidMessage, MessageView
from patas_backend.models.user import User
from patas_backend.services.conversation import ConversationService

router = APIRouter()


class MessageBody(BaseModel):
    # Types only. The rules (not blank, at most 2000 characters) live in the domain.
    # Unknown fields are a 422: who writes is the caller, never sent.
    model_config = ConfigDict(extra="forbid")

    body: str


class MessageResponse(BaseModel):
    id: UUID
    application_id: UUID
    sender_id: UUID
    sender_name: str
    sender_username: str
    body: str
    sent_at: datetime

    @classmethod
    def from_view(cls, view: MessageView) -> "MessageResponse":
        return cls(
            id=view.id,
            application_id=view.application_id,
            sender_id=view.sender_id,
            sender_name=view.sender_name,
            sender_username=view.sender_username,
            body=view.body,
            sent_at=view.sent_at,
        )


def get_conversation_service(request: Request) -> ConversationService:
    return ConversationService(
        request.app.state.session_factory, request.app.state.dispatcher
    )


@router.get(
    "/applications/{application_id}/messages", response_model=list[MessageResponse]
)
async def read_messages(
    application_id: UUID,
    actor: Annotated[User, Depends(get_current_user)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    after: UUID | None = None,
) -> list[MessageResponse]:
    """The conversation of a request, oldest first; with `after`, the newer ones."""
    messages = await service.read(actor, application_id, after)
    if messages is None:
        # Also for someone who is neither side, and for a request never accepted.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return [MessageResponse.from_view(message) for message in messages]


@router.post(
    "/applications/{application_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_message(
    application_id: UUID,
    body: MessageBody,
    actor: Annotated[User, Depends(get_current_user)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> MessageResponse:
    """Owner or applicant writes in the conversation while the request is accepted."""
    try:
        view = await service.post(actor, application_id, body.body)
    except InvalidMessage as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
        ) from error
    except InvalidTransition as error:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"code": "conversation_closed", "message": str(error)},
        ) from error
    if view is None:
        # Also for someone who is neither side: to them the request does not exist.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
    return MessageResponse.from_view(view)
