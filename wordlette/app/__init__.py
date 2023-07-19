from wordlette.app.app import WordletteApp


def app(*args, **kwargs) -> WordletteApp:
    from wordlette.state_machines import StateMachine
    from wordlette.app.states import (
        BootstrappingApp,
        CreatingConfig,
        ConnectingDB,
        LoadCoreExtensions,
        ServingApp,
    )

    return WordletteApp(
        StateMachine(
            BootstrappingApp.goes_to(LoadCoreExtensions),
            LoadCoreExtensions.goes_to(
                CreatingConfig, when=CreatingConfig.no_config_found
            ),
            LoadCoreExtensions.goes_to(
                ConnectingDB, when=ConnectingDB.has_database_config
            ),
            CreatingConfig.goes_to(ConnectingDB),
            ConnectingDB.goes_to(ServingApp),
        )
    )
