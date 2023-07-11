from wordlette.app.app import WordletteApp


def app(*args, **kwargs) -> WordletteApp:
    from wordlette.state_machines import StateMachine
    from wordlette.app.states import (
        BootstrappingApp,
        CreatingConfig,
        ConnectingDB,
        StateServingApp,
    )

    return WordletteApp(
        StateMachine(
            BootstrappingApp.goes_to(
                CreatingConfig, when=BootstrappingApp.no_config_found
            ),
            BootstrappingApp.goes_to(
                ConnectingDB, when=BootstrappingApp.has_database_config
            ),
            CreatingConfig.goes_to(ConnectingDB),
            ConnectingDB.goes_to(StateServingApp),
        )
    )
