import uuid
from datetime import datetime
from typing import Optional, Dict

from azure.core.credentials import AzureNamedKeyCredential
from azure.data.tables import TableServiceClient, TableClient, UpdateMode


class JobsTable:
    __jobs_table_name: str = "statetrackerfunctionsjobruns"

    _service: TableServiceClient
    _table_client: TableClient
    _partition_key: str

    def __init__(self, storage_account_name: str, key: str, partition_key: str):
        uri = f"https://{storage_account_name}.table.core.windows.net"
        credential = AzureNamedKeyCredential(storage_account_name, key)
        self._service = TableServiceClient(endpoint=uri, credential=credential)
        self._table_client = self._service.get_table_client(table_name=self.__jobs_table_name)
        self._partition_key = partition_key

    def get(self, partition_key: str, row_key: str) -> Optional[Dict]:
        return self._table_client.get_entity(partition_key=partition_key, row_key=row_key) or {}

    def get_last_run(self) -> Optional[Dict]:
        return self.get(self._partition_key, "last")

    def update_last_run(self, **updates):
        last_run = self.get_last_run()
        if last_run is not None:
            self.create(last_run, row_key=str(uuid.uuid4()))
        else:
            last_run = {
                "PartitionKey": self._partition_key,
                "RowKey": "last",
                "run_datetime": datetime.now()
            }

        if len(updates) > 0:
            last_run.update(updates)
        self.replace(last_run)

    def query(self, partition_key: str, row_key: Optional[str] = None, **filters) -> Dict:
        row_key_eq = f"RowKey eq '{row_key}'" if row_key is not None else ""
        filters_query = ' and '.join([f"{k} eq '{v}'" for k, v in filters.items()])
        return self._table_client.query_entities(
            f"PartitionKey eq '{partition_key}' {(' and ' + row_key_eq) if len(row_key_eq) > 0 else ''}{filters_query}")

    @staticmethod
    def _fill_with_keys(entity: Dict, partition_key: Optional[str] = None, row_key: Optional[str] = None) -> Dict:
        entity_cpy = entity.copy()
        if "PartitionKey" in entity or "RowKey" in entity:
            if partition_key is not None:
                entity_cpy["PartitionKey"] = partition_key
            if row_key is not None:
                entity_cpy["RowKey"] = row_key
        elif partition_key is None or row_key is None:
            raise ValueError(
                "Your entity does not contain any key. partition_key or row_key"
                " must be provided (inside the entity or within the parameters)")
        return entity_cpy

    def create(self, entity: Dict, partition_key: Optional[str] = None, row_key: Optional[str] = None) -> Dict:
        return self._table_client.create_entity(self._fill_with_keys(entity, partition_key, row_key))

    def replace(self, entity: Dict, partition_key: Optional[str] = None, row_key: Optional[str] = None) -> Dict:
        return self._table_client.upsert_entity(mode=UpdateMode.REPLACE,
                                                entity=self._fill_with_keys(entity, partition_key, row_key))
