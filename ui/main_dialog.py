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
from PyQt5.QtWidgets import QDialog, QMessageBox, QApplication
from PyQt5.QtCore import QTimer, QDateTime, Qt
from PyQt5 import uic
from qgis.core import QgsMessageLog, Qgis, QgsApplication

from .manage_connections_dialog import ManageConnectionsDialog
from ..core.database_service import (
    DatabaseConnectionService, SchemaService, FunctionService, FunctionExecutionTask
)
from PyQt5.QtGui import QIcon
import resources_rc

class MainDialog(QDialog):
    """
    Diálogo principal do plugin.
    Responsabilidade única: interface principal para execução de funções.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Carrega UI dinamicamente
        ui_path = os.path.join(os.path.dirname(__file__), 'main_dialog.ui')
        uic.loadUi(ui_path, self)
        self.btnPlay.setIcon(QIcon(":/plugins/validador_regras/icons/play.svg"))
        self.btnStop.setIcon(QIcon(":/plugins/validador_regras/icons/pause.svg"))
        # Inicializa serviços
        self.connection_service = DatabaseConnectionService()
        self.schema_service = SchemaService(self.connection_service)
        self.function_service = FunctionService(self.connection_service)
        
        # Estado interno
        self.current_connection = None
        self.current_task = None
        self.start_time = None
        
        # Configura timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer)
        
        # Configura interface
        self._setup_ui()
        
        # Conecta sinais
        self._connect_signals()
        
        # Carrega conexões e seleciona a padrão
        self._load_connections()
    
    def _setup_ui(self):
        """Configura a interface do usuário."""
        # Configura botões iniciais
        self.btnStop.setEnabled(False)
        self.progressBar.setVisible(False)
        
        # Configura logs
        
        # Log inicial
        self._log("Plugin Validador de Regras PostGIS iniciado.", Qgis.Info)
    
    def _connect_signals(self):
        """Conecta os sinais da interface."""
        # Conexões
        self.cmbSelectDatabase.currentIndexChanged.connect(self._on_connection_changed)
        self.btnCreateConnection.clicked.connect(self._open_manage_connections_dialog)
        
        # Schemas e funções
        self.cmbSchema.currentIndexChanged.connect(self._on_schema_changed)
        self.cmbFunction.currentIndexChanged.connect(self._on_function_changed)
        
        # Execução
        self.btnPlay.clicked.connect(self._execute_function)
        self.btnStop.clicked.connect(self._stop_execution)
        
        # Logs
        self.btnClearLog.clicked.connect(self._clear_log)
        self.btnCopyLog.clicked.connect(self._copy_log)
        self.btnExportCsv.clicked.connect(self._export_csv)
        self.btnTutorial.clicked.connect(self._open_tutorial)
    
    def _load_connections(self):
        """Carrega as conexões disponíveis no combo."""
        self.cmbSelectDatabase.clear()
        self.cmbSelectDatabase.addItem("Selecionar banco de dados", None)
        
        connections = self.connection_service.get_all_connections()
        default_connection_info = self.connection_service.get_default_connection_info()
        
        default_index = 0
        for i, connection in enumerate(connections, 1):
            self.cmbSelectDatabase.addItem(connection['name'], connection)
            
            # Se é a conexão padrão, marca para seleção
            if (default_connection_info and 
                connection['name'] == default_connection_info['name']):
                default_index = i
        
        # Seleciona a conexão padrão
        if default_index > 0:
            self.cmbSelectDatabase.setCurrentIndex(default_index)
            self._log(f"Conexão padrão '{default_connection_info['name']}' selecionada automaticamente.", Qgis.Info)
    
    def _on_connection_changed(self):
        """Callback para mudança de conexão."""
        current_data = self.cmbSelectDatabase.currentData()
        
        if current_data is None:
            self.current_connection = None
            self._clear_connection_info()
            self._clear_schemas()
            return
        
        self.current_connection = current_data
        self._update_connection_info()
        self._load_schemas()
    
    def _update_connection_info(self):
        """Atualiza as informações da conexão na interface."""
        if self.current_connection:
            self.lblDbNameValue.setText(self.current_connection['name'])
            self.lblHostValue.setText(f"{self.current_connection['host']}:{self.current_connection['port']}")
        else:
            self._clear_connection_info()
    
    def _clear_connection_info(self):
        """Limpa as informações da conexão."""
        self.lblDbNameValue.setText("N/A")
        self.lblHostValue.setText("N/A")
    
    def _load_schemas(self):
        """Carrega os schemas da conexão atual."""
        if not self.current_connection:
            self._clear_schemas()
            return
        
        self._log(f"Carregando schemas da conexão '{self.current_connection['name']}'...", Qgis.Info)
        
        schemas = self.schema_service.get_schemas(self.current_connection)
        
        self.cmbSchema.clear()
        self.cmbSchema.addItem("Selecione um schema", None)
        
        for schema in schemas:
            self.cmbSchema.addItem(schema, schema)
        
        if schemas:
            self._log(f"Carregados {len(schemas)} schemas.", Qgis.Info)
        else:
            self._log("Nenhum schema encontrado ou erro ao carregar schemas.", Qgis.Warning)
        
        self._clear_functions()
    
    def _clear_schemas(self):
        """Limpa a lista de schemas."""
        self.cmbSchema.clear()
        self.cmbSchema.addItem("Selecione um schema", None)
        self._clear_functions()
    
    def _on_schema_changed(self):
        """Callback para mudança de schema."""
        schema_name = self.cmbSchema.currentData()
        
        if schema_name is None:
            self._clear_functions()
            return
        
        self._load_functions(schema_name)
    
    def _load_functions(self, schema_name: str):
        """
        Carrega as funções do schema selecionado, filtrando as que não possuem parâmetros.
        """
        if not self.current_connection:
            self._clear_functions()
            return
        
        self._log(f"Carregando funções do schema '{schema_name}'...", Qgis.Info)
        
        # get_functions já retorna apenas funções sem parâmetros
        functions = self.function_service.get_functions(self.current_connection, schema_name)
        
        self.cmbFunction.clear()
        if functions:
            for function in functions:
                display_name = f"{function['name']} -> {function['return_type']}"
                self.cmbFunction.addItem(display_name, function)
            self._log(f"Carregadas {len(functions)} funções sem parâmetros.", Qgis.Info)
        else:
            self.cmbFunction.addItem("Nenhuma função sem parâmetros encontrada", None)
            self._log("Nenhuma função sem parâmetros encontrada ou erro ao carregar funções.", Qgis.Warning)
    
    def _clear_functions(self):
        """Limpa a lista de funções."""
        self.cmbFunction.clear()
        self.cmbFunction.addItem("Selecione uma função", None)
    
    def _on_function_changed(self):
        """Callback para mudança de função."""
        function_data = self.cmbFunction.currentData()
        
        if function_data is None:
            return
        
        # Aqui poderia carregar parâmetros da função se necessário
        self._log(f"Função '{function_data['name']}' selecionada.", Qgis.Info)
    
    def _execute_function(self):
        """Executa a função selecionada."""
        # Validações
        if not self.current_connection:
            QMessageBox.warning(self, "Aviso", "Selecione uma conexão antes de executar.")
            return
        
        schema_name = self.cmbSchema.currentData()
        if not schema_name:
            QMessageBox.warning(self, "Aviso", "Selecione um schema antes de executar.")
            return
        
        function_data = self.cmbFunction.currentData()
        if not function_data:
            QMessageBox.warning(self, "Aviso", "Selecione uma função antes de executar.")
            return
        
        function_name = function_data['name']
        
        # Como get_functions já filtra, não precisamos verificar parâmetros aqui novamente
        # Apenas confirmamos que a função selecionada é válida para execução

        # Confirma execução
        reply = QMessageBox.question(
            self,
            "Confirmar Execução",
            f"Executar a função '{schema_name}.{function_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Inicia execução
        self._start_execution(schema_name, function_name)
    
    def _start_execution(self, schema_name: str, function_name: str):
        """Inicia a execução da função em background."""
        # Desabilita controles
        self._set_execution_state(True)
        
        # Limpa logs anteriores
        self.txtLogs.clear()
        self._log(f"Iniciando execução de {schema_name}.{function_name}...", Qgis.Info)
        
        # Cria e inicia task
        self.current_task = FunctionExecutionTask(
            self.current_connection, 
            schema_name, 
            function_name
        )
        
        # Conecta sinais da task
        self.current_task.taskCompleted.connect(self._on_task_completed)
        self.current_task.taskTerminated.connect(self._on_task_terminated)
        
        # Adiciona task ao gerenciador
        QgsApplication.taskManager().addTask(self.current_task)
        
        # Inicia timer
        self.start_time = QDateTime.currentDateTime()
        self.timer.start(1000)
        
        # Mostra progresso
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 0)  # Progresso indeterminado
        self.lblStatus.setText("Executando...")
    
    def _stop_execution(self):
        """Para a execução atual."""
        if self.current_task:
            self.current_task.cancel()
            self._log("Execução cancelada pelo usuário.", Qgis.Warning)
        
        self._finish_execution()
    
    def _on_task_completed(self):
        """
        Callback para task completada com sucesso.
        """
        if self.current_task and self.current_task.result:
            # QgsProviderConnection.executeSql retorna um QgsResult, que é iterável
            # Precisamos consumir o resultado para saber o número de linhas
            result_list = list(self.current_task.result) # Converte para lista para poder contar e iterar novamente
            result_count = len(result_list)
            self._log(f"Função executada com sucesso. Retornou {result_count} registro(s).", Qgis.Info)
            
            # Mostra resultado se houver
            if result_count > 0:
                self._log("Resultado:", Qgis.Info)
                for i, row in enumerate(result_list[:10]):  # Mostra apenas os primeiros 10
                    self._log(f"  Linha {i+1}: {row}", Qgis.Info)
                
                if result_count > 10:
                    self._log(f"  ... e mais {result_count - 10} linha(s)", Qgis.Info)
        else:
            self._log("Função executada, mas não retornou dados ou houve erro interno.", Qgis.Info)
        
        self._finish_execution()
    
    def _on_task_terminated(self):
        """
        Callback para task terminada com erro.
        """
        error_msg = "Erro desconhecido"
        if self.current_task and self.current_task.error_message:
            error_msg = self.current_task.error_message
        
        self._log(f"Erro na execução: {error_msg}", Qgis.Critical)
        self._finish_execution()
    
    def _finish_execution(self):
        """
        Finaliza a execução e restaura a interface.
        """
        # Para timer
        self.timer.stop()
        self.start_time = None
        
        # Esconde progresso
        self.progressBar.setVisible(False)
        self.lblStatus.setText("Pronto")
        self.lblTimer.setText("Timer 00:00:00")
        
        # Reabilita controles
        self._set_execution_state(False)
        
        # Limpa task
        self.current_task = None
    
    def _set_execution_state(self, executing: bool):
        """
        Define o estado da interface durante execução.
        """
        # Controles principais
        self.cmbSelectDatabase.setEnabled(not executing)
        self.btnCreateConnection.setEnabled(not executing)
        self.cmbSchema.setEnabled(not executing)
        self.cmbFunction.setEnabled(not executing)
        self.btnPlay.setEnabled(not executing)
        
        # Botão stop
        self.btnStop.setEnabled(executing)
        
        # Cursor
        if executing:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()
    
    def _update_timer(self):
        """
        Atualiza o timer de execução.
        """
        if self.start_time:
            elapsed = self.start_time.secsTo(QDateTime.currentDateTime())
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.lblTimer.setText(f"Timer {hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def _open_manage_connections_dialog(self):
        """
        Abre o diálogo de gerenciamento de conexões.
        """
        dialog = ManageConnectionsDialog(parent=self)
        dialog.connections_updated.connect(self._load_connections)
        dialog.exec_()
    
    def _log(self, message: str, level: Qgis.MessageLevel = Qgis.Info):
        """
        Adiciona uma mensagem ao log.
        
        Args:
            message: Mensagem a ser logada
            level: Nível da mensagem
        """
        # Adiciona timestamp
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        
        # Define prefixo baseado no nível
        if level == Qgis.Critical:
            prefix = "[ERRO]"
        elif level == Qgis.Warning:
            prefix = "[AVISO]"
        else:
            prefix = "[INFO]"
        
        formatted_message = f"{timestamp} {prefix} {message}"
        
        # Adiciona ao widget de log
        self.txtLogs.append(formatted_message)
        
        # Adiciona ao log do QGIS
        QgsMessageLog.logMessage(message, "ValidadorRegras", level)
    
    def _clear_log(self):
        """
        Limpa o log.
        """
        self.txtLogs.clear()
        self._log("Log limpo.", Qgis.Info)
    
    def _copy_log(self):
        """
        Copia o log para a área de transferência.
        """
        self.txtLogs.selectAll()
        self.txtLogs.copy()
        self._log("Log copiado para a área de transferência.", Qgis.Info)
    
    def _export_csv(self):
        """
        Exporta dados para CSV (funcionalidade futura).
        """
        self._log("Funcionalidade de exportação CSV não implementada.", Qgis.Info)
        QMessageBox.information(self, "Info", "Funcionalidade de exportação CSV será implementada em versão futura.")
    
    def _open_tutorial(self):
        """
        Abre tutorial (funcionalidade futura).
        """
        self._log("Tutorial não implementado.", Qgis.Info)
        QMessageBox.information(self, "Info", "Tutorial será implementado em versão futura.")
    
    def closeEvent(self, event):
        """
        Callback para fechamento do diálogo.
        """
        # Para execução se estiver rodando
        if self.current_task:
            self._stop_execution()
        
        super().closeEvent(event)




