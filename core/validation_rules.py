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
import psycopg2
from qgis.core import QgsMessageLog, Qgis

from .interfaces import IValidationRule
from .connection_config import ConnectionConfig

class DiscoverMuvdFunctionsRule(IValidationRule):
    """
    Regra que lista todas as funções existentes no schema 'muvd'.
    Se o schema não existir, registra um erro específico.
    """
    def __init__(self):
        # será preenchido após execução bem‑sucedida
        self.last_functions: list[str] = []

    def name(self) -> str:
        return "Descobrir Funções MUVD"

    def description(self) -> str:
        return "Verifica e lista todas as funções disponíveis no schema 'muvd'."

    def run(
        self,
        connection_config: ConnectionConfig,
        log_callback=None,
        progress_callback=None
    ) -> bool:
        # 1. Log de início
        start_msg = f"Iniciando verificação de funções em 'muvd' para '{connection_config.name}'..."
        if log_callback: log_callback(start_msg, Qgis.Info)

        # 2. Monta string de conexão, usando atributo .database se existir
        dbname = getattr(connection_config, "database", connection_config.name)
        conn_str = (
            f"host={connection_config.host} "
            f"port={connection_config.port} "
            f"dbname={dbname} "
            f"user={connection_config.user} "
            f"password={connection_config.password}"
        )

        try:
            with psycopg2.connect(conn_str, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    # 3. Verifica existência do schema 'muvd'
                    cur.execute(
                        "SELECT 1 "
                        "FROM information_schema.schemata "
                        "WHERE schema_name = 'muvd';"
                    )
                    if not cur.fetchone():
                        msg = "Schema 'muvd' não encontrado."
                        QgsMessageLog.logMessage(msg, "ValidationRules", Qgis.Critical)
                        if log_callback: log_callback(msg, Qgis.Critical)
                        if progress_callback: progress_callback(0, "Schema não existe")
                        return False

                    # 4. Lista todas as funções do schema
                    cur.execute(
                        "SELECT routine_name "
                        "FROM information_schema.routines "
                        "WHERE specific_schema = 'muvd' "
                        "ORDER BY routine_name;"
                    )
                    funcs = [row[0] for row in cur.fetchall()]
                    self.last_functions = funcs

            # 5. Trata caso sem funções
            if not self.last_functions:
                msg = "Nenhuma função encontrada em 'muvd'."
                QgsMessageLog.logMessage(msg, "ValidationRules", Qgis.Critical)
                if log_callback: log_callback(msg, Qgis.Critical)
                if progress_callback: progress_callback(0, "Sem funções")
                return False

            # 6. Reporta progresso e logs para cada função
            total = len(self.last_functions)
            for idx, fn in enumerate(self.last_functions, start=1):
                percent = int(idx * 100 / total)
                if progress_callback: progress_callback(percent, fn)
                if log_callback: log_callback(f"{idx}/{total}: função '{fn}' encontrada.", Qgis.Info)

            # 7. Conclusão com sucesso
            ok_msg = f"Listagem concluída: {total} funções encontradas em 'muvd'."
            QgsMessageLog.logMessage(ok_msg, "ValidationRules", Qgis.Info)
            if log_callback: log_callback(ok_msg, Qgis.Info)
            if progress_callback: progress_callback(100, "Concluído")
            return True

        except psycopg2.OperationalError as e:
            err = f"Erro de conexão ao verificar 'muvd': {e}"
            QgsMessageLog.logMessage(err, "ValidationRules", Qgis.Critical)
            if log_callback: log_callback(err, Qgis.Critical)
            if progress_callback: progress_callback(0, "Erro de Conexão")
            return False

        except Exception as e:
            err = f"Erro inesperado ao verificar funções MUVD: {e}"
            QgsMessageLog.logMessage(err, "ValidationRules", Qgis.Critical)
            if log_callback: log_callback(err, Qgis.Critical)
            if progress_callback: progress_callback(0, "Erro Inesperado")
            return False



class ExecuteMuvdFunctionRule(IValidationRule):
    """
    Regra que executa uma função definida no schema 'muvd'.
    Recebe o nome da função como parâmetro.
    """
    def __init__(self, function_name: str):
        self.function_name = function_name

    def name(self) -> str:
        return f"Executar {self.function_name}"

    def description(self) -> str:
        return f"Executa a função '{self.function_name}' dentro do schema 'muvd'."

    def run(
        self,
        connection_config: ConnectionConfig,
        log_callback=None,
        progress_callback=None
    ) -> bool:
        if log_callback:
            log_callback(f"Iniciando execução de '{self.function_name}' em '{connection_config.name}'...")

        conn_str = (
            f"host={connection_config.host}"
            f" port={connection_config.port}"
            f" dbname={connection_config.name}"
            f" user={connection_config.user}"
            f" password={connection_config.password}"
        )

        try:
            with psycopg2.connect(conn_str, connect_timeout=30) as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT muvd.{self.function_name}();")
                    result = cur.fetchone()

            success = True
            msg = f"Função '{self.function_name}' executada com sucesso. Retorno: {result}"  
            QgsMessageLog.logMessage(msg, "ValidationRules", Qgis.Info)
            if log_callback: log_callback(msg)
            if progress_callback: progress_callback(100, "Concluído")
            return success

        except psycopg2.OperationalError as e:
            err = f"Erro de conexão ao executar '{self.function_name}': {e}"
            QgsMessageLog.logMessage(err, "ValidationRules", Qgis.Critical)
            if log_callback: log_callback(err)
            if progress_callback: progress_callback(0, "Erro de Conexão")
            return False

        except Exception as e:
            err = f"Erro ao executar '{self.function_name}': {e}"
            QgsMessageLog.logMessage(err, "ValidationRules", Qgis.Critical)
            if log_callback: log_callback(err)
            if progress_callback: progress_callback(0, "Erro Inesperado")
            return False
