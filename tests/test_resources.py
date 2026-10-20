import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from gridriskuav.baselines import ALGORITHMS, local_search
from gridriskuav.models import HazardZone, Scenario, Task
from gridriskuav.scenarios import generate_scenario


class ResourceTests(unittest.TestCase):
    def test_hazard_exposure_uses_segment_intersection_length(self):
        scenario = Scenario("edge", (Task(1, 4, 0, 1, 1),), budget=20,
                            hazard_zones=(HazardZone(2, 0, 1, 2),))
        self.assertAlmostEqual(scenario.route_exposure([1]), 8.0)

    def test_battery_reserve_and_weather(self):
        scenario = Scenario("battery", (Task(1, 3, 4, 1, 1),), budget=13,
                            weather_travel_factor=1.2, battery_capacity=12,
                            battery_reserve=2, battery_per_distance=1)
        self.assertEqual(scenario.route_distance([1]), 10)
        self.assertEqual(scenario.route_cost([1]), 13)
        self.assertTrue(scenario.is_feasible([1]))
        self.assertFalse(replace(scenario, battery_reserve=3).is_feasible([1]))

    def test_all_constructive_and_local_search_routes_respect_resources(self):
        base = generate_scenario(20, "hotspot", 23)
        scenario = replace(base, max_flight_distance=24, battery_capacity=28,
                           battery_reserve=4, max_flight_exposure=4,
                           hazard_zones=(HazardZone(3, 3, 2, 1),))
        for name, algorithm in ALGORITHMS.items():
            result = algorithm(scenario)
            if name == "optimal_dp":
                self.assertEqual(result.status, "skipped_resource_constraints")
            else:
                self.assertTrue(scenario.is_feasible(result.route), name)

    def test_local_search_at_least_matches_starts(self):
        scenario = generate_scenario(25, "bimodal", 61)
        result = local_search(scenario)
        for name in ("nearest", "reward_per_cost", "risk_aware_greedy"):
            self.assertGreaterEqual(result.objective + 1e-9, ALGORITHMS[name](scenario).objective)

    def test_scenario_json_round_trip(self):
        scenario = generate_scenario(5, "uniform", 3)
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
            path = Path(temp) / "scenario.json"
            scenario.to_json(path)
            self.assertEqual(Scenario.from_json(path), scenario)


if __name__ == "__main__":
    unittest.main()
