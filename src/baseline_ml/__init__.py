from .generator import ComputablePasswordGenerator

def __getattr__(name):
    if name == "Models":
        from .models import Models
        return Models
    elif name in ("Utils", "LossHistory"):
        import importlib
        utils_module = importlib.import_module(".utils", __package__)
        return getattr(utils_module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")
