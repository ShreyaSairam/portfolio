"""
Helper to load each project's standalone app.py as a page inside the hub
dashboard, without renaming or restructuring the individual projects
(each one also runs perfectly well on its own with `streamlit run app.py`
inside its own folder).

Each project directory is added to sys.path once (so a project's app.py
can keep doing its normal `from engine import ...` / `from recognizer
import ...` style imports), then its app.py is loaded under a unique
module name and its main() function is called to render the page.
"""

import importlib.util
import os
import sys

PORTFOLIO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_DIRS = {
    "football_dashboard": os.path.join(PORTFOLIO_ROOT, "football_dashboard"),
    "signspeak": os.path.join(PORTFOLIO_ROOT, "signspeak"),
    "wanderwise": os.path.join(PORTFOLIO_ROOT, "wanderwise"),
    "attendance_system": os.path.join(PORTFOLIO_ROOT, "attendance_system"),
    "genomics_dsst": os.path.join(PORTFOLIO_ROOT, "genomics_dsst"),
}


def _ensure_on_path(project_dir):
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)


def run_project(project_key):
    """Loads <project_dir>/app.py under a unique module name and calls main()."""
    project_dir = PROJECT_DIRS[project_key]
    _ensure_on_path(project_dir)

    module_name = f"_hub_{project_key}_app"
    app_path = os.path.join(project_dir, "app.py")

    module = sys.modules.get(module_name)
    if module is None:
        spec = importlib.util.spec_from_file_location(module_name, app_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        # module's own os.path.dirname(__file__) calls need __file__ set
        # correctly, which spec_from_file_location already does
        spec.loader.exec_module(module)

    module.main()
