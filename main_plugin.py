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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsMessageLog, Qgis
import os.path

from .ui.main_dialog import MainDialog
import resources_rc

class ValidadorRegrasPlugin:
    """
    Plugin principal do Validador de Regras PostGIS.
    Responsabilidade única: gerenciar o ciclo de vida do plugin.
    """

    def __init__(self, iface):
        """
        Inicializa o plugin.
        
        Args:
            iface: Interface do QGIS
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        # Inicializa locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            f'ValidadorRegras_{locale}.qm'
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declara variáveis de instância
        self.actions = []
        self.menu = self.tr('&Validador de Regras PostGIS')
        self.toolbar = self.iface.addToolBar('ValidadorRegras')
        self.toolbar.setObjectName('ValidadorRegras')
        
        # Diálogo principal
        self.main_dialog = None

    def tr(self, message):
        """
        Traduz uma string usando Qt translation API.
        
        Args:
            message: String a ser traduzida
            
        Returns:
            String traduzida
        """
        return QCoreApplication.translate('ValidadorRegras', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None
    ):
        """
        Adiciona uma ação à toolbar e/ou menu.
        
        Args:
            icon_path: Caminho para o ícone
            text: Texto da ação
            callback: Função callback
            enabled_flag: Se a ação está habilitada
            add_to_menu: Se adiciona ao menu
            add_to_toolbar: Se adiciona à toolbar
            status_tip: Dica de status
            whats_this: Texto de ajuda
            parent: Widget pai
            
        Returns:
            QAction criada
        """
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        """
        Cria a interface gráfica do plugin.
        """
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        
        self.add_action(
            icon_path,
            text=self.tr('Validador de Regras PostGIS'),
            callback=self.run,
            parent=self.iface.mainWindow(),
            status_tip=self.tr('Executa o Validador de Regras PostGIS'),
            whats_this=self.tr('Plugin para validação de regras em bancos PostGIS')
        )
        
        QgsMessageLog.logMessage(
            "Plugin Validador de Regras PostGIS carregado com sucesso.", 
            "ValidadorRegras", 
            Qgis.Info
        )

    def unload(self):
        """
        Remove o plugin da interface do QGIS.
        """
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr('&Validador de Regras PostGIS'),
                action
            )
            self.iface.removeToolBarIcon(action)
        
        # Remove a toolbar
        del self.toolbar
        
        # Fecha o diálogo se estiver aberto
        if self.main_dialog:
            self.main_dialog.close()
            self.main_dialog = None
        
        QgsMessageLog.logMessage(
            "Plugin Validador de Regras PostGIS descarregado.", 
            "ValidadorRegras", 
            Qgis.Info
        )

    def run(self):
        """
        Executa o plugin.
        """
        try:
            # Cria o diálogo se não existir
            if self.main_dialog is None:
                self.main_dialog = MainDialog()
            
            # Mostra o diálogo
            self.main_dialog.show()
            
            # Traz para frente
            self.main_dialog.raise_()
            self.main_dialog.activateWindow()
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Erro ao executar o plugin: {e}", 
                "ValidadorRegras", 
                Qgis.Critical
            )
            
            # Tenta recriar o diálogo em caso de erro
            self.main_dialog = None
            try:
                self.main_dialog = MainDialog()
                self.main_dialog.show()
            except Exception as e2:
                QgsMessageLog.logMessage(
                    f"Erro crítico ao recriar diálogo: {e2}", 
                    "ValidadorRegras", 
                    Qgis.Critical
                )

