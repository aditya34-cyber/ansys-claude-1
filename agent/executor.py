from __future__ import annotations

from typing import Any

from .fluent import FluentSessionManager

ALLOWED_TOOLS = {
    "launch_fluent",
    "load_case",
    "set_solver",
    "set_material",
    "set_boundary_condition",
    "initialize_solution",
    "run_iterations",
    "get_residuals",
    "get_results",
}

REQUIRED_PARAMETERS = {
    "launch_fluent": [],
    "load_case": ["case_file"],
    "set_solver": ["solver"],
    "set_material": ["material"],
    "set_boundary_condition": ["zone", "value"],
    "initialize_solution": [],
    "run_iterations": ["iterations"],
    "get_residuals": [],
    "get_results": [],
}


class ToolExecutor:
    def __init__(self, fluent_manager: FluentSessionManager) -> None:
        self.fluent_manager = fluent_manager

    def _validate_action(self, action: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        if not isinstance(action, dict):
            raise ValueError("Each action must be a dictionary.")

        tool = str(action.get("tool", "")).strip()
        if not tool:
            raise ValueError("Each action must include a 'tool' name.")
        if tool not in ALLOWED_TOOLS:
            raise ValueError(f"Tool '{tool}' is not in the allowed tool list.")

        parameters = action.get("parameters", {})
        if not isinstance(parameters, dict):
            raise ValueError(f"Action '{tool}' must include a parameter dictionary.")

        missing = [name for name in REQUIRED_PARAMETERS.get(tool, []) if name not in parameters]
        if missing:
            raise ValueError(f"Action '{tool}' is missing required parameters: {', '.join(missing)}")

        return tool, parameters

    def _execute_tool(self, tool: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if tool == "launch_fluent":
            self.fluent_manager.start()
            return {"status": "Fluent launched"}
        if tool == "load_case":
            return self.fluent_manager.load_case(str(parameters["case_file"]))
        if tool == "set_solver":
            return self.fluent_manager.set_solver(str(parameters["solver"]))
        if tool == "set_material":
            material = parameters.get("material")
            zone = parameters.get("zone")
            return self.fluent_manager.set_material(str(material), zone=str(zone) if zone else None)
        if tool == "set_boundary_condition":
            return self.fluent_manager.set_boundary_condition(str(parameters["zone"]), str(parameters["value"]))
        if tool == "initialize_solution":
            return self.fluent_manager.initialize_solution()
        if tool == "run_iterations":
            return self.fluent_manager.run_iterations(int(parameters["iterations"]))
        if tool == "get_residuals":
            return self.fluent_manager.get_residuals()
        if tool == "get_results":
            return self.fluent_manager.get_results()
        raise ValueError(f"Tool '{tool}' is not supported by the executor.")

    def execute(self, actions: list[dict[str, Any]]) -> dict[str, Any]:
        if not isinstance(actions, list):
            return {"success": False, "error": "Claude returned an invalid action payload."}

        results: list[dict[str, Any]] = []
        for action in actions:
            try:
                tool, parameters = self._validate_action(action)
                print(f"[TOOL] {tool}")
                result = self._execute_tool(tool, parameters)
                results.append({"success": True, "tool": tool, "result": result})
            except Exception as exc:  # noqa: BLE001 - we want to capture execution errors and return them to Claude.
                tool_name = str(action.get("tool", "unknown")) if isinstance(action, dict) else "unknown"
                err = str(exc)
                print(f"[ERROR] {tool_name}: {err}")
                results.append({"success": False, "tool": tool_name, "error": err})

        all_success = all(item.get("success") for item in results)
        return {
            "success": all_success,
            "results": results,
            "error": None if all_success else "One or more tool actions failed.",
        }
