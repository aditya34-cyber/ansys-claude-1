from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import ansys.fluent.core as pyfluent


@dataclass
class FluentConfig:
    precision: str = os.getenv("FLUENT_PRECISION", "double")
    processor_count: int = int(os.getenv("FLUENT_PROCESSOR_COUNT", "1"))
    ui_mode: str = os.getenv("FLUENT_UI_MODE", "no_gui")
    mode: str = os.getenv("FLUENT_MODE", "solver")
    start_timeout: int = int(os.getenv("FLUENT_START_TIMEOUT", "120"))


class FluentSessionManager:
    def __init__(self, config: FluentConfig | None = None) -> None:
        self.config = config or FluentConfig()
        self.session: Any | None = None

    def start(self) -> Any:
        if self.session is not None:
            print("[FLUENT] Reusing existing Fluent session.")
            return self.session

        print("[TOOL] launch_fluent")
        print(
            f"[FLUENT] Starting Fluent with precision={self.config.precision}, "
            f"processor_count={self.config.processor_count}, ui_mode={self.config.ui_mode}."
        )
        self.session = pyfluent.launch_fluent(
            precision=self.config.precision,
            processor_count=self.config.processor_count,
            ui_mode=self.config.ui_mode,
            mode=self.config.mode,
            start_timeout=self.config.start_timeout,
        )
        print("[FLUENT] Fluent session started.")
        return self.session

    def close(self) -> None:
        if self.session is not None:
            try:
                self.session.exit()
            except Exception:  # pragma: no cover
                pass
            self.session = None
            print("[FLUENT] Fluent session closed.")

    def _require_session(self) -> Any:
        if self.session is None:
            raise RuntimeError("Fluent session is not active. Launch it before sending tool actions.")
        return self.session

    def load_case(self, case_file: str) -> dict[str, Any]:
        session = self._require_session()
        if hasattr(session, "read_case_lightweight"):
            session.read_case_lightweight(case_file)
            return {"status": "Case loaded", "case_file": case_file}
        if hasattr(session, "execute_tui"):
            session.execute_tui(f"file/read-case {case_file}")
            return {"status": "Case loaded via TUI", "case_file": case_file}
        raise RuntimeError("This PyFluent build does not expose a supported case-load method.")

    def set_solver(self, solver: str) -> dict[str, Any]:
        session = self._require_session()
        lookup = {
            "pressure_based": "solve/set/pressure-based yes",
            "pressure-based": "solve/set/pressure-based yes",
            "density_based": "solve/set/density-based yes",
            "density-based": "solve/set/density-based yes",
        }
        command = lookup.get(str(solver).lower())
        if command and hasattr(session, "execute_tui"):
            session.execute_tui(command)
            return {"status": "Solver set", "solver": solver}
        raise RuntimeError(f"Solver '{solver}' is not supported by the minimal Fluent workflow.")

    def set_material(self, material: str, zone: str | None = None) -> dict[str, Any]:
        session = self._require_session()
        if hasattr(session, "execute_tui"):
            session.execute_tui(f"material/change-create {material} {material} y")
            return {"status": "Material configured", "material": material, "zone": zone}
        raise RuntimeError("Material configuration is not exposed in this minimal PyFluent build.")

    def set_boundary_condition(self, zone: str, value: str) -> dict[str, Any]:
        session = self._require_session()
        if hasattr(session, "execute_tui"):
            session.execute_tui(f"boundary-conditions/set {zone} {value}")
            return {"status": "Boundary condition set", "zone": zone, "value": value}
        raise RuntimeError("Boundary condition control is not exposed in this minimal PyFluent build.")

    def initialize_solution(self) -> dict[str, Any]:
        session = self._require_session()
        if hasattr(session, "execute_tui"):
            session.execute_tui("solve/initialize/initialize-flow")
            return {"status": "Solution initialized"}
        raise RuntimeError("Solution initialization is not exposed in this minimal PyFluent build.")

    def run_iterations(self, iterations: int) -> dict[str, Any]:
        session = self._require_session()
        if hasattr(session, "execute_tui"):
            session.execute_tui(f"solve/iterate {int(iterations)}")
            return {"status": "Iterations completed", "iterations": int(iterations)}
        raise RuntimeError("Iteration control is not exposed in this minimal PyFluent build.")

    def get_residuals(self) -> dict[str, Any]:
        session = self._require_session()
        if hasattr(session, "execute_tui"):
            session.execute_tui("solve/report/residuals")
            return {"status": "Residuals requested"}
        raise RuntimeError("Residual reporting is not exposed in this minimal PyFluent build.")

    def get_results(self) -> dict[str, Any]:
        session = self._require_session()
        if hasattr(session, "execute_tui"):
            session.execute_tui("report/summary")
            return {"status": "Result summary requested"}
        raise RuntimeError("Result reporting is not exposed in this minimal PyFluent build.")
