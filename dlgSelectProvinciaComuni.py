# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dlgSelectProvinciaComuni.ui'
#
# Created: Wed Oct 30 17:12:11 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_DlgSelectProvinciaComuni(object):
    def setupUi(self, DlgSelectProvinciaComuni):
        DlgSelectProvinciaComuni.setObjectName(_fromUtf8("DlgSelectProvinciaComuni"))
        DlgSelectProvinciaComuni.setWindowModality(QtCore.Qt.WindowModal)
        DlgSelectProvinciaComuni.resize(697, 505)
        self.gridLayout = QtGui.QGridLayout(DlgSelectProvinciaComuni)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(DlgSelectProvinciaComuni)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(False)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.dbListComboBox = QtGui.QComboBox(DlgSelectProvinciaComuni)
        self.dbListComboBox.setObjectName(_fromUtf8("dbListComboBox"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.dbListComboBox)
        self.verticalLayout.addLayout(self.formLayout)
        self.label_2 = QtGui.QLabel(DlgSelectProvinciaComuni)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.provinceComboBox = QtGui.QComboBox(DlgSelectProvinciaComuni)
        self.provinceComboBox.setObjectName(_fromUtf8("provinceComboBox"))
        self.verticalLayout.addWidget(self.provinceComboBox)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label_4 = QtGui.QLabel(DlgSelectProvinciaComuni)
        self.label_4.setAlignment(QtCore.Qt.AlignCenter)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.horizontalLayout_2.addWidget(self.label_4)
        self.label_3 = QtGui.QLabel(DlgSelectProvinciaComuni)
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.horizontalLayout_2.addWidget(self.label_3)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.comuniListView = QtGui.QListView(DlgSelectProvinciaComuni)
        self.comuniListView.setObjectName(_fromUtf8("comuniListView"))
        self.horizontalLayout.addWidget(self.comuniListView)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.addPushButton = QtGui.QPushButton(DlgSelectProvinciaComuni)
        self.addPushButton.setObjectName(_fromUtf8("addPushButton"))
        self.verticalLayout_2.addWidget(self.addPushButton)
        self.removePushButton = QtGui.QPushButton(DlgSelectProvinciaComuni)
        self.removePushButton.setObjectName(_fromUtf8("removePushButton"))
        self.verticalLayout_2.addWidget(self.removePushButton)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.selectedComuniListView = QtGui.QListView(DlgSelectProvinciaComuni)
        self.selectedComuniListView.setObjectName(_fromUtf8("selectedComuniListView"))
        self.horizontalLayout.addWidget(self.selectedComuniListView)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.selectOutFilePushButton = QtGui.QPushButton(DlgSelectProvinciaComuni)
        self.selectOutFilePushButton.setObjectName(_fromUtf8("selectOutFilePushButton"))
        self.verticalLayout.addWidget(self.selectOutFilePushButton)
        self.exportDbPushButton = QtGui.QPushButton(DlgSelectProvinciaComuni)
        self.exportDbPushButton.setObjectName(_fromUtf8("exportDbPushButton"))
        self.verticalLayout.addWidget(self.exportDbPushButton)
        self.progressBar = QtGui.QProgressBar(DlgSelectProvinciaComuni)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.verticalLayout.addWidget(self.progressBar)
        self.logLabel = QtGui.QLabel(DlgSelectProvinciaComuni)
        self.logLabel.setText(_fromUtf8(""))
        self.logLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.logLabel.setObjectName(_fromUtf8("logLabel"))
        self.verticalLayout.addWidget(self.logLabel)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(DlgSelectProvinciaComuni)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Help)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 2)

        self.retranslateUi(DlgSelectProvinciaComuni)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), DlgSelectProvinciaComuni.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), DlgSelectProvinciaComuni.reject)
        QtCore.QMetaObject.connectSlotsByName(DlgSelectProvinciaComuni)

    def retranslateUi(self, DlgSelectProvinciaComuni):
        DlgSelectProvinciaComuni.setWindowTitle(QtGui.QApplication.translate("DlgSelectProvinciaComuni", "Esporta il DB Geosisma a SpatiaLite", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("DlgSelectProvinciaComuni", "DB Sorgente", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("DlgSelectProvinciaComuni", "Province", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("DlgSelectProvinciaComuni", "Comuni", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("DlgSelectProvinciaComuni", "Comuni da Esportare", None, QtGui.QApplication.UnicodeUTF8))
        self.addPushButton.setText(QtGui.QApplication.translate("DlgSelectProvinciaComuni", ">", None, QtGui.QApplication.UnicodeUTF8))
        self.removePushButton.setText(QtGui.QApplication.translate("DlgSelectProvinciaComuni", "<", None, QtGui.QApplication.UnicodeUTF8))
        self.selectOutFilePushButton.setText(QtGui.QApplication.translate("DlgSelectProvinciaComuni", "Seleziona DB di destinazione", None, QtGui.QApplication.UnicodeUTF8))
        self.exportDbPushButton.setText(QtGui.QApplication.translate("DlgSelectProvinciaComuni", "Exporta DB", None, QtGui.QApplication.UnicodeUTF8))

