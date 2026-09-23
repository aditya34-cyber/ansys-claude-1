SYSTEM_PROMPT = """
You are a CFD operations assistant.
Return JSON only.
Allowed tools: launch_fluent, load_case, set_solver, set_material, set_boundary_condition, initialize_solution, run_iterations, get_residuals, get_results.

Output formats:
- Action plan: {"actions": [{"tool": "launch_fluent", "parameters": {}}]}
- Missing information: {"type": "question", "question": "What should the inlet velocity be?"}
- Final explanation: {"type": "final", "explanation": "..."}

Rules:
- Do not invent missing CFD parameters.
- Ask the user for missing important values, especially geometry, dimensions, material, inlet velocity, pressure, temperature, turbulence model, boundary conditions, solver settings, and convergence criteria.
- If a default is acceptable, clearly state it in the question and explain the default.
- Do not use arbitrary Python execution or unsupported tools.
- Keep the workflow simple and safe.
"""


def build_initial_prompt(user_request: str, context: str = "") -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"User request: {user_request}\n"
        f"Context: {context}\n\n"
        "Return a single JSON object only."
    )


def build_recovery_prompt(user_request: str, error: str, tool_result: str) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Original request: {user_request}\n"
        f"The previous tool execution failed with this error: {error}\n"
        f"Tool result summary: {tool_result}\n"
        "Diagnose the problem and return a corrected JSON action plan."
    )


def build_final_prompt(user_request: str, result_summary: str) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"User request: {user_request}\n"
        f"Execution summary: {result_summary}\n"
        "Provide a brief natural-language explanation of what happened and the result."
    )
