"""
Outline API wrapper
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx

from .exceptions import (OutlineAccessKeyNotFound, OutlineErrorHostname,
                         OutlineInvalidDataLimit, OutlineInvalidHostname,
                         OutlineInvalidName, OutlineInvalidPort,
                         OutlinePortAlreadyInUse)


@dataclass
class BaseMeta():
    """
    Base class for Outline objects
    """

    def __init__(self, data: dict):
        self.__dict__ = data


class DataTransfered(BaseMeta):
    """
    Base class for Outline data transfered
    """
    bytesTransferredByUserId: dict[str, int] = {}

    @property
    def total(self) -> int:
        """
        Returns the total data transfered
        """
        return sum(self.bytesTransferredByUserId.values())

    def by_key(self, access_key: str | int | OutlineAccessKey) -> int:
        """
        Returns the data transfered by the given access key
        """

        if isinstance(access_key, OutlineAccessKey):
            access_key = access_key.id

        return self.bytesTransferredByUserId.get(str(access_key), 0)


class OutlineAccessKey(BaseMeta):
    """
    Base class for Outline access keys
    """
    id: str
    name: str
    password: str
    port: int
    method: str
    accessUrl: str
    dataLimit: dict = {"bytes": 0}

    def __init__(self, client: OutlineClient, data: dict):
        super().__init__(data)
        self.client = client

    def url(self, name: str = ''):
        """
        Returns the access key URL with the given name

        name (str): The name to use
        """
        if not name:
            return self.accessUrl

        return f"{self.accessUrl}#{name}"

    def delete(self):
        """
        Deletes the access key
        """
        self.client.delete_key(self)

    @property
    def limit(self) -> int:
        """
        Returns the data limit in bytes
        """
        key = self.client.key(self.id)
        return key.dataLimit["bytes"]

    def change_data_limit(self, limit: int):
        """
        Sets a data transfer limit for an access key

        limit (int): The limit in bytes
        """
        self.client.change_data_limit_for_key(self, limit)

    def reset_data_limit(self):
        """
        Removes the access key data limit,
        lifting data transfer restrictions on an access key.
        """
        self.client.reset_data_limit_key(self)

    def rename(self, name: str):
        """
        Renames the access key

        name (str): The new name
        """
        self.client.rename_key(self, name)
        self.name = name

    @property
    def metrics(self) -> int:
        """
        Returns the data transfered by the access key
        """
        return self.client.metrics.by_key(self)


@dataclass
class OutlineClientInfo:
    """
    OutlineClientInfo
    """
    name: str
    server_id: str
    created_at: int
    version: str
    port_for_new_keys: int
    hostname_for_keys: str

    def __init__(self, server_info: dict):
        self.name = server_info.get('name', 'Outline Server')
        self.server_id = server_info.get('serverId', "")
        self.created_at = server_info.get('createdTimestampMs', 0)
        self.version = server_info.get('version', "")
        self.port_for_new_keys = server_info.get('portForNewAccessKeys', 0)
        self.hostname_for_keys = server_info.get('hostnameForAccessKeys', "")


class OutlineClient:
    """
    Base class for Outline servers
    """

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.request = httpx.Client(base_url=base_url, verify=False)

        r = self.request.get("/server")
        self.server = OutlineClientInfo(r.json())

    def rename(self, name: str):
        """
        Changes the name of the server
        """

        r = self.request.put("/name", json={"name": name})
        self.server.name = name

        if r.status_code != 204:
            raise OutlineInvalidName()

    def change_hostname(self, hostname: str):
        """
        Changes the hostname for access keys.
        Must be a valid hostname or IP address.
        If it's a hostname, DNS must be set up independently of this API.

        hostname (str): The hostname or IP address to use
        """

        r = self.request.put("/server/hostname-for-access-keys",
                             json={"hostname": hostname})
        if r.status_code == 400:
            raise OutlineInvalidHostname()
        if r.status_code == 500:
            raise OutlineErrorHostname()

    def change_port(self, port: int):
        """
        Changes the default port for newly created access keys.
        This can be a port already used for access keys.

        port (int): The port to use must be between 1 and 65535
        """

        if 1 > port or port > 65535:
            raise OutlineInvalidPort()

        r = self.request.put("/server/port-for-new-access-keys",
                             json={"port": port})

        if r.status_code == 409:
            raise OutlinePortAlreadyInUse()

    @property
    def is_metrics_shared(self) -> bool:
        """
        Returns whether metrics is being shared
        """

        r = self.request.get("/metrics/enabled")
        r.raise_for_status()
        return r.json()["metricsEnabled"]

    def metrics_shared(self, shared: bool):
        """
        Enables or disables sharing of metrics

        shared (bool): Whether to share metrics
        """

        r = self.request.put("/metrics/enabled",
                             json={"metricsEnabled": shared})
        r.raise_for_status()

    def change_data_limit(self, limit: int):
        """
        Sets a data transfer limit for all access keys

        limit (int): The limit in bytes
        """

        r = self.request.put("/server/access-key-data-limit",
                             json={"limit": {
                                 "bytes": limit
                             }})
        if r.status_code == 400:
            raise OutlineInvalidDataLimit()

    def reset_data_limit(self):
        """
        Removes the access key data limit,
        lifting data transfer restrictions on all access keys.
        """

        r = self.request.delete("/server/access-key-data-limit")
        r.raise_for_status()

    @property
    def keys(self) -> list[OutlineAccessKey]:
        """
        Returns a list of access keys
        """

        r = self.request.get("/access-keys")
        r.raise_for_status()
        return [OutlineAccessKey(self, x) for x in r.json()["accessKeys"]]

    def key(self, access_key: str | int) -> OutlineAccessKey:
        """
        Returns an access key
        """
        access_key = str(access_key)

        keys = self.keys
        for key in keys:
            if key.id == access_key:
                return key
        raise OutlineAccessKeyNotFound()

    def delete_all_keys(self):
        """
        Deletes all access keys
        """

        for key in self.keys:
            key.delete()

    def delete_key(self, access_key: int | str | OutlineAccessKey):
        """
        Deletes an access key
        """

        if isinstance(access_key, OutlineAccessKey):
            access_key = access_key.id

        r = self.request.delete(f"/access-keys/{access_key}")
        r.raise_for_status()

    def rename_key(self, access_key: int | str | OutlineAccessKey, name: str):
        """
        Renames an access key

        access_key (int | str | OutlineAccessKey): The access key to rename
        name (str): The new name
        """

        if isinstance(access_key, OutlineAccessKey):
            access_key = access_key.id

        r = self.request.put(f"/access-keys/{access_key}/name",
                             json={"name": name})
        r.raise_for_status()

    def change_data_limit_for_key(self,
                                  access_key: int | str | OutlineAccessKey,
                                  limit: int):
        """
        Sets a data transfer limit for an access key

        access_key (int | str | OutlineAccessKey): Access key

        limit (int): The limit in bytes
        """

        if isinstance(access_key, OutlineAccessKey):
            access_key = access_key.id

        r = self.request.put(f"/access-keys/{access_key}/data-limit",
                             json={"limit": {
                                 "bytes": limit
                             }})
        if r.status_code == 400:
            raise OutlineInvalidDataLimit()

    def reset_data_limit_key(self, access_key: int | str | OutlineAccessKey):
        """
        Removes the access key data limit,
        lifting data transfer restrictions on an access key.

        access_key (int | str | OutlineAccessKey): Access key
        """

        if isinstance(access_key, OutlineAccessKey):
            access_key = access_key.id

        r = self.request.delete(f"/access-keys/{access_key}/data-limit")
        r.raise_for_status()

    def new(self, method: str = "aes-192-gcm", name: str = ""):
        """
        Creates a new access key

        method (str): The encryption method to use
        name (str): The name of the access key
        """

        r = self.request.post("/access-keys", json={
            "method": method,
        })

        r.raise_for_status()

        key = OutlineAccessKey(self, r.json())

        if name:
            key.rename(name)

        return key

    @property
    def metrics(self) -> DataTransfered:
        """
        Returns the data transfered
        """

        r = self.request.get("/metrics/transfer")
        r.raise_for_status()
        return DataTransfered(r.json())
