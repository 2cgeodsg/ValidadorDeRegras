import json
from typing import List, Optional
from qgis.core import QgsMessageLog, Qgis

from ..core.interfaces import IConnectionRepository
from ..core.connection_config import ConnectionConfig

class JsonConnectionRepository(IConnectionRepository):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._connections = self._load_connections()

    def _load_connections(self) -> List[ConnectionConfig]:
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                return [ConnectionConfig(**conn) for conn in data]
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            QgsMessageLog.logMessage(f'Erro ao decodificar JSON do arquivo de conexões: {self.file_path}', 'ConnectionManager', Qgis.Warning)
            return []

    def _save_connections(self):
        with open(self.file_path, 'w') as f:
            json.dump([conn.__dict__ for conn in self._connections], f, indent=4)

    def get_all(self) -> List[ConnectionConfig]:
        return list(self._connections)

    def get_by_name(self, name: str) -> Optional[ConnectionConfig]:
        return next((conn for conn in self._connections if conn.name == name), None)

    def add(self, config: ConnectionConfig):
        if self.get_by_name(config.name):
            raise ValueError(f'Conexão com o nome "{config.name}" já existe.')
        self._connections.append(config)
        self._save_connections()

    def update(self, config: ConnectionConfig):
        for i, conn in enumerate(self._connections):
            if conn.name == config.name:
                self._connections[i] = config
                self._save_connections()
                return
        raise ValueError(f'Conexão com o nome "{config.name}" não encontrada para atualização.')

    def delete(self, name: str):
        initial_len = len(self._connections)
        self._connections = [conn for conn in self._connections if conn.name != name]
        if len(self._connections) == initial_len:
            raise ValueError(f'Conexão com o nome "{name}" não encontrada para remoção.')
        self._save_connections()

    def set_default(self, name: str):
        found = False
        for conn in self._connections:
            if conn.name == name:
                conn.is_default = True
                found = True
            else:
                conn.is_default = False
        if not found:
            raise ValueError(f'Conexão com o nome "{name}" não encontrada para definir como padrão.')
        self._save_connections()


