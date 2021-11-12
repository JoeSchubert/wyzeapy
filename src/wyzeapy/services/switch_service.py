#  Copyright (c) 2021. Mulliken, LLC - All Rights Reserved
#  You may use, distribute and modify this code under the terms
#  of the attached license. You should have received a copy of
#  the license with this file. If not, please write to:
#  joshua@mulliken.net to receive a copy
from typing import List, Dict, Any

from wyzeapy.services.base_service import BaseService
from wyzeapy.types import Device, DeviceTypes, PropertyIDs
from datetime import datetime, time, timedelta, timezone


class Switch(Device):
    def __init__(self, dictionary: Dict[Any, Any]):
        super().__init__(dictionary)
        self.on: bool = False

class SwitchUsage(Switch):
    def __init__(self, dictionary: Dict[Any, Any]):
        super().__init__(dictionary)
        self._usage_history = {
            "0000000000000": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        }


class SwitchService(BaseService):
    async def update(self, switch: Switch):
        # Get updated device_params
        async with BaseService._update_lock:
            switch.device_params = await self.get_updated_params(switch.mac)

        device_info = await self._get_property_list(switch)

        for property_id, value in device_info:
            if property_id == PropertyIDs.ON:
                switch.on = value == "1"
            elif property_id == PropertyIDs.AVAILABLE:
                switch.available = value == "1"

        return switch

    async def get_switches(self) -> List[Switch]:
        if self._devices is None:
            self._devices = await self.get_object_list()

        devices = [device for device in self._devices if device.type is DeviceTypes.PLUG or
                   device.type is DeviceTypes.OUTDOOR_PLUG]
        return [Switch(switch.raw_dict) for switch in devices]

    async def turn_on(self, switch: Switch):
        await self._set_property(switch, PropertyIDs.ON.value, "1")

    async def turn_off(self, switch: Switch):
        await self._set_property(switch, PropertyIDs.ON.value, "0")


class SwitchUsageService(SwitchService):
    """ Class that inherits from the Switch Service to override the update functionality"""
    async def get_switches(self) -> List[SwitchUsage]:
        if self._devices is None:
            self._devices = await self.get_object_list()

        devices = [device for device in self._devices if device.type is DeviceTypes.PLUG or
                   device.type is DeviceTypes.OUTDOOR_PLUG]
        return [SwitchUsage(switch.raw_dict) for switch in devices]

    async def update(self, device: Device,
                     start_time=int(datetime.timestamp(datetime.combine(
                         datetime.utcnow(), time.min, tzinfo=timezone.utc) - timedelta(days=7)) * 1000),
                     end_time=int(datetime.timestamp(datetime.combine(
                         datetime.utcnow(), time.max, tzinfo=timezone.utc)) * 1000)
                     ):
        """
        :param device: The device to gather history for
        :param start_time: The start time to gather history for in seconds since epoch
        :param end_time: The end time to gather history for in seconds since epoch
        :return: device with property _usage_history as a
            dictionary where the key is the timestamp for the day and the value is a list of power usage where the index is the hour (0-23)
        """
        device._usage_history = await self._get_plug_history(device, start_time, end_time)

        return device
