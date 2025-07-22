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
from abc import ABC, abstractmethod
from typing import List, Optional
from .connection_config import ConnectionConfig

class IConnectionRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[ConnectionConfig]:
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[ConnectionConfig]:
        pass

    @abstractmethod
    def add(self, config: ConnectionConfig):
        pass

    @abstractmethod
    def update(self, config: ConnectionConfig):
        pass

    @abstractmethod
    def delete(self, name: str):
        pass

    @abstractmethod
    def set_default(self, name: str):
        pass

class IConnectionTester(ABC):
    @abstractmethod
    def test_connection(self, config: ConnectionConfig) -> bool:
        pass




class IValidationRule(ABC):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def run(self, connection_config: ConnectionConfig, log_callback=None, progress_callback=None) -> bool:
        pass


