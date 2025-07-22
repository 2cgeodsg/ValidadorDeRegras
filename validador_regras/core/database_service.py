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
from typing import List, Dict, Optional, Tuple
from qgis.core import (
    QgsSettings, QgsDataSourceUri, QgsProviderRegistry, 
    QgsMessageLog, Qgis, QgsTask, QgsApplication
)
from PyQt5.QtCore import QObject, pyqtSignal

class DatabaseConnectionService:
    """
    Serviço para gerenciar conexões de banco de dados PostGIS.
    Responsabilidade única: operações de conexão com banco de dados.
    """
    
    SETTINGS_GROUP = "PostgreSQL/connections"
    DEFAULT_CONNECTION_KEY = "validador_regras/default_connection"
    
    def __init__(self):
        self.settings = QgsSettings()
        self.provider_registry = QgsProviderRegistry.instance()
    
    def get_default_connection_info(self) -> Optional[Dict[str, str]]:
        """
        Retorna informações da conexão padrão.
        
        Returns:
            Dicionário com informações da conexão ou None se não definida
        """
        default_name = self.settings.value(self.DEFAULT_CONNECTION_KEY)
        if not default_name:
            return None
        
        self.settings.beginGroup(f"{self.SETTINGS_GROUP}/{default_name}")
        
        try:
            connection_info = {
                'name': default_name,
                'host': self.settings.value('host', ''),
                'port': self.settings.value('port', '5432'),
                'database': self.settings.value('database', ''),
                'username': self.settings.value('username', ''),
                'password': self.settings.value('password', ''),
                'service': self.settings.value('service', ''),
                'sslmode': self.settings.value('sslmode', 'prefer'),
            }
            return connection_info
        finally:
            self.settings.endGroup()
    
    def get_all_connections(self) -> List[Dict[str, str]]:
        """
        Retorna todas as conexões PostGIS disponíveis.
        
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
                    'sslmode': self.settings.value('sslmode', 'prefer'),
                }
                connections.append(connection_info)
                self.settings.endGroup()
        finally:
            self.settings.endGroup()
        
        return connections
    
    def create_connection(self, connection_info: Dict[str, str]):
        """
        Cria uma conexão de banco de dados usando QgsDataSourceUri.
        
        Args:
            connection_info: Dicionário com informações da conexão
            
        Returns:
            Objeto de conexão ou None se falhou
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
            
            # Cria conexão usando o provider PostgreSQL
            provider = self.provider_registry.providerMetadata('postgres')
            if provider:
                return provider.createConnection(uri.uri(), {})
            
            return None
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Erro ao criar conexão: {e}", 
                "ValidadorRegras", 
                Qgis.Critical
            )
            return None


class SchemaService:
    """
    Serviço para operações relacionadas a schemas.
    Responsabilidade única: gerenciar schemas do banco de dados.
    """
    
    def __init__(self, connection_service: DatabaseConnectionService):
        self.connection_service = connection_service
    
    def get_schemas(self, connection_info: Dict[str, str]) -> List[str]:
        """
        Lista todos os schemas disponíveis na conexão.
        
        Args:
            connection_info: Informações da conexão
            
        Returns:
            Lista de nomes de schemas
        """
        try:
            conn = self.connection_service.create_connection(connection_info)
            if not conn:
                return []
            
            query = """
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY schema_name
            """
            
            result = conn.executeSql(query)
            schemas = [row[0] for row in result]
            
            QgsMessageLog.logMessage(
                f"Encontrados {len(schemas)} schemas na conexão '{connection_info['name']}'", 
                "ValidadorRegras", 
                Qgis.Info
            )
            
            return schemas
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Erro ao listar schemas: {e}", 
                "ValidadorRegras", 
                Qgis.Critical
            )
            return []

class FunctionService:
    """
    Serviço para operações relacionadas a funções (stored procedures).
    Responsabilidade única: gerenciar funções do banco de dados.
    """

    def __init__(self, connection_service: DatabaseConnectionService = None):
        # Se quem instanciar não passar um DatabaseConnectionService, criamos um interno
        self.connection_service = connection_service or DatabaseConnectionService()

    def get_functions(self, connection_info: Dict[str, str], schema_name: str) -> List[Dict[str, str]]:
        conn = self.connection_service.create_connection(connection_info)
        if not conn:
            QgsMessageLog.logMessage(
                "[FunctionService] sem conexão", "ValidadorRegras", Qgis.Critical
            )
            return []

        # Monta a SQL incluindo o schema diretamente na string
        sql = f"""
            SELECT r.routine_name, r.data_type
            FROM information_schema.routines AS r
            WHERE r.routine_schema = '{schema_name}'
              AND r.routine_type = 'FUNCTION'
            ORDER BY r.routine_name
        """
        try:
            rows = list(conn.executeSql(sql))  # sem segundo argumento
            QgsMessageLog.logMessage(
                f"[DEBUG] routines retornou {len(rows)} linhas", "ValidadorRegras", Qgis.Info
            )
            return [{'name': n, 'return_type': r or 'void'} for n, r in rows]
        except Exception as e:
            QgsMessageLog.logMessage(
                f"[DEBUG] erro ao listar routines: {e}", "ValidadorRegras", Qgis.Critical
            )
            return []


    def _has_parameters(self, conn, schema_name: str, specific_name: str) -> bool:
        """
        Retorna True se a função tiver parâmetros IN ou INOUT.
        """
        sql = """
            SELECT COUNT(*)
            FROM information_schema.parameters
            WHERE specific_schema = ?
              AND specific_name = ?
              AND parameter_mode IN ('IN','INOUT')
        """
        try:
            row = next(conn.executeSql(sql, [schema_name, specific_name]), (0,))
            return row[0] > 0
        except Exception as e:
            QgsMessageLog.logMessage(
                f"[FunctionService] erro ao verificar parâmetros: {e}",
                "ValidadorRegras", Qgis.Critical
            )
            # Em caso de erro, assume que há parâmetros (evita listar funções com erro)
            return True

    def get_function_parameters(self, connection_info: Dict[str, str], schema_name: str, specific_name: str) -> List[Dict[str, str]]:
        """
        Obtém os parâmetros de uma função específica usando specific_name.
        """
        conn = self.connection_service.create_connection(connection_info)
        if not conn:
            return []

        sql = """
            SELECT
                parameter_name,
                data_type,
                parameter_mode,
                ordinal_position
            FROM information_schema.parameters
            WHERE specific_schema = ?
              AND specific_name = ?
            ORDER BY ordinal_position
        """
        try:
            params = []
            for name, dtype, mode, pos in conn.executeSql(sql, [schema_name, specific_name]):
                if mode in ('IN', 'INOUT'):
                    params.append({
                        'name': name or f'param_{pos}',
                        'type': dtype,
                        'mode': mode,
                        'position': pos
                    })
            return params
        except Exception as e:
            QgsMessageLog.logMessage(
                f"[FunctionService] erro ao carregar parâmetros: {e}",
                "ValidadorRegras", Qgis.Critical
            )
            return []


class FunctionExecutionTask(QgsTask):
    """
    Task para execução de funções em background.
    Responsabilidade única: executar funções sem bloquear a interface.
    """
    
    def __init__(self, connection_info: Dict[str, str], schema_name: str, function_name: str, parameters: List = None):
        super().__init__(f"Executando função {schema_name}.{function_name}", QgsTask.CanCancel)
        self.connection_info = connection_info
        self.schema_name = schema_name
        self.function_name = function_name
        self.parameters = parameters or []
        self.result = None
        self.error_message = None
    
    def run(self) -> bool:
        try:
            conn = DatabaseConnectionService().create_connection(self.connection_info)
            if not conn:
                self.error_message = "Falha ao conectar com o banco de dados"
                return False

            # Se houver parâmetros, injeta-os na SQL
            if self.parameters:
                # Escapa cada valor (ex.: strings entre aspas simples)
                vals = []
                for v in self.parameters:
                    if isinstance(v, str):
                        valor_escapado = v.replace("'", "''")
                        vals.append("'" + valor_escapado + "'")
                    else:
                        vals.append(str(v))
                args = ", ".join(vals)
                query = f"SELECT {self.schema_name}.{self.function_name}({args})"
                # sem binding
                result = conn.executeSql(query)
            else:
                # sem parâmetros, SQL simples
                query = f"SELECT {self.schema_name}.{self.function_name}()"
                result = conn.executeSql(query)

            self.result = list(result)
            QgsMessageLog.logMessage(
                f"Função {self.schema_name}.{self.function_name} executada com sucesso",
                "ValidadorRegras", Qgis.Info
            )
            return True

        except Exception as e:
            self.error_message = str(e)
            QgsMessageLog.logMessage(
                f"Erro ao executar função {self.schema_name}.{self.function_name}: {e}",
                "ValidadorRegras", Qgis.Critical
            )
            return False
    
    def finished(self, result: bool):
        """
        Callback chamado quando a task termina.
        
        Args:
            result: True se executada com sucesso, False caso contrário
        """
        if result:
            QgsMessageLog.logMessage(
                f"Task de execução da função {self.schema_name}.{self.function_name} concluída", 
                "ValidadorRegras", 
                Qgis.Info
            )
        else:
            QgsMessageLog.logMessage(
                f"Task de execução da função {self.schema_name}.{self.function_name} falhou: {self.error_message}", 
                "ValidadorRegras", 
                Qgis.Critical
            )



