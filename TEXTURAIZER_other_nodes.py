from .any_type import any

import re
from typing import Any, Dict, Tuple, cast

class Texturaizer_SwitchAny:
    """
    Node that switches between two inputs based on a boolean condition.
    Returns 'on_true' if boolean is True, otherwise returns 'on_false'.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "on_true": (any, {}),
                "on_false": (any, {}),
                "boolean": ("BOOLEAN", {"default": True}),
            }
        }

    CATEGORY = "Texturaizer"
    RETURN_TYPES = (any,)
    FUNCTION = "execute"

    def execute(self, on_true, on_false, boolean=True):
        """
        Executes the switch logic based on the boolean value.
        Returns 'on_true' if True, 'on_false' otherwise.
        """
        return (on_true,) if boolean else (on_false,)

class Texturaizer_SwitchLazy:
    """
    Node that switches between up to 10 inputs based on an index.
    Only the selected input is evaluated (lazy).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "index": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 10,
                        "tooltip": "Select which input to output (1-10).",
                    },
                ),
            },
            "optional": {
                "input1": (any, {"lazy": True}),
                "input2": (any, {"lazy": True}),
                "input3": (any, {"lazy": True}),
                "input4": (any, {"lazy": True}),
                "input5": (any, {"lazy": True}),
                "input6": (any, {"lazy": True}),
                "input7": (any, {"lazy": True}),
                "input8": (any, {"lazy": True}),
                "input9": (any, {"lazy": True}),
                "input10": (any, {"lazy": True}),
            },
        }

    CATEGORY = "Texturaizer"
    RETURN_TYPES = (any, "INT")
    RETURN_NAMES = ("selected", "index")
    FUNCTION = "execute"

    # ------------------ LAZY CONTROL ------------------

    def check_lazy_status(self, *args, **kwargs):
        selected_index = int(kwargs["index"])
        return [f"input{selected_index}"]

    # --------------------------------------------------

    @staticmethod
    def execute(*args, **kwargs):
        selected_index = int(kwargs["index"])
        selected_input = f"input{selected_index}"

        if selected_input in kwargs and kwargs[selected_input] is not None:
            return kwargs[selected_input], selected_index

        return None, selected_index

InputSpec = Tuple[object, Dict[str, Any]]

class Texturaizer_SwitchSmart:
    """
    Lazy switch node (like Texturaizer_SwitchLazy), but selects by matching a key against triggers.

    Trigger matching:
      - exact: dog
      - startswith: ^AYS
      - startswith: AYS*
      - regex: re:^GITS\\[coeff=
    Tokens separated by ',' or '|'.
    Blank trigger acts as ELSE (first blank wins).
    """

    @classmethod
    def INPUT_TYPES(cls):
        required = cast(Dict[str, InputSpec], {
            "key": (any, {"tooltip": "Selector (any type). Converted to string and matched against triggers."}),
        })

        optional = cast(Dict[str, InputSpec], {})

        # IMPORTANT: declare ALL possible inputs as lazy on the backend
        for i in range(1, 11):
            optional[f"input{i}"] = (any, {"lazy": True})

        # triggers optional (JS may only provide 1..N)
        for i in range(1, 11):
            optional[f"trigger{i}"] = ("STRING", {
                "default": "",
                "tooltip": "Tokens: exact, ^prefix, prefix*, or re:<regex>. Comma or | separated. Blank = ELSE."
            })

        return {"required": required, "optional": optional}

    CATEGORY = "Texturaizer"
    RETURN_TYPES = (any, "INT")
    RETURN_NAMES = ("selected", "index")
    FUNCTION = "execute"

    def check_lazy_status(self, *args, **kwargs):
        triggers = [kwargs.get(f"trigger{i}", "") for i in range(1, 11)]
        idx = self._resolve_selected_index(kwargs.get("key", None), triggers)
        return [f"input{idx}"]  # only evaluate the selected input

    @staticmethod
    def execute(*args, **kwargs):
        triggers = [kwargs.get(f"trigger{i}", "") for i in range(1, 11)]
        idx = Texturaizer_SwitchSmart._resolve_selected_index(kwargs.get("key", None), triggers)

        name = f"input{idx}"
        if name in kwargs and kwargs[name] is not None:
            return kwargs[name], idx

        return None, idx

    @staticmethod
    def _to_str(v) -> str:
        try:
            return "" if v is None else str(v).strip()
        except Exception:
            return ""

    @staticmethod
    def _split_tokens(s) -> list[str]:
        s = "" if s is None else str(s).strip()
        if not s:
            return []
        return [t.strip() for t in s.replace("|", ",").split(",") if t.strip()]

    @staticmethod
    def _token_matches(key: str, token: str) -> bool:
        if token.startswith("re:"):
            pat = token[3:].strip()
            if not pat:
                return False
            try:
                return re.match(pat, key) is not None
            except re.error:
                return False

        if token.startswith("^"):
            prefix = token[1:]
            return bool(prefix) and key.startswith(prefix)

        if token.endswith("*") and len(token) > 1:
            return key.startswith(token[:-1])

        return key == token

    @classmethod
    def _resolve_selected_index(cls, key, triggers: list[str]) -> int:
        key_norm = cls._to_str(key)

        # 1) explicit matches
        for i, trig in enumerate(triggers, start=1):
            for tok in cls._split_tokens(trig):
                if cls._token_matches(key_norm, tok):
                    return i

        # 2) ELSE: first blank trigger
        for i, trig in enumerate(triggers, start=1):
            if not cls._to_str(trig):
                return i

        return 1

class Texturaizer_Placeholder:
    """
    A placeholder node that optionally prints a message and returns five any-type outputs as None.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "message": ("STRING", {"default": "", "multiline": False, "placeholder": "Enter a message to print..."})
            }
        }

    CATEGORY = "Texturaizer"
    RETURN_TYPES = (any, any, any, any, any)
    RETURN_NAMES = ("output1", "output2", "output3", "output4", "output5")
    FUNCTION = "execute"

    @staticmethod
    def execute(message):
        if message:
            print(message)

        # Return five None values as the outputs
        return None, None, None, None, None

NODE_CLASS_MAPPINGS = {
    "Texturaizer_SwitchAny": Texturaizer_SwitchAny,
    "Texturaizer_SwitchLazy": Texturaizer_SwitchLazy,
    "Texturaizer_SwitchSmart": Texturaizer_SwitchSmart,
    "Texturaizer_Placeholder": Texturaizer_Placeholder,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Texturaizer_SwitchAny": "Switch Any (Texturaizer)",
    "Texturaizer_SwitchLazy": "Switch Lazy (Texturaizer)",
    "Texturaizer_SwitchSmart": "Switch Smart (Texturaizer)",
    "Texturaizer_Placeholder": "Placeholder (Texturaizer)",
}
