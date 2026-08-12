import unittest

from bat_space_modeler.mobile_agent import SimMobileAgentClient, select_mobile_agent


class BsmScaffoldTest(unittest.TestCase):
    def test_selects_generic_sim_mobile_agent(self) -> None:
        client = select_mobile_agent("sim")
        self.assertIsInstance(client, SimMobileAgentClient)
        self.assertIn("command.safe_hold", client.capabilities())

    def test_rejects_non_simulation_agent_in_phase_zero(self) -> None:
        with self.assertRaisesRegex(ValueError, "only the generic simulation"):
            select_mobile_agent("r2")


if __name__ == "__main__":
    unittest.main()
