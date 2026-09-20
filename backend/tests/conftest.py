import importlib.util
import os
import sys

os.environ.setdefault("UPLOADS_BUCKET", "test-bucket")
os.environ.setdefault("GROQ_API_KEY", "gsk_test_key")
os.environ.setdefault("GROQ_MODEL_ID", "openai/gpt-oss-120b")
os.environ.setdefault("RESULTS_TABLE", "test-table")
os.environ.setdefault("STATE_MACHINE_ARN", "arn:aws:states:us-east-1:123456789012:stateMachine:test")

_FUNCTIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "functions")


def load_function_module(function_name: str, filename: str = "app.py"):
    """Loads a Lambda function's module (app.py, or another file in the
    same function directory) in isolation.

    Every function directory is self-contained and has its own copy of
    shared helper files (clients.py, models.py, and some have their own
    prompts.py). Because more than one of those files share the same
    bare module name across function directories (two different
    "prompts" modules, for instance), naively sys.path-inserting each
    function directory and importing by bare name causes Python to
    silently reuse whichever module of that name it already cached —
    pulling in the wrong function's prompts/clients/models. This purges
    those bare names from sys.modules first and inserts only this one
    function's directory at the front of sys.path, so each test file
    always loads the correct, matching set of files for the function
    it's actually testing.
    """
    function_dir = os.path.join(_FUNCTIONS_DIR, function_name)

    for stale in ("app", "prompts", "clients", "models"):
        sys.modules.pop(stale, None)

    if function_dir in sys.path:
        sys.path.remove(function_dir)
    sys.path.insert(0, function_dir)

    module_name = f"{function_name}_{filename.replace('.py', '')}"
    spec = importlib.util.spec_from_file_location(module_name, os.path.join(function_dir, filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
