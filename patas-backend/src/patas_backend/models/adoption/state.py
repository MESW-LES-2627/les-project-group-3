from datetime import datetime
from typing import TYPE_CHECKING, ClassVar, NoReturn

from patas_backend.models.adoption.errors import InvalidTransition
from patas_backend.models.adoption.events import (
    ApplicationAccepted,
    ApplicationAdopted,
    ApplicationClosed,
    ApplicationDeclined,
    ApplicationWithdrawn,
)
from patas_backend.models.adoption.status import ApplicationStatus

if TYPE_CHECKING:
    from patas_backend.models.adoption.application import AdoptionApplication

S = ApplicationStatus


class ApplicationState:
    """What an application in one status can do.

    Each status is one subclass. A subclass overrides only the changes that status
    allows; every other change is refused here. The states hold no data, so one
    instance of each is shared (see STATES).
    """

    status: ClassVar[ApplicationStatus]

    def accept(self, app: "AdoptionApplication", note: str | None) -> None:
        self._refuse("accepted")

    def decline(self, app: "AdoptionApplication", note: str | None) -> None:
        self._refuse("declined")

    def withdraw(self, app: "AdoptionApplication") -> None:
        self._refuse("withdrawn")

    def confirm_handover(
        self, app: "AdoptionApplication", by_owner: bool, at: datetime
    ) -> None:
        self._refuse("handed over")

    def close(self, app: "AdoptionApplication") -> None:
        self._refuse("closed")

    def _refuse(self, action: str) -> NoReturn:
        raise InvalidTransition(
            f"an application that is {self.status.value} cannot be {action}"
        )


class _ActiveState(ApplicationState):
    """Open and Accepted: both can still be declined or withdrawn."""

    def decline(self, app: "AdoptionApplication", note: str | None) -> None:
        app.owner_note = note
        app._become(
            S.DECLINED,
            ApplicationDeclined(
                application_id=app.id,
                animal_id=app.animal_id,
                was_accepted=self.status is S.ACCEPTED,
            ),
        )

    def withdraw(self, app: "AdoptionApplication") -> None:
        app._become(
            S.WITHDRAWN,
            ApplicationWithdrawn(
                application_id=app.id,
                animal_id=app.animal_id,
                was_accepted=self.status is S.ACCEPTED,
            ),
        )


class OpenState(_ActiveState):
    status = S.OPEN

    def accept(self, app: "AdoptionApplication", note: str | None) -> None:
        app.owner_note = note
        app._become(
            S.ACCEPTED,
            ApplicationAccepted(application_id=app.id, animal_id=app.animal_id),
        )

    def close(self, app: "AdoptionApplication") -> None:
        app._become(
            S.CLOSED,
            ApplicationClosed(application_id=app.id, animal_id=app.animal_id),
        )


class AcceptedState(_ActiveState):
    status = S.ACCEPTED

    def confirm_handover(
        self, app: "AdoptionApplication", by_owner: bool, at: datetime
    ) -> None:
        if by_owner:
            if app.owner_confirmed_at is not None:
                raise InvalidTransition("the owner already confirmed the handover")
            app.owner_confirmed_at = at
        else:
            if app.applicant_confirmed_at is not None:
                raise InvalidTransition("the applicant already confirmed the handover")
            app.applicant_confirmed_at = at
        if (
            app.owner_confirmed_at is not None
            and app.applicant_confirmed_at is not None
        ):
            app._become(
                S.ADOPTED,
                ApplicationAdopted(application_id=app.id, animal_id=app.animal_id),
            )


# The four final states allow nothing: every change is refused by the base class.
class DeclinedState(ApplicationState):
    status = S.DECLINED


class WithdrawnState(ApplicationState):
    status = S.WITHDRAWN


class ClosedState(ApplicationState):
    status = S.CLOSED


class AdoptedState(ApplicationState):
    status = S.ADOPTED


STATES: dict[ApplicationStatus, ApplicationState] = {
    state.status: state
    for state in (
        OpenState(),
        AcceptedState(),
        DeclinedState(),
        WithdrawnState(),
        ClosedState(),
        AdoptedState(),
    )
}
