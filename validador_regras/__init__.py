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
import sys


def classFactory(iface):
    """
    :param iface: interface do QGIS fornecida pelo framework
    :type iface: QgisInterface
    :return: instância de ValidadorRegrasPlugin
    """
    # Garante que o diretório do plugin está no sys.path
    plugin_dir = os.path.dirname(__file__)
    if plugin_dir not in sys.path:
        sys.path.insert(0, plugin_dir)

    # Importa a classe principal (nome exato em main_plugin.py)
    from .main_plugin import ValidadorRegrasPlugin

    # Retorna a instância do plugin
    return ValidadorRegrasPlugin(iface)
