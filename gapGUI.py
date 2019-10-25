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

MONO_SCALING_FACTOR = 0.9804  #According to Craig's Au foil measurements, March 2019


class gapGUI(QWidget):


	def __init__(self):
		super().__init__()

		self.HPOL = 0
		self.VPOL = 1

		self.polarization = self.HPOL

		self.VPOL_table = Path('LookupTables/vpol_gap_table.txt')
		self.HPOL_table = Path('LookupTables/HPOLfundamental.txt')
		self.M1Pitch_table = Path('LookupTables/M1_pitch.txt')

		self.initUI()
		self.resize(900, 400)


	def initUI(self):
		self.setWindowTitle('gapGUI')
		
		superlayout = QVBoxLayout()

		layout = QVBoxLayout()
		sublayout = QHBoxLayout()
		sublayout.addStretch(1)
		self.combo = QComboBox(self)
		self.combo.addItem(" Horizontal (p) polarization ")
		self.combo.addItem(" Vertical (s) polarization ")
		self.combo.currentIndexChanged.connect(self.polarizationChanged)
		sublayout.addWidget(self.combo)
		sublayout.addStretch(1)
		layout.addLayout(sublayout)
	
		superlayout.addLayout(layout)
		superlayout.addStretch(1)

		layout = QHBoxLayout()

		tabs = QTabWidget()
		tab1 = QWidget()	
		tab2 = QWidget()
		tabs.resize(300,200) 
 
		tabs.addTab(tab1,"Choose hv")
		tabs.addTab(tab2,"Choose gap")

		tab1.layout  = QVBoxLayout()
		tab1.form = QFormLayout()

		self.hvInput = QLineEdit()
		tab1.form.addRow(QLabel("Mono energy:"),self.hvInput)
		tab1.layout.addLayout(tab1.form)
		tab1.hbox=QHBoxLayout()
		tab1.hbox.addStretch(1)

		tab1.calculateButton=QPushButton('Calculate')
		tab1.calculateButton.clicked.connect(self.hvCalculateButtonClicked)
		tab1.hbox.addWidget(tab1.calculateButton)
		tab1.layout.addLayout(tab1.hbox)	
		tab1.setLayout(tab1.layout)

		tab2.layout  = QVBoxLayout()
		tab2.form = QFormLayout()
		self.gapInput = QLineEdit()
		tab2.form.addRow(QLabel("EPU gap:"),self.gapInput)
		tab2.layout.addLayout(tab2.form)
		tab2.hbox=QHBoxLayout()
		tab2.hbox.addStretch(1)
		tab2.calculateButton=QPushButton('Calculate')
		tab2.calculateButton.clicked.connect(self.gapCalculateButtonClicked)
		tab2.hbox.addWidget(tab2.calculateButton)
		tab2.layout.addLayout(tab2.hbox)	
		tab2.setLayout(tab2.layout)
		

		layout.addWidget(tabs)
		layout.addStretch(1)
		
		# RHS output
		outputvbox  = QVBoxLayout()
		outputLabel = QLabel("Beamline settings:")
		outputvbox.addWidget(outputLabel)
		self.outputForm = QFormLayout()
		self.outputEPUGap=QLineEdit()
		self.outputForm.addRow(QLabel("EPU gap:"),self.outputEPUGap)
		self.outputEPUPhase=QLineEdit()
		self.outputForm.addRow(QLabel("EPU phase:"),self.outputEPUPhase)
		self.outputhv=QLineEdit()
		self.outputForm.addRow(QLabel("Mono energy:"),self.outputhv)
		self.correcthv=QLineEdit()
		self.outputForm.addRow(QLabel("True energy:"),self.correcthv)
		self.outputPitch=QLineEdit()
		self.outputForm.addRow(QLabel("M1 pitch:"),self.outputPitch)

		outputvbox.addLayout(self.outputForm)
		layout.addLayout(outputvbox)
		superlayout.addLayout(layout)
		superlayout.addStretch(1)

	

		superlayout.addWidget(QLabel("Status information:"))

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
			self.messageBox.insertPlainText("\nUsing gap lookup table:  HPOLfundamental.txt")

		test=lookupGap(self.VPOL_table,20)

		if test==0:
			self.messageBox.insertPlainText("\n!! Couldn't find gap table:  vpol_gap_table.txt !!")
			self.messageBox.insertPlainText("\n\tUnable to calculate until you restart with that file present")

			tab1.calculateButton.setEnabled(False)
			tab2.calculateButton.setEnabled(False)
		else:
			self.messageBox.insertPlainText("\nUsing gap lookup table:  vpol_gap_table.txt")

		test=lookupM1Pitch(self.M1Pitch_table,20)
		if test==0:
			self.messageBox.insertPlainText("\n!! Couldn't find pitch table:  M1_pitch.txt !!")
			self.messageBox.insertPlainText("\n\tButtons greyed until you restart with that file present")

			tab1.calculateButton.setEnabled(False)
			tab2.calculateButton.setEnabled(False)
		else:
			self.messageBox.insertPlainText("\nUsing M1 pitch lookup table:  M1_pitch.txt")
		
		self.messageBox.insertPlainText("\nUsing mono correction factor real = set*{}".format(MONO_SCALING_FACTOR))

		

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
		self.correcthv.setText("")

		if i == self.HPOL:
			self.polarization=self.HPOL
		if i == self.VPOL:
			self.polarization=self.VPOL

	def hvCalculateButtonClicked(self):
		hvText = self.hvInput.text()
		if hvText=='':
			self.messageBox.moveCursor(QtGui.QTextCursor.End)
			self.messageBox.insertPlainText("\nYou can't leave the 'Mono energy' field blank")
		else:
			try:
				hv = float(hvText)
			except:
				self.messageBox.moveCursor(QtGui.QTextCursor.End)
				self.messageBox.insertPlainText("\nhv ='{0}'? What's that supposed to mean?".format(hvText))
				return

			self.outputhv.setText("{0:.2f}".format(hv))
			self.correcthv.setText("{0:.2f}".format(hv*MONO_SCALING_FACTOR))

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

			pitch = lookupM1Pitch(self.M1Pitch_table,hv)
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
				self.correcthv.setText("{0:.2f}".format(hv*MONO_SCALING_FACTOR))
				self.outputEPUPhase.setText("{0}".format(phase))
				pitch = lookupM1Pitch(self.M1Pitch_table,hv)
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





