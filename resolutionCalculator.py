"""
If anybody reads this: I'm so sorry
	--CraPol
"""


## GUI
from PyQt5.QtWidgets import *
from PyQt5 import QtCore,QtGui

## Saving to file
import sys

from BLOCH_beamline import *
import numpy as np




class gapGUI(QWidget):


	def __init__(self):
		super().__init__()
		self.initUI()
		self.resize(900, 400)


	def initUI(self):
		self.setWindowTitle('BLOCH resolution calculator v1 (13.02.2019)')
		
		superlayout = QVBoxLayout()

		layout  = QHBoxLayout()

		# Analyzer input
		analyzer_vbox  = QVBoxLayout()
		analyzer_Label = QLabel("Analyzer settings:")
		analyzer_vbox.addWidget(analyzer_Label)
		self.analyzer_Form = QFormLayout()
		self.analyzer_passEnergy=QLineEdit()
		self.analyzer_Form.addRow(QLabel("Pass energy (eV)"),self.analyzer_passEnergy)
		self.analyzer_slit=QLineEdit()
		self.analyzer_Form.addRow(QLabel("Slit (mm)"),self.analyzer_slit)
		self.analyzer_noise=QLineEdit()
		self.analyzer_Form.addRow(QLabel("Noise (meV)"),self.analyzer_noise)

		analyzer_vbox.addLayout(self.analyzer_Form)
		layout.addLayout(analyzer_vbox)

		layout.addStretch(1)
		
		# Beamline input
		beamline_vbox  = QVBoxLayout()
		beamline_Label = QLabel("Beamline settings:")
		beamline_vbox.addWidget(outputLabel)
		self.beamline_Form = QFormLayout()
		self.beamline_ExitSlit=QLineEdit()
		self.beamline_Form.addRow(QLabel("Exit slit vgap (um)"),self.beamline_ExitSlit)
		self.beamline_hv=QLineEdit()
		self.beamline_Form.addRow(QLabel("Photon energy (eV)"),self.beamline_hv)
		beamline_vbox.addLayout(self.beamline_Form)
		layout.addLayout(beamline_vbox)

		superlayout.addLayout(layout)
		superlayout.addStretch(1)

		self.calculateButton=QPushButton('Calculate')
		self.calculateButton.clicked.connect(self.CalculateButtonClicked)
		superlayout.addWidget(calculateButton)

		# Results
		superlayout.addWidget(QLabel("Resolution:"))

		self.messageBox = QTextEdit()
		self.messageBox.setReadOnly(True)
		self.messageBox.setLineWrapMode(QTextEdit.NoWrap)
		self.font = QtGui.QFont()
		self.font.setPointSize(12)
		label = QLabel("text text")
		label.setFont(self.font)
		self.messageBox.setFont(self.font)
		self.messageBox.setMaximumHeight(label.sizeHint().height() * 5)

		self.messageBox.moveCursor(QtGui.QTextCursor.End)
		test=lookupGap(self.HPOL_table,20)

		if test==0:
			self.messageBox.insertPlainText("\n!! Couldn't find gap table:  HPOLfundamental.txt !!")
			self.messageBox.insertPlainText("\n\tUnable to calculate until you restart with that file present")

			tab1.calculateButton.setEnabled(False)
			tab2.calculateButton.setEnabled(False)
		else:
			self.messageBox.insertPlainText("\nGaps for h.pol. based on lookup table:  HPOLfundamental.txt")

		test=lookupGap(self.VPOL_table,20)

		if test==0:
			self.messageBox.insertPlainText("\n!! Couldn't find gap table:  vpol_gap_table.txt !!")
			self.messageBox.insertPlainText("\n\tUnable to calculate until you restart with that file present")

			tab1.calculateButton.setEnabled(False)
			tab2.calculateButton.setEnabled(False)
		else:
			self.messageBox.insertPlainText("\nGaps for v.pol. based on lookup table::  vpol_gap_table.txt")

		self.messageBox.insertPlainText("\nM1 pitch is linear with grating slope, based on measurements taken 04.02.2018")
		

		sb = self.messageBox.verticalScrollBar()
		sb.setValue(sb.maximum())

		superlayout.addWidget(self.messageBox)
		self.setLayout(superlayout)
		self.show()

	def polarizationChanged(self,i):
		self.outputEPUGap.setText("")
		self.outputEPUPhase.setText("")
		self.outputhv.setText("")
		self.outputPitch.setText("")

		if i == self.HPOL:
			self.polarization=self.HPOL
		if i == self.VPOL:
			self.polarization=self.VPOL

	def hvCalculateButtonClicked(self):
		hvText = self.hvInput.text()
		if hvText=='':
			self.messageBox.moveCursor(QtGui.QTextCursor.End)
			self.messageBox.insertPlainText("\nYou can't leave the 'photon energy' field blank")
		else:
			try:
				hv = float(hvText)
			except:
				self.messageBox.moveCursor(QtGui.QTextCursor.End)
				self.messageBox.insertPlainText("\nhv ='{0}'? What's that supposed to mean?".format(hvText))
				return

			self.outputhv.setText("{0:.2f}".format(hv))
		

			if self.polarization==self.HPOL:
				gap = lookupGap(self.HPOL_table,hv)
				phase = 0
			elif self.polarization==self.VPOL:
				gap = lookupGap(self.VPOL_table,hv)
				phase = 42

			if np.isnan(gap):
				self.messageBox.moveCursor(QtGui.QTextCursor.End)
				self.messageBox.insertPlainText("\nCouldn't find a gap for getting hv={0} - probably out of range of the lookup table".format(hv))
			
			self.outputEPUGap.setText("{0:.2f}".format(gap))
			self.outputEPUPhase.setText("{0:.2f}".format(phase))

			pitch = lookupM1Pitch(hv)

			if np.isnan(pitch):
				self.messageBox.moveCursor(QtGui.QTextCursor.End)
				self.messageBox.insertPlainText("\nCouldn't find a pitch for hv={0} - probably out of range of the lookup table".format(hv))

			self.outputPitch.setText("{0:.1f}".format(pitch))



	def gapCalculateButtonClicked(self):
		gapText = self.gapInput.text()
		if gapText=='':
			self.messageBox.moveCursor(QtGui.QTextCursor.End)
			self.messageBox.insertPlainText("\nYou can't leave the 'EPU gap' field blank")
		else:
			try:
				gap = float(gapText)

				self.outputEPUGap.setText("{0}".format(gap))
				if self.polarization==self.HPOL:
					hv = lookupHarmonicEnergy(self.HPOL_table,gap,1)
					phase=0
				if self.polarization==self.VPOL:
					hv = lookupHarmonicEnergy(self.VPOL_table,gap,1)
					phase = 42

				if np.isnan(hv):
					self.messageBox.moveCursor(QtGui.QTextCursor.End)
					self.messageBox.insertPlainText("\nCouldn't find a photon energy for gap {0} - probably out of range of the lookup table".format(gap))
				self.outputhv.setText("{0}".format(hv))
				self.outputEPUPhase.setText("{0}".format(phase))
				pitch = lookupM1Pitch(hv)
				if np.isnan(pitch):
					self.messageBox.moveCursor(QtGui.QTextCursor.End)
					self.messageBox.insertPlainText("\nCouldn't find a pitch for hv={0} - probably out of range of the lookup table".format(hv))

				self.outputPitch.setText("{0:.1f}".format(pitch))
		
			except:
				self.messageBox.moveCursor(QtGui.QTextCursor.End)
				self.messageBox.insertPlainText("\nEPU Gap ='{0}'? What's that supposed to mean?".format(gapText))


if __name__ == '__main__':
	app = QApplication(sys.argv)
	app.setStyle('Fusion')
	font = QtGui.QFont()
	font.setPointSize(16)
	app.setFont(font)
	ex = gapGUI()
	sys.exit(app.exec_())





