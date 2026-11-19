class AlreadySwiped(Exception):
    """The user has already made a decision about this animal."""


class SwipeAnimalNotAvailable(Exception):
    """The animal is no longer available for swiping."""


class SwipeOwnAnimal(Exception):
    """The owner cannot swipe on their own animal."""


class SwipeProfileRequired(Exception):
    """The user must save a Matchmaker profile before swiping."""
