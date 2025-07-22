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
import os
from typing import Dict, List, Optional
from PyQt5.QtWidgets import (
    QDialog, QTableWidgetItem, QMessageBox, QButtonGroup, QRadioButton
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5 import uic
from qgis.core import (
    QgsSettings, QgsProviderRegistry, QgsDataSourceUri, 
    QgsMessageLog, Qgis
)

from .add_edit_connection_dialog import AddEditConnectionDialog


class PostGISConnectionManager:
    """
    Gerenciador de conexões PostGIS usando APIs nativas do QGIS.
    Responsabilidade única: gerenciar conexões PostGIS.
    """
    
    SETTINGS_GROUP = "PostgreSQL/connections"
    DEFAULT_CONNECTION_KEY = "validador_regras/default_connection"
    
    def __init__(self):
        self.settings = QgsSettings()
        self.provider_registry = QgsProviderRegistry.instance()
    
    def get_all_connections(self) -> List[Dict[str, str]]:
        """
        Retorna todas as conexões PostGIS disponíveis no QGIS.
        
        Returns:
            Lista de dicionários com informações das conexões
        """
        connections = []
        self.settings.beginGroup(self.SETTINGS_GROUP)
        
        try:
            connection_names = self.settings.childGroups()
            for name in connection_names:
                self.settings.beginGroup(name)
                connection_info = {
                    'name': name,
                    'host': self.settings.value('host', ''),
                    'port': self.settings.value('port', '5432'),
                    'database': self.settings.value('database', ''),
                    'username': self.settings.value('username', ''),
                    'password': self.settings.value('password', ''),
                    'service': self.settings.value('service', ''),
                    'sslmode': self.settings.value('sslmode', ''),
                }
                connections.append(connection_info)
                self.settings.endGroup()
        finally:
            self.settings.endGroup()
        
        return connections
    
    def get_connection_by_name(self, name: str) -> Optional[Dict[str, str]]:
        """
        Retorna uma conexão específica pelo nome.
        
        Args:
            name: Nome da conexão
            
        Returns:
            Dicionário com informações da conexão ou None se não encontrada
        """
        connections = self.get_all_connections()
        return next((conn for conn in connections if conn['name'] == name), None)
    
    def delete_connection(self, name: str) -> bool:
        """
        Remove uma conexão PostGIS.
        
        Args:
            name: Nome da conexão a ser removida
            
        Returns:
            True se removida com sucesso, False caso contrário
        """
        try:
            self.settings.beginGroup(self.SETTINGS_GROUP)
            self.settings.remove(name)
            self.settings.endGroup()
            
            # Se era a conexão padrão, remove a configuração
            if self.get_default_connection() == name:
                self.set_default_connection(None)
            
            QgsMessageLog.logMessage(
                f"Conexão '{name}' removida com sucesso.", 
                "ValidadorRegras", 
                Qgis.Info
            )
            return True
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Erro ao remover conexão '{name}': {e}", 
                "ValidadorRegras", 
                Qgis.Critical
            )
            return False
    
    def test_connection(self, connection_info: Dict[str, str]) -> bool:
        """
        Testa uma conexão PostGIS.
        
        Args:
            connection_info: Dicionário com informações da conexão
            
        Returns:
            True se a conexão foi bem-sucedida, False caso contrário
        """
        try:
            uri = QgsDataSourceUri()
            uri.setConnection(
                connection_info['host'],
                connection_info['port'],
                connection_info['database'],
                connection_info['username'],
                connection_info['password']
            )
            
            # Tenta criar uma conexão usando o provider PostgreSQL
            provider = self.provider_registry.providerMetadata('postgres')
            if provider:
                conn = provider.createConnection(uri.uri(), {})
                if conn:
                    # Testa executando uma query simples
                    result = conn.executeSql("SELECT 1")
                    return len(result) > 0
            
            return False
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Erro ao testar conexão: {e}", 
                "ValidadorRegras", 
                Qgis.Critical
            )
            return False
    
    def get_default_connection(self) -> Optional[str]:
        """
        Retorna o nome da conexão padrão.
        
        Returns:
            Nome da conexão padrão ou None se não definida
        """
        return self.settings.value(self.DEFAULT_CONNECTION_KEY)
    
    def set_default_connection(self, connection_name: Optional[str]):
        """
        Define a conexão padrão.
        
        Args:
            connection_name: Nome da conexão ou None para remover padrão
        """
        if connection_name:
            self.settings.setValue(self.DEFAULT_CONNECTION_KEY, connection_name)
            QgsMessageLog.logMessage(
                f"Conexão '{connection_name}' definida como padrão.", 
                "ValidadorRegras", 
                Qgis.Info
            )
        else:
            self.settings.remove(self.DEFAULT_CONNECTION_KEY)
            QgsMessageLog.logMessage(
                "Conexão padrão removida.", 
                "ValidadorRegras", 
                Qgis.Info
            )


class ManageConnectionsDialog(QDialog):
    """
    Diálogo para gerenciar conexões PostGIS.
    Responsabilidade única: interface para gerenciamento de conexões.
    """
    
    connections_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Carrega dinamicamente o .ui
        ui_path = os.path.join(
            os.path.dirname(__file__),
            'manage_connections_dialog.ui'
        )
        uic.loadUi(ui_path, self)
        
        self.connection_manager = PostGISConnectionManager()
        self.radio_button_group = QButtonGroup(self)
        
        # Configura a tabela
        self._setup_table()
        
        # Preenche tabela
        self._populate_table()
        
        # Conecta botões
        self._connect_signals()
    
    def _setup_table(self):
        """Configura a tabela de conexões."""
        self.tblConexoes.setSelectionBehavior(self.tblConexoes.SelectRows)
        self.tblConexoes.setAlternatingRowColors(True)
    
    def _connect_signals(self):
        """Conecta os sinais dos botões."""
        self.btnAdd.clicked.connect(self._add_connection)
        self.btnEdit.clicked.connect(self._edit_connection)
        self.btnRemove.clicked.connect(self._remove_connection)
        self.btnTest.clicked.connect(self._test_selected_connection)
        self.btnClose.clicked.connect(self.accept)
    
    def _populate_table(self):
        """Carrega todas as conexões PostGIS na tabela."""
        self.tblConexoes.setRowCount(0)
        self.radio_button_group = QButtonGroup(self)
        
        connections = self.connection_manager.get_all_connections()
        default_connection = self.connection_manager.get_default_connection()
        
        for connection in connections:
            row = self.tblConexoes.rowCount()
            self.tblConexoes.insertRow(row)
            
            # Preenche as colunas
            self.tblConexoes.setItem(row, 0, QTableWidgetItem(connection['name']))
            self.tblConexoes.setItem(row, 1, QTableWidgetItem(connection['host']))
            self.tblConexoes.setItem(row, 2, QTableWidgetItem(str(connection['port'])))
            self.tblConexoes.setItem(row, 3, QTableWidgetItem(connection['username']))
            
            # Adiciona radio button para conexão padrão
            radio_button = QRadioButton()
            radio_button.setProperty('connection_name', connection['name'])
            
            if connection['name'] == default_connection:
                radio_button.setChecked(True)
            
            radio_button.toggled.connect(self._on_default_changed)
            self.radio_button_group.addButton(radio_button)
            self.tblConexoes.setCellWidget(row, 4, radio_button)
    
    def _on_default_changed(self, checked: bool):
        """Callback para mudança da conexão padrão."""
        if checked:
            sender = self.sender()
            connection_name = sender.property('connection_name')
            self.connection_manager.set_default_connection(connection_name)
    
    def _add_connection(self):
        """Abre diálogo para adicionar nova conexão."""
        dlg = AddEditConnectionDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._populate_table()
            self.connections_updated.emit()
    
    def _edit_connection(self):
        """Abre diálogo para editar conexão selecionada."""
        row = self.tblConexoes.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, 
                "Selecione uma conexão",
                "Por favor, selecione uma conexão para editar."
            )
            return
        
        connection_name = self.tblConexoes.item(row, 0).text()
        connection_info = self.connection_manager.get_connection_by_name(connection_name)
        
        if connection_info:
            dlg = AddEditConnectionDialog(connection_info, parent=self)
            if dlg.exec_() == QDialog.Accepted:
                self._populate_table()
                self.connections_updated.emit()
    
    def _remove_connection(self):
        """Remove a conexão selecionada."""
        row = self.tblConexoes.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, 
                "Selecione uma conexão",
                "Por favor, selecione uma conexão para remover."
            )
            return
        
        connection_name = self.tblConexoes.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, 
            "Confirmar remoção",
            f"Tem certeza que deseja remover a conexão '{connection_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.connection_manager.delete_connection(connection_name):
                self._populate_table()
                self.connections_updated.emit()
                QMessageBox.information(
                    self, 
                    "Sucesso", 
                    f"Conexão '{connection_name}' removida com sucesso."
                )
    
    def _test_selected_connection(self):
        """Testa a conexão selecionada."""
        row = self.tblConexoes.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, 
                "Selecione uma conexão",
                "Por favor, selecione uma conexão para testar."
            )
            return
        
        connection_name = self.tblConexoes.item(row, 0).text()
        connection_info = self.connection_manager.get_connection_by_name(connection_name)
        
        if connection_info:
            if self.connection_manager.test_connection(connection_info):
                QMessageBox.information(
                    self, 
                    "Sucesso",
                    f"Conexão '{connection_name}' testada com sucesso!"
                )
            else:
                QMessageBox.critical(
                    self, 
                    "Erro",
                    f"Falha ao testar a conexão '{connection_name}'. "
                    "Verifique os logs do QGIS para mais detalhes."
                )

