from domain.managers import ip_manager
from utils.tcping import TcpingRunner
from utils.curl import CurlRunner


class MonitorService:
    """Monitor service"""
    def __init__(self):
        pass

    async def run_monitor(self, provider_id, monitor_config):
        """Run monitor"""
        if monitor_config['type'] == 'tcping':
            runner = TcpingRunner()
            runner.run('ip', 'port')
    