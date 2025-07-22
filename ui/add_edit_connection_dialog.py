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
from typing import Dict, Optional
from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore    import Qt
from PyQt5 import uic
from qgis.core import QgsSettings, QgsDataSourceUri, QgsProviderRegistry, QgsMessageLog, Qgis


class PostGISConnectionEditor:
    """
    Editor de conexões PostGIS usando APIs nativas do QGIS.
    Responsabilidade única: criar/editar conexões PostGIS.
    """
    
    SETTINGS_GROUP = "PostgreSQL/connections"
    
    def __init__(self):
        self.settings = QgsSettings()
        self.provider_registry = QgsProviderRegistry.instance()
    
    def save_connection(self, connection_info: Dict[str, str]) -> bool:
        """
        Salva uma conexão PostGIS nas configurações do QGIS.
        
        Args:
            connection_info: Dicionário com informações da conexão
            
        Returns:
            True se salva com sucesso, False caso contrário
        """
        try:
            connection_name = connection_info['name']
            
            self.settings.beginGroup(f"{self.SETTINGS_GROUP}/{connection_name}")
            
            # Salva todas as configurações da conexão
            self.settings.setValue('host', connection_info.get('host', ''))
            self.settings.setValue('port', connection_info.get('port', '5432'))
            self.settings.setValue('database', connection_info.get('database', ''))
            self.settings.setValue('username', connection_info.get('username', ''))
            self.settings.setValue('password', connection_info.get('password', ''))
            self.settings.setValue('service', connection_info.get('service', ''))
            self.settings.setValue('sslmode', connection_info.get('sslmode', 'prefer'))
            
            self.settings.endGroup()
            
            QgsMessageLog.logMessage(
                f"Conexão '{connection_name}' salva com sucesso.", 
                "ValidadorRegras", 
                Qgis.Info
            )
            return True
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Erro ao salvar conexão: {e}", 
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
                connection_info.get('host', ''),
                connection_info.get('port', '5432'),
                connection_info.get('database', ''),
                connection_info.get('username', ''),
                connection_info.get('password', '')
            )
            
            if connection_info.get('service'):
                uri.setParam('service', connection_info['service'])
            
            if connection_info.get('sslmode'):
                uri.setParam('sslmode', connection_info['sslmode'])
            
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
    
    def connection_exists(self, name: str) -> bool:
        """
        Verifica se uma conexão com o nome especificado já existe.
        
        Args:
            name: Nome da conexão
            
        Returns:
            True se a conexão existe, False caso contrário
        """
        self.settings.beginGroup(self.SETTINGS_GROUP)
        exists = name in self.settings.childGroups()
        self.settings.endGroup()
        return exists


class AddEditConnectionDialog(QDialog):
    """
    Diálogo para adicionar/editar conexões PostGIS.
    Responsabilidade única: interface para criação/edição de conexões.
    """
    
    def __init__(self, connection_info: Optional[Dict[str, str]] = None, parent=None):
        super().__init__(parent)
        
        # Carrega dinamicamente o .ui
        ui_path = os.path.join(
            os.path.dirname(__file__),
            'add_edit_connection_dialog.ui'
        )
        uic.loadUi(ui_path, self)
        
        self.connection_editor = PostGISConnectionEditor()
        self.connection_info = connection_info
        self.is_editing = connection_info is not None
        
        # Configura o diálogo
        self._setup_dialog()
        
        # Conecta sinais
        self._connect_signals()
        
        # Se está editando, preenche os campos
        if self.is_editing:
            self._populate_fields()
    
    def _setup_dialog(self):
        """Configura o diálogo baseado no modo (adicionar/editar)."""
        if self.is_editing:
            self.setWindowTitle("Editar Conexão PostGIS")
            self.txtName.setEnabled(True)  # Não permite alterar o nome ao editar
        else:
            self.setWindowTitle("Adicionar Conexão PostGIS")
    
    def _connect_signals(self):
        """Conecta os sinais dos botões."""
        self.btnTest.clicked.connect(self._test_connection)
        self.btnSave.clicked.connect(self._save_connection)
        self.btnCancel.clicked.connect(self.reject)
    
    def _populate_fields(self):
        """Preenche os campos com os dados da conexão (modo edição)."""
        if self.connection_info:
            self.txtName.setText(self.connection_info.get('name', ''))
            self.txtHost.setText(self.connection_info.get('host', ''))
            self.txtPort.setText(str(self.connection_info.get('port', '5432')))
            self.txtDatabase.setText(self.connection_info.get('database', ''))
            self.txtUsername.setText(self.connection_info.get('username', ''))
            self.txtPassword.setText(self.connection_info.get('password', ''))
            self.txtService.setText(self.connection_info.get('service', ''))
            
            # Define o modo SSL
            ssl_mode = self.connection_info.get('sslmode', 'prefer')
            index = self.cmbSslMode.findText(ssl_mode)
            if index >= 0:
                self.cmbSslMode.setCurrentIndex(index)
    
    def _get_connection_data(self) -> Dict[str, str]:
        """
        Coleta os dados do formulário.
        
        Returns:
            Dicionário com os dados da conexão
        """
        return {
            'name': self.txtName.text().strip(),
            'host': self.txtHost.text().strip(),
            'port': self.txtPort.text().strip(),
            'database': self.txtDatabase.text().strip(),
            'username': self.txtUsername.text().strip(),
            'password': self.txtPassword.text(),
            'service': self.txtService.text().strip(),
            'sslmode': self.cmbSslMode.currentText()
        }
    
    def _validate_form(self) -> bool:
        """
        Valida os dados do formulário.
        
        Returns:
            True se válido, False caso contrário
        """
        data = self._get_connection_data()
        
        # Campos obrigatórios
        required_fields = ['name', 'host', 'database', 'username']
        for field in required_fields:
            if not data[field]:
                QMessageBox.warning(
                    self, 
                    "Campo obrigatório",
                    f"O campo '{field}' é obrigatório."
                )
                return False
        
        # Valida porta
        try:
            port = int(data['port'])
            if port < 1 or port > 65535:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(
                self, 
                "Porta inválida",
                "A porta deve ser um número entre 1 e 65535."
            )
            return False
        
        # Verifica se o nome já existe (apenas no modo adicionar)
        if not self.is_editing and self.connection_editor.connection_exists(data['name']):
            QMessageBox.warning(
                self, 
                "Nome já existe",
                f"Já existe uma conexão com o nome '{data['name']}'."
            )
            return False
        
        return True
    
    def _test_connection(self):
        """Testa a conexão com os dados atuais do formulário."""
        if not self._validate_form():
            return
        
        connection_data = self._get_connection_data()
        
        # Mostra cursor de espera
        self.setCursor(Qt.WaitCursor)
        self.btnTest.setEnabled(False)
        
        try:
            if self.connection_editor.test_connection(connection_data):
                QMessageBox.information(
                    self, 
                    "Sucesso",
                    "Conexão testada com sucesso!"
                )
            else:
                QMessageBox.critical(
                    self, 
                    "Erro",
                    "Falha ao testar a conexão. Verifique os dados e os logs do QGIS."
                )
        finally:
            # Restaura cursor e botão
            self.unsetCursor()
            self.btnTest.setEnabled(True)
    
    def _save_connection(self):
        """Salva a conexão."""
        if not self._validate_form():
            return
        
        connection_data = self._get_connection_data()
        
        if self.connection_editor.save_connection(connection_data):
            QMessageBox.information(
                self, 
                "Sucesso",
                f"Conexão '{connection_data['name']}' salva com sucesso!"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self, 
                "Erro",
                "Erro ao salvar a conexão. Verifique os logs do QGIS."
            )

