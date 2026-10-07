import logging
import asyncio
import time

from uuid import UUID

from . import Module


class ScannerModule(Module):
    """
    Handle all scan related tasks
    """

    RESULT_TTL = 60.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._unprovisioned = set()
        self._last_seen = {}

    def clear_results(self):
        self._unprovisioned.clear()
        self._last_seen.clear()

    def _expire_stale_results(self):
        cutoff = time.monotonic() - self.RESULT_TTL
        expired = [uuid for uuid, seen_at in self._last_seen.items() if seen_at < cutoff]
        for uuid in expired:
            self._last_seen.pop(uuid, None)
            self._unprovisioned.discard(uuid)

    def recent_devices(self):
        self._expire_stale_results()
        return self._unprovisioned

    def has_recent_result(self, uuid):
        self._expire_stale_results()
        return uuid in self._last_seen

    def _scan_result(self, rssi, data, options):
        """
        The method is called from the bluetooth-meshd daemon when a
        unique UUID has been seen during UnprovisionedScan() for
        unprovsioned devices.
        """

        try:
            uuid = UUID(bytes=data[:16])
            self._unprovisioned.add(uuid)
            self._last_seen[uuid] = time.monotonic()
            logging.info(f"Found unprovisioned node: {uuid}")
        except:
            logging.exception("Failed to retrieve UUID")

    async def handle_cli(self, args):
        await self.scan()

        # print user friendly results
        print(f"\nFound {len(self._unprovisioned)} nodes:")
        for uuid in self._unprovisioned:
            print(f"\t{uuid}")

    async def scan(self):
        logging.info("Scanning for unprovisioned devices...")

        await self.app.management_interface.unprovisioned_scan(seconds=10)
        await asyncio.sleep(10.0)
