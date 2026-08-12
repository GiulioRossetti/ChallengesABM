import unittest

from challengeabm.metrics import count_states
from challengeabm.states import State


class MetricTests(unittest.TestCase):
    def test_count_states(self) -> None:
        counts = count_states([State.UNAWARE, State.UNAWARE, State.OBSERVING])
        self.assertEqual(counts["U"], 2)
        self.assertEqual(counts["O"], 1)


if __name__ == "__main__":
    unittest.main()

