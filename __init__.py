# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeosismaOfflineExportDB
                                 A QGIS plugin
 Exporta porzioni del Db PostGis di Geosisma in Spatialite 
                             -------------------
        begin                : 2013-10-21
        copyright            : (C) 2013 by Luigi Pirelli
        email                : luipir@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

def classFactory(iface):
    # load GeosismaOfflineExportDB class from file GeosismaOfflineExportDB
    from geosismaofflinepreparecache import GeosismaOfflinePrepareCache
    return GeosismaOfflinePrepareCache(iface)
