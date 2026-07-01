from abc import ABC, abstractmethod

from models.difference_group import DifferenceGroup
from models.logical_aligned_pair import LogicalAlignedPair


class Comparator(ABC):
    """
    Base interface implemented by every comparator.

    Each comparator receives one aligned pair and returns
    zero or more logical DifferenceGroups.
    """

    @abstractmethod
    def compare(
        self,
        pair: LogicalAlignedPair,
    ) -> list[DifferenceGroup]:
        """
        Compare one aligned pair.

        Returns
        -------
        list[DifferenceGroup]
            Zero or more logical groups describing the
            differences found in this aligned pair.
        """
        raise NotImplementedError