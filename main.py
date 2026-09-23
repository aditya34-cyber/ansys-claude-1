import json
import os

from dotenv import load_dotenv

from agent.claude import ClaudeClient
from agent.executor import ToolExecutor
from agent.fluent import FluentSessionManager

MAX_RETRIES = 2


def connectivity_test(manager: FluentSessionManager | None = None) -> bool:
    runtime_manager = manager or FluentSessionManager()
    try:
        runtime_manager.start()
        print("Fluent connection successful.")
        runtime_manager.close()
        return True
    except Exception as exc:  # noqa: BLE001 - the app must report, not swallow, the real failure.
        print(f"[ERROR] Fluent connection failed: {exc}")
        print("Check the Ansys Fluent installation and the PyFluent launcher configuration.")
        print("The app will continue in prompt mode so you can still interact with Claude.")
        return False


def main() -> None:
    load_dotenv()
    print("## CFD Agent")

    if os.getenv("FLUENT_DISABLE_AUTO_CHECK", "true").lower() not in {"1", "true", "yes", "on"}:
        fluent_manager = FluentSessionManager()
        if not connectivity_test(fluent_manager):
            print("[WARN] Continuing without a Fluent session. Install Fluent or set FLUENT_DISABLE_AUTO_CHECK=true to skip the startup check.")
        else:
            fluent_manager.close()
    else:
        print("[WARN] Fluent auto-check is disabled. Starting in prompt mode.")

    try:
        claude = ClaudeClient()
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        print("Add your Anthropic API key to the .env file and restart the app.")
        return

    fluent_manager = FluentSessionManager()
    executor = ToolExecutor(fluent_manager)
    user_request = input("\nEnter a CFD request:\n> ").strip()
    if not user_request:
        print("[ERROR] No CFD request was provided.")
        return

    last_error = ""
    last_summary = ""

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"[USER] {user_request}")
        try:
            if attempt == 1:
                print("[CLAUDE] Planning simulation...")
                plan = claude.get_actions(user_request)
            else:
                print("[CLAUDE] Recovering from the previous execution error...")
                plan = claude.recover(user_request, last_error, last_summary)
        except Exception as exc:
            print(f"[ERROR] Claude request failed: {exc}")
            print("[INFO] Stopping early to avoid wasting the Anthropic API budget on repeated invalid responses.")
            break

        if isinstance(plan, dict) and plan.get("type") == "question":
            question = str(plan.get("question", "Please provide the missing parameter."))
            print(f"[CLAUDE] {question}")
            answer = input("Your answer: ").strip()
            user_request = f"{user_request}\nUser clarification: {question} -> {answer}"
            continue

        if not isinstance(plan, dict) or not isinstance(plan.get("actions"), list):
            print("[ERROR] Claude returned an invalid action list.")
            break

        print(f"[CLAUDE] Action plan: {json.dumps(plan, indent=2)}")
        result = executor.execute(plan["actions"])
        last_summary = json.dumps(result, indent=2)

        if result.get("success"):
            print(f"[RESULT] {last_summary}")
            final_explanation = claude.explain_results(user_request, last_summary)
            print(f"[CLAUDE] {final_explanation}")
            return

        last_error = str(result.get("error", "Unknown execution error."))
        print(f"[ERROR] {last_error}")

    print("[ERROR] Maximum retry limit reached. The task did not complete successfully.")


if __name__ == "__main__":
    main()
