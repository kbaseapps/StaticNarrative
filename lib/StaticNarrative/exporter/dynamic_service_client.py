"""Client for dealing with KBase dynamic services."""

import time

from installed_clients.baseclient import BaseClient, ServerError


class DynamicServiceClient:
    def __init__(
        self: "DynamicServiceClient",
        sw_url: str,
        service_ver: str,
        module_name: str,
        token: str,
        url_cache_time: int = 300,
    ) -> None:
        """Initialise a dynamic service client.

        :param self: this class
        :type self: DynamicServiceClient
        :param sw_url: service worker URL
        :type sw_url: str
        :param service_ver: service version
        :type service_ver: str
        :param module_name: module to be accessed
        :type module_name: str
        :param token: KBase auth
        :type token: str
        :param url_cache_time: time in seconds to cache the URL for, defaults to 300
        :type url_cache_time: int, optional
        """
        self.sw_url = sw_url
        self.service_ver = service_ver
        self.module_name = module_name
        self.url_cache_time = url_cache_time
        self.cached_url = None
        self.last_refresh_time = None
        self.token = token

    def call_method(
        self: "DynamicServiceClient", method: str, params_array: list
    ) -> list:
        """
        Calls the given method. Uses the BaseClient and cached service URL.
        """
        was_url_refreshed = False
        if not self.cached_url or (
            time.time() - self.last_refresh_time > self.url_cache_time
        ):
            self._lookup_url()
            was_url_refreshed = True
        try:
            return self._call(method, params_array, self.token)
        except ServerError:
            # Happens if a URL expired for real, even though it's still cached.
            if was_url_refreshed:
                raise  # Forwarding error with no changes
            self._lookup_url()
            method_call_return = self._call(method, params_array, self.token)
            return method_call_return

    def _lookup_url(self: "DynamicServiceClient") -> None:
        bc = BaseClient(url=self.sw_url, lookup_url=False)
        self.cached_url = bc.call_method(
            "ServiceWizard.get_service_status",
            [{"module_name": self.module_name, "version": self.service_ver}],
        )["url"]
        self.last_refresh_time = time.time()

    def _call(
        self: "DynamicServiceClient", method: str, params_array: list, token: str
    ) -> list:
        bc = BaseClient(url=self.cached_url, token=token, lookup_url=False)
        return bc.call_method(self.module_name + "." + method, params_array)
