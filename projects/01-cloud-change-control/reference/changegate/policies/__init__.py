"""Modular security policies. See base.py for the Policy interface.

Add your own policies in a separate module, decorate them with @register, and list the module in
changegate.toml under [policies] extra_modules = ["my_company.policies"].
"""

from .base import Policy, PolicyLoadError, load_policies, register, registered, run_policies

__all__ = ["Policy", "PolicyLoadError", "load_policies", "register", "registered", "run_policies"]
