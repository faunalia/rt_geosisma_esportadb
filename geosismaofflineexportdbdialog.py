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
import time, os
from qgis.core import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from dlgSelectProvinciaComuni import Ui_DlgSelectProvinciaComuni
from ExportDBThread import ExportDbThread

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

MESSAGELOG_CLASS = "Exporta DB"

class GeosismaOfflineExportDBDialog(QDialog):

    def __init__(self):
        QDialog.__init__(self)
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
        self.ui.exportDbPushButton.clicked.connect(self.exportDb)
        self.ui.dbListComboBox.currentIndexChanged[str].connect(self.initConnection)
        
        self.comuniModel = QStandardItemModel()
        self.selectedCouniModel = QStandardItemModel()
        
        # manage close running thread
        self.manageClose = False
        self.ui.buttonBox.rejected.connect(self.manageClosecCallback)
        #self.createDB()
        # populate db
        #selectedComuni = [{u'idprovincia': u'045', u'id_istat': u'004', u'toponimo': u'Casola in Lunigiana'}]
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
        self.destinationDBFileName = settings.value("/rt_geosisma_exportadb/destinationDBFileName", "./geosima_geo.sqlite")
        
        self.ui.selectOutFilePushButton.setText( self.destinationDBFileName )
        self.ui.selectOutFilePushButton.clicked.connect(self.selectDestinationDB)
        

    def selectDestinationDB(self):
        currentDir = os.path.dirname(self.destinationDBFileName)
        self.destinationDBFileName = QFileDialog.getOpenFileName(self, "Apri o inserisci un filename", currentDir, "SpatiaLite DB (*.sqlite);; All Files (*)")
        
        self.settings.setValue("/rt_geosisma_exportadb/destinationDBFileName", self.destinationDBFileName)
        

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
        
        (ok, DATABASE_USER, DATABASE_PWD) = QgsCredentials.instance().get( "", DATABASE_USER, DATABASE_PWD, DATABASE_PWD );
        
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


    def exportDb(self):
        if self.selectedCouniModel.rowCount() == 0:
            return
        # get list of selected Comuni
        selectedComuni = []
        for idx in range(self.selectedCouniModel.rowCount()):
            selectedComuni.append( self.selectedCouniModel.item(idx).data() )
        
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            # launch time spending activity
            exportDbThread = ExportDbThread(self.cursor, selectedComuni, self.destinationDBFileName)
            exportDbThread.procDone.connect(self.exportDBTerminated)
            exportDbThread.procMessage.connect(self.exportDBMessage)
            exportDbThread.start()
            
            # update progres bar until termination
            i=0
            while ( not exportDbThread.isFinished() and not self.manageClose ):
                self.ui.progressBar.setValue(i)
                i = (i % 100)+1
                # necessary to process events, otherwise they are processed all toghether at the end
                qApp.processEvents()
                time.sleep(0.1)
            
            # check if to manage thread closing
            if self.manageClose:
                self.ui.logLabel.setText("Terminando l'export... attendere")
                exportDbThread.smoothlyStop()
            
            while ( exportDbThread.isRunning() ):
                qApp.processEvents()
                time.sleep(0.1)
                continue;
            
            QApplication.restoreOverrideCursor()
            
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "", "Export fallito. Verifica la finestra di Log")
            raise e

    def exportDBMessage(self, message, messagetype):
        QgsMessageLog.logMessage(message, MESSAGELOG_CLASS, messagetype)
        self.ui.logLabel.setText(message)
        
    def exportDBTerminated(self, val):
        self.terminatedProcess = val
        
        if self.manageClose:
            return
        
        if self.terminatedProcess:
            self.ui.progressBar.setValue(100)
            self.ui.logLabel.setText("")
            QMessageBox.information(self, "", "Export avvenuto con successo")
        else:
            QMessageBox.critical(self, "", "Export fallito. Verifica la finestra di Log")

    def manageClosecCallback(self):
        self.manageClose = True
