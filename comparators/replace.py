from comparators.base import BaseComparator

from comparators.analyzers.character_difference import CharacterDifferenceAnalyzer
from comparators.analyzers.word import WordAnalyzer
from comparators.analyzers.case import CaseAnalyzer
from comparators.analyzers.number import NumberAnalyzer
from comparators.analyzers.whitespace import WhitespaceAnalyzer
from comparators.analyzers.spelling import SpellingAnalyzer

from models.aligned_pair import AlignmentType, AlignedPair
from models.difference import Difference


class ReplaceComparator(BaseComparator):

    def __init__(self):

        self.analyzers = [

            CaseAnalyzer(),
            NumberAnalyzer(),
            WhitespaceAnalyzer(),
            CharacterDifferenceAnalyzer(),
            SpellingAnalyzer(),
            WordAnalyzer(),
            
        ]

    def compare(
        self,
        pairs: list[AlignedPair]
    ) -> list[Difference]:

        differences = []

        for pair in pairs:

            if pair.alignment_type != AlignmentType.REPLACE:
                continue

            for analyzer in self.analyzers:

                result = analyzer.analyze(pair)

                if result:

                    differences.extend(result)

                    break

        return differences