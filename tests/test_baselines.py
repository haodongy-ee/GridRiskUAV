import unittest

from gridriskuav.baselines import ALGORITHMS, optimal_dp
from gridriskuav.models import Scenario, Task
from gridriskuav.scenarios import generate_scenario, reference_scenario


class BaselineTests(unittest.TestCase):
    def test_all_algorithms_return_feasible_unique_routes(self):
        scenario = reference_scenario()
        for algorithm in ALGORITHMS.values():
            result = algorithm(scenario)
            self.assertEqual(result.status, "ok")
            self.assertLessEqual(result.route_cost, scenario.budget + 1e-9)
            self.assertEqual(len(result.route), len(set(result.route)))

    def test_optimal_dominates_greedy_objectives(self):
        scenario = generate_scenario(10, "bimodal", 42)
        optimum = optimal_dp(scenario)
        for name, algorithm in ALGORITHMS.items():
            if name != "optimal_dp":
                self.assertGreaterEqual(optimum.objective + 1e-9, algorithm(scenario).objective)

    def test_size_limit_is_explicit(self):
        scenario = generate_scenario(19, "uniform", 7)
        result = optimal_dp(scenario)
        self.assertEqual(result.status, "skipped_size_limit")

    def test_empty_scenario(self):
        scenario = Scenario("empty", (), budget=0)
        for algorithm in ALGORITHMS.values():
            result = algorithm(scenario)
            self.assertEqual(result.route, ())
            self.assertEqual(result.task_coverage, 1.0)


if __name__ == "__main__":
    unittest.main()
