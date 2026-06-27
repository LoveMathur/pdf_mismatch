from abc import ABC, abstractmethod

from models.aligned_pair import AlignedPair
from models.difference import Difference


class BaseAnalyzer(ABC):

    @abstractmethod
    def analyze(
        self,
        pair: AlignedPair
    ) -> list[Difference]:
        ... 