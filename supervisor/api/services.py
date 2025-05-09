"""Init file for Supervisor network RESTful API."""

from ..const import (
    ATTR_AVAILABLE,
    ATTR_PROVIDERS,
    ATTR_SERVICES,
    ATTR_SLUG,
    PROVIDE_SERVICE,
    REQUEST_FROM,
)
from ..coresys import CoreSysAttributes
from ..exceptions import APIError, APIForbidden, APINotFound
from .utils import api_process, api_validate


class APIServices(CoreSysAttributes):
    """Handle RESTful API for services functions."""

    def _extract_service(self, request):
        """Return service, throw an exception if it doesn't exist."""
        service = self.sys_services.get(request.match_info.get("service"))
        if not service:
            raise APINotFound("Service does not exist")

        return service

    @api_process
    async def list_services(self, request):
        """Show register services."""
        services = []
        for service in self.sys_services.list_services:
            services.append(
                {
                    ATTR_SLUG: service.slug,
                    ATTR_AVAILABLE: service.enabled,
                    ATTR_PROVIDERS: service.providers,
                }
            )

        return {ATTR_SERVICES: services}

    @api_process
    async def set_service(self, request):
        """Write data into a service."""
        service = self._extract_service(request)
        body = await api_validate(service.schema, request)
        addon = request[REQUEST_FROM]

        _check_access(request, service.slug)
        await service.set_service_data(addon, body)

    @api_process
    async def get_service(self, request):
        """Read data into a service."""
        service = self._extract_service(request)

        # Access
        _check_access(request, service.slug)

        if not service.enabled:
            raise APIError("Service not enabled")
        return service.get_service_data()

    @api_process
    async def del_service(self, request):
        """Delete data into a service."""
        service = self._extract_service(request)
        addon = request[REQUEST_FROM]

        # Access
        _check_access(request, service.slug, True)
        await service.del_service_data(addon)


def _check_access(request, service, provide=False):
    """Raise error if the rights are wrong."""
    addon = request[REQUEST_FROM]
    if not addon.services_role.get(service):
        raise APIForbidden(f"No access to {service} service!")

    if provide and addon.services_role.get(service) != PROVIDE_SERVICE:
        raise APIForbidden(f"No access to write {service} service!")
