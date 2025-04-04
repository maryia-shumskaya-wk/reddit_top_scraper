from __future__ import annotations

import io
import logging

import yaml
from frozendict import frozendict

_LOGGER = logging.getLogger(__name__)
CONFIG_FILE_NAME = './config.yml'


def get_config() -> frozendict:
    try:
        with io.open(CONFIG_FILE_NAME, 'r', encoding='utf-8') as file:
            return frozendict(yaml.full_load(file))
    except FileNotFoundError:
        _LOGGER.error('Config file not found')
        return frozendict()
