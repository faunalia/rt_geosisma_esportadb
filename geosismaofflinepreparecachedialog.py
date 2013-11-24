# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeosismaOfflineExportDBDialog
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
"""
import time, os, inspect, traceback
from qgis.core import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from dlgSelectProvinciaComuni import Ui_DlgSelectProvinciaComuni
from ExportDBThread import ExportDBThread
from DlgWmsLayersManager import DlgWmsLayersManager, WmsLayersBridge

# PostGIS import
import psycopg2
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
# PostGIS DB settings
DATABASE_HOST = "localhost"
DATABASE_NAME = "geosisma_geo"
DATABASE_SCHEMA = "public"
DATABASE_PORT = "5434"
DATABASE_USER = "postgres"
DATABASE_PWD = "postgres"
# SpatiaLite imports
from pyspatialite import dbapi2 as db
SPLITE_DATABASE_NAME = DATABASE_NAME+".sqlite"

CACHE_DB_SUBDIR = "dbs"
CACHE_LAYERS_SUBDIRS = "layers"

MESSAGELOG_CLASS = "rt_geosisma_preparacache"
GEOSISMA_OFFLINE_PLUGIN_NAME = "rt_geosisma_offline"
DEFAULT_SRID = 3003
# DEFAULT_SRID = 32632

class GeosismaOfflinePrepareCacheDialog(QDialog):

    RLID_WMS = {} # probably unuseful
    instance = None
    
    # signals
    exportDbDone = pyqtSignal(bool)
    prepareCacheDone = pyqtSignal(bool)

    def __init__(self, iface):
        QDialog.__init__(self)
        GeosismaOfflinePrepareCacheDialog.instance = self
        self.iface = iface
        self.canvas = iface.mapCanvas()
        # Set up the user interface from Designer.
        self.settings = QSettings()
        
        self.ui = Ui_DlgSelectProvinciaComuni()
        self.ui.setupUi(self)
        self.initGUI()
        # init gui
        
        #self.initConnection(1)
        #self.initProvincie()
    
        self.ui.provinceComboBox.currentIndexChanged.connect(self.selectComuni)
        self.ui.addPushButton.clicked.connect(self.addComuneToSlected)
        self.ui.removePushButton.clicked.connect(self.removeComuneFromSelected)
        self.ui.prepareDataPushButton.clicked.connect(self.exportDB)
        self.ui.dbListComboBox.currentIndexChanged[str].connect(self.initConnection)
        self.exportDbDone.connect(self.prepareCache)
        
        self.comuniModel = QStandardItemModel()
        self.selectedCouniModel = QStandardItemModel()
        
        # manage close running thread
        self.manageClose = False
        self.ui.buttonBox.rejected.connect(self.manageClosecCallback)
        #self.createDB()
        # populate db
#         selectedComuni = [{u'idprovincia': u'045', u'id_istat': u'004', u'toponimo': u'Casola in Lunigiana'}]
#         item = QStandardItem( selectedComuni[0]["toponimo"] )
#         item.setData( selectedComuni[0]  )
#         self.selectedCouniModel.appendRow(item)
#         self.ui.selectedComuniListView.setModel(self.selectedCouniModel)
        #self.populateDB(selectedComuni)
        #self.ui.comuniListView.setSelectionMode(QAbstractItemView.MultiSelection)
        #self.ui.selectedComuniListView.setSelectionMode(QAbstractItemView.MultiSelection)

    def initGUI(self):
        # add configured postgis connection list
        settings = QSettings()
        settings.beginGroup( "/PostgreSQL/connections" );
        dbs = ["Seleziona un DB"] + settings.childGroups()
        self.ui.dbListComboBox.blockSignals(True)
        self.ui.dbListComboBox.addItems( dbs )
        self.ui.dbListComboBox.blockSignals(False)
        
        # add event to connect db
        
        # add event to select destination db
        settings = QSettings()
        plugin_path = os.path.dirname(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
        #self.destinationDBFileName = os.path.join(plugin_path, GEOSISMA_OFFLINE_PLUGIN_NAME, "dbs", DATABASE_NAME+".sqlite")
        self.destinationPathName = os.path.join(plugin_path, GEOSISMA_OFFLINE_PLUGIN_NAME, "offlinedata")
        self.destinationPathName = settings.value("/rt_geosisma_preparacache/destinationPathName", self.destinationPathName)
        
        self.ui.selectOutPathPushButton.setText( self.destinationPathName )
        self.ui.selectOutPathPushButton.clicked.connect(self.selectDestinationsPath)

        # SET outs
        self.destinationDBFileName = os.path.join(self.destinationPathName, CACHE_DB_SUBDIR, SPLITE_DATABASE_NAME)
        self.destinationCachePath = os.path.join(self.destinationPathName, CACHE_LAYERS_SUBDIRS, SPLITE_DATABASE_NAME)

    def selectDestinationsPath(self):
        self.destinationPathName = QFileDialog.getExistingDirectory(self, self.tr("Seleziona un Path"), self.destinationPathName)
        
        self.settings.setValue("/rt_geosisma_preparacache/destinationPathName", self.destinationPathName)
        self.destinationDBFileName = os.path.join(self.destinationPathName, CACHE_DB_SUBDIR, SPLITE_DATABASE_NAME)
        
        # set layer cache path
        self.destinationCachePath = os.path.join(self.destinationPathName, CACHE_LAYERS_SUBDIRS, SPLITE_DATABASE_NAME)
        WmsLayersBridge.setPathToCache(self.destinationCachePath)


    def initConnection(self, dbname):
        try:
            self.connection.close()
        except:
            pass
        
        # get connection data
        root = "/PostgreSQL/connections/"+dbname+"/"
        DATABASE_HOST = self.settings.value(root+"host", "localhost")
        DATABASE_NAME = self.settings.value(root+"database", "geosisma_geo")
        DATABASE_SCHEMA = "public"
        DATABASE_PORT = self.settings.value(root+"port", "5342")
        DATABASE_USER = self.settings.value(root+"username", "postgres")
        DATABASE_PWD = self.settings.value(root+"password", "")
        
        (ok, DATABASE_USER, DATABASE_PWD) = QgsCredentials.instance().get( "", DATABASE_USER, DATABASE_PWD );
        
        self.uri = QgsDataSourceURI()
        self.uri.setConnection(DATABASE_HOST, DATABASE_PORT, DATABASE_NAME, DATABASE_USER, DATABASE_PWD)
        
        # connect
        self.connection = psycopg2.connect( self.uri.connectionInfo().encode('utf-8') )
        self.cursor = self.connection.cursor()
        
        # load province
        self.initProvincie()


    def initProvincie(self):
        sqlquery = "SELECT id_istat, toponimo, idregione, sigla FROM istat_province"
        self.cursor.execute(sqlquery)
        colnames = [desc[0] for desc in self.cursor.description]
        for provincia in self.cursor.fetchall():
            # create a dict for this provincia
            provinciaDict = {k:v for k,v in zip(colnames, provincia)}
            # add to provinceComboBox
            prov = provincia[colnames.index("toponimo")] + " ("+ provincia[colnames.index("sigla")] +")"
            self.ui.provinceComboBox.addItem(prov, provinciaDict)
        return


    def selectComuni(self, index):
        provinciaDict = self.ui.provinceComboBox.itemData(index)
        istat_provincia = provinciaDict["id_istat"]
        sqlquery = "SELECT id_istat, toponimo, idprovincia FROM istat_comuni WHERE idprovincia = '%s'" % istat_provincia
        self.cursor.execute(sqlquery)
        
        self.comuniModel.clear()
        colnames = [desc[0] for desc in self.cursor.description]
        for comuni in self.cursor.fetchall():
            # create a dict for this provincia
            comuniDict = {k:v for k,v in zip(colnames, comuni)}
            # add in the Comuni list
            item = QStandardItem( comuni[colnames.index("toponimo")] )
            item.setData( comuniDict )
            self.comuniModel.appendRow(item)
        self.comuniModel.sort(0)
        self.ui.comuniListView.setModel(self.comuniModel)
        return


    def addComuneToSlected(self):
        selectedIdx = self.ui.comuniListView.selectedIndexes()
        for idx in selectedIdx:
            item = QStandardItem( self.comuniModel.itemFromIndex(idx) )
            # check if item is already present
            found = False
            for row in range(self.selectedCouniModel.rowCount()):
                if (item.text() == self.selectedCouniModel.item(row).text()):
                    found = True
            if (not found):
                self.selectedCouniModel.appendRow( item )
            self.comuniModel.removeRow(idx.row())
        # show updated elements
        self.comuniModel.sort(0)
        self.selectedCouniModel.sort(0)
        self.ui.comuniListView.setModel(self.comuniModel)
        self.ui.selectedComuniListView.setModel(self.selectedCouniModel)
        return


    def removeComuneFromSelected(self):
        selectedIdx = self.ui.selectedComuniListView.selectedIndexes()
        for idx in selectedIdx:
            item = QStandardItem( self.selectedCouniModel.itemFromIndex(idx) )
            # check if item is already present
            found = False
            for row in range(self.comuniModel.rowCount()):
                if (item.text() == self.comuniModel.item(row).text()):
                    found = True
            if (not found):
                self.comuniModel.appendRow( item )
            self.selectedCouniModel.removeRow(idx.row())
        # show updated elements
        self.comuniModel.sort(0)
        self.selectedCouniModel.sort(0)
        self.ui.selectedComuniListView.setModel(self.selectedCouniModel)
        self.ui.comuniListView.setModel(self.comuniModel)
        return


    def exportDb___(self):
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.exportDB()
            if not self.terminatedExportDb:
                return
            self.prepareCache()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "", self.tr("Preparazioen dati fallita. Verifica la finestra di Log"))
            raise e
        finally:
            QApplication.restoreOverrideCursor()

    def reloadCrs(self):
        self.srid = self.getSridFromConf()
        srs = QgsCoordinateReferenceSystem( self.srid, QgsCoordinateReferenceSystem.EpsgCrsId )
        renderer = self.canvas.mapRenderer()
        self._setRendererCrs(renderer, srs)
        
        print "srid = ",self.srid
        print "mapUnits = ", srs.mapUnits()
        
        renderer.setMapUnits( srs.mapUnits() if srs.mapUnits() != QGis.UnknownUnit else QGis.Meters )


    def exportDB(self):
        print "started exportDB"

        if self.manageClose:
            return
        
        if self.selectedCouniModel.rowCount() == 0:
            return
        # get list of selected Comuni
        selectedComuni = []
        for idx in range(self.selectedCouniModel.rowCount()):
            selectedComuni.append( self.selectedCouniModel.item(idx).data() )
        
        self.showMessage(self.tr("Esporta base di dati geografica %s" % self.destinationDBFileName), QgsMessageLog.INFO)
        
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)

            # launch time spending activity
            exportDBThread = ExportDBThread(self.cursor, selectedComuni, self.destinationDBFileName)
            exportDBThread.procDone.connect(self.exportDBTerminated)
            exportDBThread.procMessage.connect(self.showMessage)
            exportDBThread.start()
             
            # update progres bar until termination
            i=0
            while ( not exportDBThread.isFinished() and not self.manageClose ):
                self.ui.progressBar.setValue(i)
                i = (i % 100)+1
                # necessary to process events, otherwise they are processed all toghether at the end
                qApp.processEvents()
                time.sleep(0.1)
             
            # check if to manage thread closing
            if self.manageClose:
                self.ui.logLabel.setText("Terminando l'export... attendere")
                exportDBThread.smoothlyStop()
             
            while ( exportDBThread.isRunning() ):
                qApp.processEvents()
                time.sleep(0.1)
                continue;
            
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "", self.tr("ExportDB fallito! Verifica la finestra di Log"))
            QApplication.setOverrideCursor(Qt.WaitCursor)
            raise e
        finally:
            QApplication.restoreOverrideCursor()
        
        print "terminated exportDB"


    def prepareCache(self, success=True):
        ''' prepare cache reuse DlgWmsLayersManager from rt_omero plugin with just slight modifications '''
        print "prepareCache"

        if not success:
            return
        if self.manageClose:
            return

        if self.selectedCouniModel.rowCount() == 0:
            return
        # get list of selected Comuni
        selectedComuni = []
        for idx in range(self.selectedCouniModel.rowCount()):
            selectedComuni.append( self.selectedCouniModel.item(idx).data() )
        
        # disabilita le icone per i layer raster
        settings = QSettings()
        prevRasterIcons = settings.value("/qgis/createRasterLegendIcons", True)
        settings.setValue("/qgis/createRasterLegendIcons", False)

        # disabilita il rendering
        prevRenderFlag = self.canvas.renderFlag()
        self.canvas.setRenderFlag( False )
        
        # get the CRS from CONF and set the canvas CRS
        #self.reloadCrs()
        
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            # load layers
            #self.offlineMode = False
            self.wmsLayersBridge = WmsLayersBridge(self.iface, self.showMessage)
            firstTime = True
            if not DlgWmsLayersManager.loadWmsLayers(firstTime): # static method
                raise Exception("RT Geosisma", "Impossibile caricare i layer richiesti dal database selezionato")
            
            # reload the canvas CRS, the first added layer could have changed it
            #self.reloadCrs()
            
            # save layers in cache
            firstTime = False
            #self.offlineMode = True
            
            # get extent (BBOX) of the selected comuni from the exported DB
            # this step seems doesn't have effect :(
            sridextent = self.getExtentAndSrid()
            if sridextent != None:
                srid, xmin, ymin, xmax, ymax = sridextent
                #print "db srid=",srid, "bbox=",xmin, ymin, xmax, ymax
                # trasform bbox in current srid
                rect = QgsRectangle(xmin, ymin, xmax, ymax)
                crsSrc = QgsCoordinateReferenceSystem(srid)    # WGS 84
                crsDest = QgsCoordinateReferenceSystem(DEFAULT_SRID)  # WGS 84 / UTM zone 33N
                xform = QgsCoordinateTransform(crsSrc, crsDest)
                currentRect = xform.transformBoundingBox(rect)
                print "current srid=",DEFAULT_SRID, "bbox=",currentRect.xMinimum(), currentRect.yMinimum(), currentRect.xMaximum(), currentRect.yMaximum()
                # set extent to the selected comuni BBOX
                self.canvas.setExtent(currentRect)
            
            # hide progress bar because it's already present in DlgWmsLayersManager
            self.ui.progressBar.hide()
            wmsManager = DlgWmsLayersManager(self.iface, self.wmsLayersBridge, self)
            wmsManager.exec_()
    
            # reset previous rederer config 
            self.canvas.setRenderFlag( prevRenderFlag )
            # restore the raster legend icons creation
            settings.setValue("/qgis/createRasterLegendIcons", prevRasterIcons)
    
            self.ui.logLabel.setText(self.tr(""))
            QMessageBox.information(self, "", self.tr("Preparazione dati avvenuta con successo"))

        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "", self.tr("Preparazione cache fallita! Verifica la finestra di Log"))
            QApplication.setOverrideCursor(Qt.WaitCursor)
            raise e
        finally:
            QApplication.restoreOverrideCursor()

    def getExtentAndSrid(self):
        
        sqlquery = """
        SELECT
            geometry_columns.srid,
            Min(MbrMinX(the_geom)), Min(MbrMinY(the_geom)),
            Max(MbrMaxX(the_geom)), Max(MbrMaxY(the_geom))
        FROM
            fab_catasto, geometry_columns
        WHERE
            geometry_columns.f_table_name = 'fab_catasto';
        """
        
        spliteconn = db.connect(self.destinationDBFileName)
        rs = spliteconn.cursor().execute(sqlquery)
        rows = rs.fetchall()
        if (rows.__len__() != 1):
            self.showMessage(self.tr("Non riesco a determinare l'extent della tablella fab_catasto"), QgsMessageLog.WARNING)
            return None
            
        return rows[0]


    def showMessage(self, message, messagetype):
        QgsMessageLog.logMessage(message, MESSAGELOG_CLASS, messagetype)
        self.ui.logLabel.setText(message)


    def exportDBTerminated(self, success):
        if self.manageClose:
            return
        
        if success:
            self.ui.progressBar.setValue(100)
            self.ui.logLabel.setText(self.tr("Export del DB avvenuto con successo... preparazione cache. Attendere!"))
            #QMessageBox.information(self, "", self.tr("Export avvenuto con successo"))
        else:
            QMessageBox.critical(self, "", self.tr("Export fallito. Verifica la finestra di Log"))
        
        # notify termination
        self.exportDbDone.emit(success)
        
    def manageClosecCallback(self):
        self.manageClose = True


