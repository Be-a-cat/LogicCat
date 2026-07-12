NODE_REGISTRY = {}
NODE_RUNNING_RECORD = {}
PLUGIN_CONFIGS = {}


def registry_node(title, category="未分类", visible=True):
    def decorator(cls):
        class_name = cls.__name__

        NODE_REGISTRY[class_name] = {
            "class": cls,
            "title": title,
            "category": category,
            "visible": visible
        }
        return cls
    return decorator


def register_plugin_config(name, title=None):
    def decorator(cls):
        PLUGIN_CONFIGS[name] = {
            "class": cls,
            "title": title or name
        }
        return cls
    return decorator
