from enum import Enum


class SetupStatus(str, Enum):
    Ready = "ready"
    Waiting = "waiting"
    Complete = "complete"


class SetupCategory(str, Enum):
    NoCategory = "no_category"
    Config = "setup_config"
    Database = "setup_database"
    Admin = "setup_admin"
    General = "setup_general"
