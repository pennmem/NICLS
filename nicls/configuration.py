import configparser
import json
import pathlib
from typing import Union, Any


def load_configuration(path: Union[pathlib.Path, str]):
    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path).absolute()

    if not path.exists():
        raise Exception("config not found")

    # suffix includes dot
    config_type = path.suffix[1:]
    if config_type == 'json':
        JsonConfig.load(path)
    elif config_type == 'ini':
        IniConfig.load(path)
    else:
        raise Exception("config type not supported.")


class MetaConfig(type):
    def __new__(mcs, *args, **kwargs):
        cls = super().__new__(mcs, *args, **kwargs)
        cls._config = {}
        return cls

    def load(self, config: dict):
        for k, v in config.items():
            if isinstance(v, dict):
                nested = MetaConfig(k, (), {})
                nested.load(v)
                config[k] = nested

        self._config.update(config)

    def __getattr__(cls, name: str):
        # defend against recursion
        if name == '_config':
            raise AttributeError()

        # support only case insensitive access
        name = name.lower()
        if name in cls._config:
            return cls._config[name]

        raise AttributeError()

    def __setattr__(cls, name: str, value: Any):
        if hasattr(cls, "_config") and name in cls._config:
            raise Exception("Config is read only")
        else:
            super().__setattr__(name, value)

    # NOTE: we could expand this to allow iteration over a section of the config


class Config(metaclass=MetaConfig):
    pass

class JsonConfig(Config):
    @staticmethod
    def load(path: pathlib.Path):
        with open(path, 'r') as f:
            config = json.load(f)
        Config.load(config)


class IniConfig(Config):
    @staticmethod
    def load(path: pathlib.Path):
        config = configparser.parse(path)
        Config.load(config)
