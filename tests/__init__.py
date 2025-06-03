import sys
from pathlib import Path
from types import SimpleNamespace

# Ensure src directory is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

# Provide minimal stub modules for dependencies not installed in the test env
sys.modules.setdefault('pytz', SimpleNamespace(timezone=lambda tz: None,
                                              utc=SimpleNamespace(localize=lambda dt: dt)))
sys.modules.setdefault('dotenv', SimpleNamespace(load_dotenv=lambda *args, **kwargs: None))
