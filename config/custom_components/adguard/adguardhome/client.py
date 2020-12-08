"""Asynchronous Python client for the AdGuard Home API."""

from .exceptions import AdGuardHomeError


class AdGuardHomeClient:
    """Controls AdGuard Home client settings."""

    def __init__(self, adguard):
        """Initilaze object."""
        self._adguard = adguard
        self._disallowed_clients = []
        self._response = None
        # self._acces_list_update()

    async def _client_settings(self, ip: str):
        response = await self._adguard._request("clients/find", params={"ip0": ip})
        if len(response) != 1:
            raise AdGuardHomeError("Client not found", {"response": response})
        return response

    async def _client_update(self, data: dict):
        await self._adguard._request(
            "clients/update",
            method="POST",
            json_data={"data": data, "name": data["name"]},
        )

    async def disallowed_clients(self) -> list:
        """Return the disallowed_clients."""
        response = await self._adguard._request("access/list", method="GET",)
        self._disallowed_clients = response["disallowed_clients"]
        self._response = response
        return response["disallowed_clients"]

    async def enable_client(self, ip: str) -> None:
        """Enable a filter subscription in AdGuard Home."""
        await self.disallowed_clients()
        if ip in self._disallowed_clients:
            self._disallowed_clients.remove(ip)
        disallowed_clients = self._disallowed_clients
        json_data = {
            "allowed_clients": [],
            "blocked_hosts": ["version.bind", "id.server", "hostname.bind"],
            "disallowed_clients": disallowed_clients,
        }
        try:
            await self._adguard._request(
                "access/set",
                method="POST",
                json_data={
                    "allowed_clients": [],
                    "blocked_hosts": ["version.bind", "id.server", "hostname.bind"],
                    "disallowed_clients": disallowed_clients,
                },
            )
        except AdGuardHomeError as exception:
            raise AdGuardHomeError(
                "Failed disabling URL on AdGuard Home filter", exception, json_data,
            )
        await self.disallowed_clients()

    async def disable_client(self, ip: str) -> None:
        """Disable a filter subscription in AdGuard Home."""
        await self.disallowed_clients()
        if ip not in self._disallowed_clients:
            self._disallowed_clients.append(ip)
        disallowed_clients = self._disallowed_clients
        try:
            await self._adguard._request(
                "access/set",
                method="POST",
                json_data={
                    "allowed_clients": [],
                    "blocked_hosts": ["version.bind", "id.server", "hostname.bind"],
                    "disallowed_clients": disallowed_clients,
                },
            )
        except AdGuardHomeError as exception:
            raise AdGuardHomeError(
                "Failed disabling URL on AdGuard Home filter", exception
            )
        await self.disallowed_clients()

    async def allow_service(self, ip: str, service: str) -> None:
        """Allow ip to access service."""
        response = await self._client_settings(ip)
        if response:
            data = response[0][ip]
            if service in data["blocked_services"]:
                data["blocked_services"].remove(service)
                await self._client_update(data)

    async def block_service(self, ip: str, service: str) -> None:
        """Block ip from accessing service."""
        response = await self._client_settings(ip)
        if response:
            data = response[0][ip]
            if service not in data["blocked_services"]:
                data["blocked_services"].append(service)
                await self._client_update(data)
