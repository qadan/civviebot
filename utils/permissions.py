'''
Standardized sets of permissions.
'''

from discord import Permissions

_BASE_LEVEL_KEYS = ['view_channel', 'use_application_commands']
_MANAGE_LEVEL_KEYS = ['manage_channels', 'manage_permissions'] + _BASE_LEVEL_KEYS
_ADMIN_LEVEL_KEYS = ['create_private_threads', 'manage_messages'] + _MANAGE_LEVEL_KEYS

base_level = Permissions(**dict.fromkeys(_BASE_LEVEL_KEYS, True))
manage_level = Permissions(**dict.fromkeys(_MANAGE_LEVEL_KEYS, True))
admin_level = Permissions(**dict.fromkeys(_ADMIN_LEVEL_KEYS, True))