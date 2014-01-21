'''
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Luigi Pirelli (luipir@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
Created on Oct 7, 2013

@author: Luigi Pirelli (luipir@gmail.com)
'''

import os, json, traceback
from collections import OrderedDict
from qgis.core import *
from PyQt4.QtCore import *

# SpatiaLite imports
from pyspatialite import dbapi2 as db
# SpatiaLite DB settings
DATABASE_SRID = 32632 # <- have to match with source DB and cratedb script

class ExportDBThread(QThread):
    
    # signals
    procDone = pyqtSignal(bool)
    procMessage = pyqtSignal(str, int)

    def __init__(self, pgconnection, selectedComuni, outDb):
        QThread.__init__(self)
        self.pgconnection = pgconnection
        self.cursor = pgconnection.cursor()
        self.selectedComuni = selectedComuni
        self.stopThread = False
        self.DATABASE_NAME = os.path.splitext( os.path.basename(outDb) )[0]
        self.DATABASE_OUTNAME = outDb
        self.DATABASE_OUTNAME_SCHEMAFILE = os.path.dirname(os.path.realpath(__file__))+'/schemas/' + self.DATABASE_NAME + ".sql"
        
    def run(self):
        try:
            # create db
            self.createDB()
            # populate db
            self.populateDB(self.selectedComuni)
            # end
            self.procDone.emit(True)
            
        except Exception as e:
            traceback.print_exc()
            self.procDone.emit(False)
            self.procMessage.emit(e.message, QgsMessageLog.CRITICAL)
            raise e


    def smoothlyStop(self):
        self.stopThread = True


    def createDB(self):
        if self.stopThread:
            return
        
        if os.path.exists(self.DATABASE_OUTNAME):
            os.unlink(self.DATABASE_OUTNAME)
        # read 
        geosisma_geo_schema = ""
        with open(self.DATABASE_OUTNAME_SCHEMAFILE, 'r') as fs:
            geosisma_geo_schema += fs.read()
        # connect spatialite db
        conn = db.connect(self.DATABASE_OUTNAME)
        # create DB
        try:
            self.procMessage.emit("Inizializza il DB Spatialite temporaneo", QgsMessageLog.INFO)
            conn.cursor().executescript(geosisma_geo_schema)
        except db.Error as e:
            self.procMessage.emit(e.message, QgsMessageLog.CRITICAL)
            raise e


    def populateDB(self, selectedComuni):
        if self.stopThread:
            return

        # connect spatialite db
        conn = db.connect(self.DATABASE_OUTNAME)
        print self.DATABASE_OUTNAME
        
        
        try:
            # copy tables
            tables = ["istat_regioni", "istat_province", "istat_comuni", "codici_belfiore", "istat_loc_tipi"]
            for table in tables:
                self.copyTable(conn, table)
             
            # copy table with geom
            tables = ["istat_loc"]
            for table in tables:
                self.copyGeomTable(conn, table)
             
            # get fab_catasto poligons only related to selectedComuni
            for comune in selectedComuni:
                print "exporting fields for: ", comune["toponimo"], "..."
                self.copyCatastoPolygons(conn, comune)
            
            # get fab_10k poligons only related to selectedComuni
            for comune in selectedComuni:
                print "exporting fields for: ", comune["toponimo"], "..."
                self.copyFab10kPolygons(conn, comune)
            
            #commit population
            conn.commit()
        except db.Error as e:
            self.procMessage.emit(e.message, QgsMessageLog.CRITICAL)
            raise e


    def copyTable(self, spliteconn, tableName):
        '''Copy a table from PostGIS to Spatialite'''
        if self.stopThread:
            return

        try:
            if (not self.cursor.closed):
                print "close cursor and reopen"
                self.cursor.close()
            self.cursor = self.pgconnection.cursor()
            
            self.procMessage.emit("Copia tabella: "+tableName, QgsMessageLog.INFO)
            # get PostGIS values
            sqlquery = u"SELECT * FROM "+tableName+";"
            self.cursor.execute( sqlquery )
            # create query string
            fields = ['?'] * self.cursor.description.__len__() # create a list of ['?', '?', '?', '?', '?', '?', '?', '?', '?', '?']
            sql = 'INSERT INTO '+tableName+' VALUES '
            sql += "( " + ",".join(fields) + " );"
            # copy on SpatiaLite
            for record in self.cursor.fetchall():
                spliteconn.cursor().execute(sql, record)
                
        except db.Error as e:
            self.procMessage.emit(e.message, QgsMessageLog.CRITICAL)
            raise e


    def copyGeomTable(self, spliteconn, tableName):
        '''Copy a geom table from PostGIS to Spatialite'''
        if self.stopThread:
            return

        # get fab_catasto field types
        # working with OrderedDict to maintaing ordering among fields and values
        try:
            self.procMessage.emit("Copia tabella: "+tableName + ". Attenzione operazione lunga!", QgsMessageLog.INFO)

            records = spliteconn.cursor().execute("PRAGMA table_info("+tableName+")")
            columnNameTypes = {}
            for record in records:
                columnNameTypes[record[1]] = record[2]
        
            # create query
            temp = {k:k for k in columnNameTypes.keys()}
            temp["the_geom"] = "ST_AsText(" + temp["the_geom"] + ")"
            temp = OrderedDict(sorted(temp.items(), key=lambda x:x[0]))
            sqlcolumns = temp.values()
            columnames = temp.keys()
            
            # do postgis query
            sqlquery = "SELECT "+",".join(sqlcolumns) + " "
            sqlquery += "FROM "+ tableName + ";"
            self.cursor.execute( sqlquery )
            self.procMessage.emit("%s: Copiando n: %d records" % (tableName, self.cursor.rowcount), QgsMessageLog.INFO)
        
            # create query string for spatialite
            sql = 'INSERT INTO '+tableName+'(' + ','.join(columnames) + ') VALUES '
            # copy on SpatiaLite
            for record in self.cursor.fetchall():
                # modify geompetry element
                valuesDict = OrderedDict(zip(columnames,record))
                for column in columnames:
                    if column == "the_geom":
                        valuesDict["the_geom"] = "GeomFromText('%s',%d)" % (valuesDict["the_geom"], DATABASE_SRID)
                    else:
                        valuesDict[column] = json.dumps( unicode( valuesDict[column] ) )
                newsql = sql + "(" +",".join( valuesDict.values() ) + ")"
                spliteconn.cursor().execute(newsql)
                
                if self.stopThread:
                    return
                    
        except db.Error as e:
            self.procMessage.emit(e.message, QgsMessageLog.CRITICAL)
            raise e


    def copyCatastoPolygons(self, spliteconn, comuneDict):
        if self.stopThread:
            return
        # get fab_catasto field types
        # working with OrderedDict to maintaing ordering among fields and values
        self.procMessage.emit("Copia tabella fab_catasto per il comune: "+comuneDict["toponimo"] + ". Attenzione operazione lunga!", QgsMessageLog.INFO)
        try:
            records = spliteconn.cursor().execute("PRAGMA table_info(fab_catasto)")
            columnNameTypes = OrderedDict()
            for record in records:
                columnNameTypes[record[1]] = record[2]
            columnNameTypes = OrderedDict( sorted(columnNameTypes.items(), key=lambda x:x[0]) )
        except db.Error as e:
            raise e
        
        # create query
        temp = OrderedDict()
        for k in columnNameTypes.iterkeys():
            temp[str(k)] = "fab_catasto."+str(k)
        temp["the_geom"] = "ST_AsText(" + temp["the_geom"] + ")"

        sqlcolumns = temp.values()
        columnames = columnNameTypes.keys()
        
        sqlquery = "SELECT "+",".join(sqlcolumns) + " "
        sqlquery += """
        FROM 
            public.fab_catasto, 
            public.codici_belfiore, 
            public.istat_comuni
        WHERE 
            fab_catasto.belfiore = codici_belfiore.id AND
            codici_belfiore.id_comune = istat_comuni.id_istat AND
            codici_belfiore.id_provincia = istat_comuni.idprovincia AND
            codici_belfiore.toponimo = istat_comuni.toponimo AND
            istat_comuni.id_istat = '{id_istat}' AND 
            istat_comuni.idprovincia = '{idprovincia}' AND 
            istat_comuni.toponimo = '{toponimo}';
        """.format(**comuneDict)
        
        # query all poligons
        self.cursor.execute( sqlquery )
        self.procMessage.emit(self.tr("fab_catasto: Copiando n: %d records" % self.cursor.rowcount), QgsMessageLog.INFO)
        
        # add record to spatialite db
        for poligons in self.cursor.fetchall():
            # create a dict for this provincia
            valueByName = zip(columnames, poligons)
            poligonsDict = OrderedDict( sorted( valueByName, key=lambda x:x[0] ) )
            # modify values to match spatialite type
            for column in columnames:
                #print column, poligonsDict[column]
                # None values
                if (poligonsDict[column] == None):
                    poligonsDict[column] = ''
                # the_geom values
                if (columnNameTypes[column] == "MULTIPOLYGON"):
                    poligonsDict[column] = "GeomFromText('%s', %d)" % ( poligonsDict[column], DATABASE_SRID)
                    #poligonsDict[column] = "GeomFromText('MULTIPOLYGON(((0 0,10 20,30 40,0 0),(1 1,2 2,3 3,1 1)),((100 100,110 110,120 120,100 100)))',DATABASE_SRID)"
                if (columnNameTypes[column] == "text"):
                    # using json.dumps to create strings without ' or " problems
                    poligonsDict[column] = json.dumps(str(poligonsDict[column]))
                if (columnNameTypes[column] == "real"):
                    poligonsDict[column] = float(poligonsDict[column])
                if (columnNameTypes[column] != "MULTIPOLYGON" and
                    columnNameTypes[column] != "text"):
                    poligonsDict[column] = str(poligonsDict[column])
            # do insert
            sql = 'INSERT INTO fab_catasto ('+ ",".join(columnames) +') VALUES '
            sql += "(" + ",".join(poligonsDict.values()) + ");"
            spliteconn.cursor().execute(sql)
            
            if self.stopThread:
                return

    def copyFab10kPolygons(self, spliteconn, comuneDict):
        if self.stopThread:
            return
        # get fab_catasto field types
        # working with OrderedDict to maintaing ordering among fields and values
        self.procMessage.emit("Copia fab_10k per il comune: "+comuneDict["toponimo"] + ". Attenzione operazione lunga!", QgsMessageLog.INFO)
        try:
            records = spliteconn.cursor().execute("PRAGMA table_info(fab_10k)")
            columnNameTypes = OrderedDict()
            for record in records:
                columnNameTypes[record[1]] = record[2]
            columnNameTypes = OrderedDict( sorted(columnNameTypes.items(), key=lambda x:x[0]) )
        except db.Error as e:
            raise e
        
        # create query
        temp = OrderedDict()
        for k in columnNameTypes.iterkeys():
            temp[str(k)] = str(k)
        temp["the_geom"] = "ST_AsText(" + temp["the_geom"] + ")"

        sqlcolumns = temp.values()
        columnames = columnNameTypes.keys()
        
        sqlquery = "SELECT "+",".join(sqlcolumns) + " "
        sqlquery += """
        FROM 
            fab_10k
        WHERE 
            cod_com = '{id_istat}' AND
            nomemin LIKE '{toponimo}';
        """.format(**comuneDict)
        
        # query all poligons
        self.cursor.execute( sqlquery )
        self.procMessage.emit(self.tr("fab_10k: Copiando n: %d records" % self.cursor.rowcount), QgsMessageLog.INFO)
        
        # add record to spatialite db
        for poligons in self.cursor.fetchall():
            # create a dict for this provincia
            valueByName = zip(columnames, poligons)
            poligonsDict = OrderedDict( sorted( valueByName, key=lambda x:x[0] ) )
            # modify values to match spatialite type
            for column in columnames:
                #print column, poligonsDict[column]
                # None values
                if (poligonsDict[column] == None):
                    poligonsDict[column] = ''
                # the_geom values
                if (columnNameTypes[column] == "MULTIPOLYGON"):
                    poligonsDict[column] = "GeomFromText('%s', %d)" % ( poligonsDict[column], DATABASE_SRID)
                    #poligonsDict[column] = "GeomFromText('MULTIPOLYGON(((0 0,10 20,30 40,0 0),(1 1,2 2,3 3,1 1)),((100 100,110 110,120 120,100 100)))',DATABASE_SRID)"
                if (columnNameTypes[column] == "text"):
                    # using json.dumps to create strings without ' or " problems
                    poligonsDict[column] = json.dumps(str(poligonsDict[column]))
                if (columnNameTypes[column] == "real"):
                    poligonsDict[column] = float(poligonsDict[column])
                if (columnNameTypes[column] != "MULTIPOLYGON" and
                    columnNameTypes[column] != "text"):
                    poligonsDict[column] = str(poligonsDict[column])
            # do insert
            sql = 'INSERT INTO fab_10k ('+ ",".join(columnames) +') VALUES '
            sql += "(" + ",".join(poligonsDict.values()) + ");"
            spliteconn.cursor().execute(sql)
            
            if self.stopThread:
                return


#     def updateExtent(self, spliteconn, comuneDict):
#         if self.stopThread:
#             return
#         
#         # get extent from postgis db... bettehr than doing it in spatialite that is too slow!
#         sqlquery = ""
#         sqlquery += """
#         SELECT 
#             ST_AsText( 
#                 ST_Envelope(
#                     ST_Union(
#                         ST_Envelope(fab_catasto.the_geom)
#                     )
#                 )
#             )
#         FROM 
#             public.fab_catasto, 
#             public.codici_belfiore, 
#             public.istat_comuni
#         WHERE 
#             fab_catasto.belfiore = codici_belfiore.id AND
#             codici_belfiore.id_comune = istat_comuni.id_istat AND
#             codici_belfiore.id_provincia = istat_comuni.idprovincia AND
#             codici_belfiore.toponimo = istat_comuni.toponimo AND
#             istat_comuni.id_istat = '{id_istat}' AND 
#             istat_comuni.idprovincia = '{idprovincia}' AND 
#             istat_comuni.toponimo = '{toponimo}';
#         """.format(**comuneDict)
#         
#         # query extent in WKT format
#         self.procMessage.emit(self.tr("Generando l'extent della tabella fab_catasto e aggionando il DB spatialite"), QgsMessageLog.INFO)
#         self.cursor.execute( sqlquery )
#         
#         wkt = self.cursor.fetchone()
#         geom = QgsGeometry.fromWkt( wkt[0] )
#         if not geom:
#             raise Exception( self.tr("Extent errato: %s" % wkt[0]) )
#         
#         # add in spatialite db
#         extentDict = comuneDict;
#         extentDict["the_geom"] = wkt[0]
#         
#         sqlquery = """
#         INSERT INTO
#             geosisma_extent
#         VALUES
#             ('{id_istat}', '{toponimo}', '{idprovincia}', GeomFromText('{the_geom}', %d) );
#         """.format(**extentDict)
#         sqlquery = sqlquery % (DATABASE_SRID)
#         spliteconn.cursor().execute(sqlquery)
