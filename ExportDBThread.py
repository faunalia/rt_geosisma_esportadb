import os, json, traceback
from collections import OrderedDict
from qgis.core import *
from PyQt4.QtCore import *

# SpatiaLite imports
from pyspatialite import dbapi2 as db
# SpatiaLite DB settings
DATABASE_SRID = 32632 # <- have to match with source DB and cratedb script

class ExportDbThread(QThread):
    
    def __init__(self, pgcursor, selectedComuni, outDb):
        QThread.__init__(self)
        self.cursor = pgcursor
        self.selectedComuni = selectedComuni
        self.stopThread = False
        self.DATABASE_NAME = os.path.splitext( os.path.basename(outDb) )[0]
        self.DATABASE_OUTNAME = outDb
        self.DATABASE_OUTNAME_SCHEMAFILE = os.path.dirname(os.path.realpath(__file__))+'/schemas/' + self.DATABASE_NAME + ".sql"
        
    procDone = pyqtSignal(bool)
    procMessage = pyqtSignal(str, int)
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
        
        try:
            # copy tables
            tables = ["istat_regioni", "istat_province", "istat_comuni", "codici_belfiore", "istat_loc_tipi"]
            for table in tables:
                self.copyTable(conn, table)
            
            # coopy table with geom
            tables = ["istat_loc"]
            for table in tables:
                self.copyGeomTable(conn, table)
            
            # get instat poligos only related to selectedComuni
            for comune in selectedComuni:
                print "exporting fields for: ", comune["toponimo"], "..."
                self.copyCatasto2010Polygons(conn, comune)
            
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
            self.procMessage.emit("Copia tabella: "+tableName, QgsMessageLog.INFO)
            # get PostGIS values
            sqlquery = u"SELECT * FROM "+tableName
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

        # get catasto_2010 field types
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
            self.procMessage.emit("Copiando n: %d records" % self.cursor.rowcount, QgsMessageLog.INFO)
        
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


    def copyCatasto2010Polygons(self, spliteconn, comuneDict):
        if self.stopThread:
            return
        # get catasto_2010 field types
        # working with OrderedDict to maintaing ordering among fields and values
        self.procMessage.emit("Copia poligoni per il comune: "+comuneDict["toponimo"] + ". Attenzione operazione lunga!", QgsMessageLog.INFO)
        try:
            records = spliteconn.cursor().execute("PRAGMA table_info(catasto_2010)")
            columnNameTypes = OrderedDict()
            for record in records:
                columnNameTypes[record[1]] = record[2]
            columnNameTypes = OrderedDict( sorted(columnNameTypes.items(), key=lambda x:x[0]) )
        except db.Error as e:
            raise e
        
        # create query
        temp = OrderedDict()
        for k in columnNameTypes.iterkeys():
            temp[str(k)] = "catasto_2010."+str(k)
        temp["the_geom"] = "ST_AsText(" + temp["the_geom"] + ")"

        sqlcolumns = temp.values()
        columnames = columnNameTypes.keys()
        
        sqlquery = "SELECT "+",".join(sqlcolumns) + " "
        sqlquery += """
        FROM 
            public.catasto_2010, 
            public.codici_belfiore, 
            public.istat_comuni
        WHERE 
            catasto_2010.belfiore = codici_belfiore.id AND
            codici_belfiore.id_comune = istat_comuni.id_istat AND
            codici_belfiore.id_provincia = istat_comuni.idprovincia AND
            codici_belfiore.toponimo = istat_comuni.toponimo AND
            istat_comuni.id_istat = '{id_istat}' AND 
            istat_comuni.idprovincia = '{idprovincia}' AND 
            istat_comuni.toponimo = '{toponimo}';
        """.format(**comuneDict)
        
        # query all poligons
        self.cursor.execute( sqlquery )
        self.procMessage.emit("Copiando n: %d records" % self.cursor.rowcount, QgsMessageLog.INFO)
        
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
            sql = 'INSERT INTO catasto_2010 ('+ ",".join(columnames) +') VALUES '
            sql += "(" + ",".join(poligonsDict.values()) + ");"
            spliteconn.cursor().execute(sql)
            
            if self.stopThread:
                return
