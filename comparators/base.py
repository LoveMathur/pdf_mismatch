from abc import ABC, abstractmethod

from models.aligned_pair import AlignedPair
from models.difference import Difference


class BaseComparator(ABC):

    @abstractmethod
    def compare(
        self,
        pairs: list[AlignedPair]
    ) -> list[Difference]:
        ...