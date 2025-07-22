import psycopg2
from qgis.core import QgsMessageLog, Qgis

from ..core.interfaces import IConnectionTester
from ..core.connection_config import ConnectionConfig

class Psycopg2ConnectionTester(IConnectionTester):
    def test_connection(self, config: ConnectionConfig) -> bool:
        try:
            conn_str = f"host={config.host} port={config.port} user={config.user} password={config.password} dbname=postgres"
            with psycopg2.connect(conn_str, connect_timeout=5) as conn:
                QgsMessageLog.logMessage(f"Conexão com \"{config.name}\" testada com sucesso.", "ConnectionManager", Qgis.Info)
                return True
        except psycopg2.OperationalError as e:
            QgsMessageLog.logMessage(f"Erro ao testar conexão com \"{config.name}\": {e}", "ConnectionManager", Qgis.Critical)
            return False
        except Exception as e:
            QgsMessageLog.logMessage(f"Erro inesperado ao testar conexão com \"{config.name}\": {e}", "ConnectionManager", Qgis.Critical)
            return False


