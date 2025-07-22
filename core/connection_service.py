"""
/***************************************************************************
 Validador de Regras PostGis
                                 A QGIS plugin
 2ºCGEO
                              -------------------
        begin                : 2025-07-16
        git sha              : $Format:%H$
        copyright            : (C) 2025 by Godinho, Alvarez, Perrut
        email                : estevezcodando@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from typing import List, Optional
from qgis.core import QgsMessageLog, Qgis
from .interfaces import IConnectionRepository, IConnectionTester
from .connection_config import ConnectionConfig

class ConnectionService:
    def __init__(self, repository: IConnectionRepository, tester: IConnectionTester):
        self._repository = repository
        self._tester = tester

    def get_all_connections(self) -> List[ConnectionConfig]:
        return self._repository.get_all()

    def get_connection_by_name(self, name: str) -> Optional[ConnectionConfig]:
        return self._repository.get_by_name(name)

    def add_connection(self, config: ConnectionConfig):
        try:
            self._repository.add(config)
            QgsMessageLog.logMessage(f"Conexão \"{config.name}\" adicionada com sucesso.", "ConnectionManager", Qgis.Info)
        except ValueError as e:
            QgsMessageLog.logMessage(f"Erro ao adicionar conexão \"{config.name}\": {e}", "ConnectionManager", Qgis.Critical)
            raise

    def update_connection(self, config: ConnectionConfig):
        try:
            self._repository.update(config)
            QgsMessageLog.logMessage(f"Conexão \"{config.name}\" atualizada com sucesso.", "ConnectionManager", Qgis.Info)
        except ValueError as e:
            QgsMessageLog.logMessage(f"Erro ao atualizar conexão \"{config.name}\": {e}", "ConnectionManager", Qgis.Critical)
            raise

    def delete_connection(self, name: str):
        try:
            self._repository.delete(name)
            QgsMessageLog.logMessage(f"Conexão \"{name}\" removida com sucesso.", "ConnectionManager", Qgis.Info)
        except ValueError as e:
            QgsMessageLog.logMessage(f"Erro ao remover conexão \"{name}\": {e}", "ConnectionManager", Qgis.Critical)
            raise

    def test_connection(self, config: ConnectionConfig) -> bool:
        return self._tester.test_connection(config)

    def get_default_connection(self) -> ConnectionConfig:
        """
        Retorna a ConnectionConfig marcada como padrão.
        Lança ValueError se nenhuma estiver definida.
        """
        all_conns = self.get_all_connections()
        for cfg in all_conns:
            if getattr(cfg, "is_default", False):
                return cfg
        raise ValueError("Nenhuma conexão padrão definida.")


