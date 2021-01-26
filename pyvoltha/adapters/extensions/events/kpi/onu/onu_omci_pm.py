# Copyright 2017-present Open Networking Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division
import arrow
from voltha_protos.device_pb2 import PmConfig, PmGroupConfig
from voltha_protos.events_pb2 import MetricInformation, MetricMetaData
from pyvoltha.adapters.extensions.events.kpi.adapter_pm_metrics import AdapterPmMetrics
from pyvoltha.adapters.extensions.events.kpi.onu.onu_pm_interval_metrics import OnuPmIntervalMetrics
from pyvoltha.adapters.extensions.omci.omci_entities import UniG
from pyvoltha.adapters.extensions.omci.omci_entities import PptpEthernetUni


class OnuOmciPmMetrics(AdapterPmMetrics):
    """ ONU OMCI related metrics """

    # Metric default settings
    #
    #  Frequency values are in units of one second
    #
    OMCI_DEV_KEY = 'omci-onu-dev'
    OMCI_CC_GROUP_NAME = 'OMCI_CC'
    DEFAULT_OMCI_CC_ENABLED = False
    DEFAULT_OMCI_CC_FREQUENCY = (2 * 60)

    OPTICAL_GROUP_NAME = 'PON_Optical'
    DEFAULT_OPTICAL_ENABLED = True
    DEFAULT_OPTICAL_FREQUENCY = (15 * 60)

    UNI_STATUS_GROUP_NAME = 'UNI_Status'
    DEFAULT_UNI_STATUS_ENABLED = True
    DEFAULT_UNI_STATUS_FREQUENCY = (15 * 60)

    def __init__(self, event_mgr, core_proxy, device_id, logical_device_id, serial_number,
                 grouped=False, freq_override=False, **kwargs):
        """
        Initializer for shared ONU Device Adapter OMCI CC PM metrics

        :param core_proxy: (CoreProxy) Core proxy for the device
        :param device_id: (str) Device ID
        :param logical_device_id: (str) VOLTHA Logical Device ID
        :param grouped: (bool) Flag indicating if statistics are managed as a group
        :param freq_override: (bool) Flag indicating if frequency collection can be specified
                                     on a per group basis
        :param kwargs: (dict) Device Adapter specific values. For an ONU Device adapter, the
                              expected key-value pairs are listed below. If not provided, the
                              associated PM statistics are not gathered:

                              'omci-onu-dev': Reference to the OMCI OnuDeviceEtnry object for
                                         retrieval of OpenOMCI Communications channel statistics
                                         and retrieval of polled statistics.
        """
        super(OnuOmciPmMetrics, self).__init__(event_mgr, core_proxy, device_id, logical_device_id, serial_number,
                                               grouped=grouped, freq_override=freq_override,
                                               **kwargs)

        self._omci_onu_device = kwargs.pop(OnuOmciPmMetrics.OMCI_DEV_KEY, None)
        self._omci_cc = self._omci_onu_device.omci_cc if self._omci_onu_device is not None else None

        self.omci_cc_pm_names = {
            ('tx_frames', PmConfig.COUNTER),
            ('tx_errors', PmConfig.COUNTER),
            ('rx_frames', PmConfig.COUNTER),
            ('rx_unknown_tid', PmConfig.COUNTER),
            ('rx_onu_frames', PmConfig.COUNTER),        # Rx ONU autonomous messages
            ('rx_unknown_me', PmConfig.COUNTER),        # Managed Entities without a decode definition
            ('rx_timeouts', PmConfig.COUNTER),
            ('rx_late', PmConfig.COUNTER),
            ('consecutive_errors', PmConfig.COUNTER),
            ('reply_min', PmConfig.GAUGE),      # Milliseconds
            ('reply_max', PmConfig.GAUGE),      # Milliseconds
            ('reply_average', PmConfig.GAUGE),  # Milliseconds
            ('hp_tx_queue_len', PmConfig.GAUGE),
            ('lp_tx_queue_len', PmConfig.GAUGE),
            ('max_hp_tx_queue', PmConfig.GAUGE),
            ('max_lp_tx_queue', PmConfig.GAUGE),
        }
        self.omci_cc_metrics_config = {m: PmConfig(name=m, type=t, enabled=True)
                                       for (m, t) in self.omci_cc_pm_names}

        self.omci_optical_pm_names = {
            ('intf_id', PmConfig.CONTEXT),

            ('transmit_power', PmConfig.GAUGE),
            ('receive_power', PmConfig.GAUGE),
        }
        self.omci_optical_metrics_config = {m: PmConfig(name=m, type=t, enabled=True)
                                            for (m, t) in self.omci_optical_pm_names}

        self.omci_uni_pm_names = {
            ('intf_id', PmConfig.CONTEXT),

            ('ethernet_type', PmConfig.GAUGE),     # PPTP Ethernet ME
            ('oper_status', PmConfig.GAUGE),       # PPTP Ethernet ME
            ('pptp_admin_state', PmConfig.GAUGE),  # PPTP Ethernet ME
            ('uni_admin_state', PmConfig.GAUGE),   # UNI-G ME
        }
        self.omci_uni_metrics_config = {m: PmConfig(name=m, type=t, enabled=True)
                                        for (m, t) in self.omci_uni_pm_names}

        self.openomci_interval_pm = OnuPmIntervalMetrics(event_mgr, core_proxy, device_id, logical_device_id,
                                                         serial_number)

        self.last_collect_optical_metrics = None

    def update(self, pm_config):
        # TODO: Test frequency override capability for a particular group
        if self.default_freq != pm_config.default_freq:
            # Update the callback to the new frequency.
            self.default_freq = pm_config.default_freq
            self.stop_collector()
            self.start_collector()

        if pm_config.grouped:
            for group in pm_config.groups:
                group_config = self.pm_group_metrics.get(group.group_name)
                if group_config is not None:
                    group_config.enabled = group.enabled
        else:
            msg = 'There are on independent OMCI metrics, only group metrics at this time'
            raise NotImplemented(msg)

        self.openomci_interval_pm.update(pm_config)

    def make_proto(self, pm_config=None):
        assert pm_config is not None

        # OMCI only supports grouped metrics
        if self._omci_onu_device is None or not self.grouped:
            return pm_config

        pm_omci_cc_stats = PmGroupConfig(group_name=OnuOmciPmMetrics.OMCI_CC_GROUP_NAME,
                                         group_freq=OnuOmciPmMetrics.DEFAULT_OMCI_CC_FREQUENCY,
                                         enabled=OnuOmciPmMetrics.DEFAULT_OMCI_CC_ENABLED)
        self.pm_group_metrics[pm_omci_cc_stats.group_name] = pm_omci_cc_stats

        pm_omci_optical_stats = PmGroupConfig(group_name=OnuOmciPmMetrics.OPTICAL_GROUP_NAME,
                                              group_freq=OnuOmciPmMetrics.DEFAULT_OPTICAL_FREQUENCY,
                                              enabled=OnuOmciPmMetrics.DEFAULT_OPTICAL_ENABLED)
        self.pm_group_metrics[pm_omci_optical_stats.group_name] = pm_omci_optical_stats

        pm_omci_uni_stats = PmGroupConfig(group_name=OnuOmciPmMetrics.UNI_STATUS_GROUP_NAME,
                                          group_freq=OnuOmciPmMetrics.DEFAULT_UNI_STATUS_FREQUENCY,
                                          enabled=OnuOmciPmMetrics.DEFAULT_UNI_STATUS_ENABLED)
        self.pm_group_metrics[pm_omci_uni_stats.group_name] = pm_omci_uni_stats

        stats_and_config = [(pm_omci_cc_stats, self.omci_cc_metrics_config),
                            (pm_omci_optical_stats, self.omci_optical_metrics_config),
                            (pm_omci_uni_stats, self.omci_cc_metrics_config)]

        for stats, config in stats_and_config:
            for m in sorted(config):
                pm = config[m]
                stats.metrics.extend([PmConfig(name=pm.name,
                                               type=pm.type,
                                               enabled=pm.enabled)])
            pm_config.groups.extend([stats])

        # Also create OMCI Interval PM configs
        return self.openomci_interval_pm.make_proto(pm_config)

    def collect_metrics(self, data=None):
        """
        Collect metrics for this adapter.

        The data collected (or passed in) is a list of pairs/tuples.  Each
        pair is composed of a MetricMetaData metadata-portion and list of MetricValuePairs
        that contains a single individual metric or list of metrics if this is a
        group metric.

        This method is called for each adapter at a fixed frequency.
        TODO: Currently all group metrics are collected on a single timer tick.
              This needs to be fixed as independent group or instance collection is
              desirable.

        :param data: (list) Existing list of collected metrics (MetricInformation).
                            This is provided to allow derived classes to call into
                            further encapsulated classes.

        :return: (list) metadata and metrics pairs - see description above
        """
        if data is None:
            data = list()

        # Note: Interval PM is collection done autonomously, not through this method

        if self._omci_cc is not None:
            group_name = OnuOmciPmMetrics.OMCI_CC_GROUP_NAME
            if self.pm_group_metrics[group_name].enabled:
                group_data = self.collect_group_metrics(group_name,
                                                        self._omci_cc,
                                                        self.omci_cc_pm_names,
                                                        self.omci_cc_metrics_config)
                if group_data is not None:
                    data.append(group_data)

            # Optical and UNI data is collected on a per-port basis
            data.extend(self.collect_optical_metrics())
            data.extend(self.collect_uni_status_metrics())

        return data

    def collect_optical_metrics(self):
        """
        Collect the metrics for optical information from all ANI/PONs

        :return: (list) collected metrics (MetricInformation)
        """
        now = self._omci_onu_device.timestamp

        group_name = OnuOmciPmMetrics.OPTICAL_GROUP_NAME
        if now is None or not self.pm_group_metrics[group_name].enabled:
            return []

        # Because several different metrics are collected by this class,
        # and the collection interval may be more often than the group interval,
        # check and make sure these metrics are actually due at this time.
        if self.last_collect_optical_metrics:
            elapsed_tenths = now - self.last_collect_optical_metrics
            if elapsed_tenths < self.pm_group_metrics[group_name].group_freq:
                self.log.info("collect-optical-metrics-not-time-yet", elapsed_tenths=elapsed_tenths)
                return []

        # Scan all ANI-G ports
        ani_g_entities = self._omci_onu_device.configuration.ani_g_entities
        ani_g_entities_ids = list(ani_g_entities.keys()) if ani_g_entities is not None else None
        metrics_info = []

        if ani_g_entities_ids is not None and len(ani_g_entities_ids):
            from pyvoltha.adapters.extensions.omci.omci_entities import AniG
            ani_g_items = ['optical_signal_level', 'transmit_optical_level']

            for entity_id in ani_g_entities_ids:
                metrics = dict()
                data = self._omci_onu_device.query_mib(class_id=AniG.class_id,
                                                       instance_id=entity_id,
                                                       attributes=ani_g_items)
                if len(data):
                    if 'optical_signal_level' in data:
                        metrics['receive_power'] = data['optical_signal_level']

                    if 'transmit_optical_level' in data:
                        metrics['transmit_power'] = data['transmit_optical_level']

                if len(metrics):
                    metric_data = MetricInformation(metadata=MetricMetaData(title=group_name,
                                                                            ts=now,
                                                                            logical_device_id=self.logical_device_id,
                                                                            serial_no=self.serial_number,
                                                                            device_id=self.device_id,
                                                                            context={
                                                                                'intf_id': str(entity_id)
                                                                            }),
                                                    metrics=metrics)
                    metrics_info.append(metric_data)

        self.last_collect_optical_metrics = now

        return metrics_info

    def collect_uni_status_metrics(self):
        """
        Collect the metrics for optical information from all ANI/PONs

        :return: (list) collected metrics (MetricInformation)
        """
        now = self._omci_onu_device.timestamp

        group_name = OnuOmciPmMetrics.UNI_STATUS_GROUP_NAME
        if now is None or not self.pm_group_metrics[group_name].enabled:
            return []

        # Scan all UNI-G and PPTP ports
        uni_g_entities = self._omci_onu_device.configuration.uni_g_entities
        uni_g_entities_ids = list(uni_g_entities.keys()) if uni_g_entities is not None else None
        pptp_entities = self._omci_onu_device.configuration.pptp_entities
        pptp_entities_ids = list(pptp_entities.keys()) if pptp_entities is not None else None

        metrics_info = []

        if uni_g_entities_ids and pptp_entities_ids and len(uni_g_entities_ids) and \
                len(uni_g_entities_ids) <= len(pptp_entities_ids):

            uni_g_items = ['administrative_state']
            pptp_items = ['administrative_state', 'operational_state', 'sensed_type']

            for entity_id in pptp_entities_ids:
                metrics = dict()
                data = self._omci_onu_device.query_mib(class_id=UniG.class_id,
                                                       instance_id=entity_id,
                                                       attributes=uni_g_items)
                if len(data):
                    if 'administrative_state' in data:
                        metrics['uni_admin_state'] = data['administrative_state']

                data = self._omci_onu_device.query_mib(class_id=PptpEthernetUni.class_id,
                                                       instance_id=entity_id,
                                                       attributes=pptp_items)
                if len(data):
                    if 'administrative_state' in data:
                        metrics['pptp_admin_state'] = data['administrative_state']

                    if 'operational_state' in data:
                        metrics['oper_status'] = data['operational_state']

                    if 'sensed_type' in data:
                        metrics['ethernet_type'] = data['sensed_type']

                if len(metrics):
                    metric_data = MetricInformation(metadata=MetricMetaData(title=group_name,
                                                                            ts=now,
                                                                            logical_device_id=self.logical_device_id,
                                                                            serial_no=self.serial_number,
                                                                            device_id=self.device_id,
                                                                            context={
                                                                                'intf_id': str(entity_id & 0xFF)
                                                                            }),
                                                    metrics=metrics)
                    metrics_info.append(metric_data)

        return metrics_info
