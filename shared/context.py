from dependency_injector import containers, providers

from .env import Environment
from .components import Cosmos, JobsTable, Database


class Gateways(containers.DeclarativeContainer):
    config = providers.Configuration()

    cosmos_client = providers.Singleton(
        Cosmos,
        connection_string=config.azure.cosmos_connection_string
    )

    jobs_table = providers.Singleton(
        JobsTable,
        storage_account_name=config.azure.storage_account_name,
        key=config.azure.storage_account_key,
        table_name=config.azure.jobs_table_name
    )


class Application(containers.DeclarativeContainer):
    config = providers.Configuration()

    gateways = providers.Container(Gateways, config=config.gateways)


application = Application()
application.config.gateways.azure.cosmos_connection_string.from_env("COSMOS_ACCOUNT_CONNECTION_STRING", required=True)
application.config.gateways.azure.storage_account_name.from_env("STORAGE_ACCOUNT_NAME", required=True)
application.config.gateways.azure.storage_account_key.from_env("STORAGE_ACCOUNT_KEY", required=True)
application.config.gateways.azure.jobs_table_name.from_env("JOBS_TABLE_NAME", required=True)
application.wire(modules=["shared.functions.amendments.function", "shared.functions.deputies.function"])

Database.init_with_credentials(Environment.sql_engine, Environment.sql_user, Environment.sql_password, Environment.sql_host,
                               Environment.sql_port, Environment.sql_database)
