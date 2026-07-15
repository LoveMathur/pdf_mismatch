from abc import ABC, abstractmethod

from models.difference import Difference
from models.logical_aligned_pair import LogicalAlignedPair


class Comparator(ABC):
    """
    Base class for all comparison modules.
    """

    @abstractmethod
    def compare(
        self,
        pair: LogicalAlignedPair,
    ) -> list[Difference]:
        """
        Compare one aligned pair and return the detected differences.
        """
        raise NotImplementedError