# Fluent AI Agent

This project is a minimal Python application that connects an Anthropic Claude model to Ansys Fluent through PyFluent. The goal is to demonstrate the control flow:

Python -> Claude -> Python action validation -> PyFluent -> Fluent -> results -> Claude -> explanation

The first MVP is intentionally small and safe. It is designed to validate the tool chain, not to build a production CFD workflow.

## Python version

Use Python 3.10 or newer.

## Virtual environment setup

From the project root:

```powershell
cd "C:\Users\santh\OneDrive\Desktop\fluent-ai-agent"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## PyFluent installation

PyFluent is installed in the project virtual environment via:

```powershell
python -m pip install ansys-fluent-core
```

This project expects the current installed `ansys.fluent.core` API. The launcher used in the code is:

```python
import ansys.fluent.core as pyfluent
pyfluent.launch_fluent(...)
```

The method signature and configuration names were verified against the installed package version before implementation.

## Anthropic SDK installation

The official Anthropic SDK is installed via:

```powershell
python -m pip install anthropic
```

## .env setup

Create a `.env` file in the project root with your key:

```text
ANTHROPIC_API_KEY=your_actual_api_key_here
```

The application reads this value without hardcoding it.

## How to launch the program

From the project root, with the virtual environment active:

```powershell
python main.py
```

You will be prompted for a CFD request, for example:

```text
Create a basic airflow simulation around a cylinder.
```

## How PyFluent finds the Ansys installation

PyFluent looks for a local Fluent installation using the standard Ansys install layout. On Windows this is usually under a path such as:

```text
C:\Program Files\ANSYS\...
```

If the path is not visible to PyFluent, the launch will fail with a clear error. Ensure the Fluent product is installed and accessible, and that the environment has permissions to start the solver.

## Troubleshooting Fluent connection problems

If the connection fails, check the following:

- Fluent is installed and the local machine has a valid license.
- The machine can start the Fluent executable.
- `pyfluent.launch_fluent` can find the Ansys installation.
- GUI or headless mode settings are valid for the local environment.
- The project uses the correct `.venv` interpreter.

The app is intentionally explicit about these failures instead of hiding them.

## Fluent configuration variables

The Fluent launcher settings are driven by environment variables so they can be changed without editing the code:

```text
FLUENT_PRECISION=double
FLUENT_PROCESSOR_COUNT=1
FLUENT_UI_MODE=no_gui
FLUENT_MODE=solver
FLUENT_START_TIMEOUT=120
```

These values are read from the `.env` file and applied by `agent/fluent.py`.

## Architecture summary

- `main.py` runs the CLI loop and the connectivity check.
- `agent/claude.py` sends requests to the Anthropic API.
- `agent/fluent.py` isolates the PyFluent connection and launch settings.
- `agent/executor.py` validates the allowed tools and executes the action set.
- `agent/prompts.py` controls the safety instructions sent to Claude.

## Minimal next iteration

This repository implements the control loop, validation layer, and a guarded Fluent launcher. The next iteration should replace the placeholder fluent commands with case-specific TUI or data-model operations for a real small CFD test case, such as a simple cylinder or channel flow.
