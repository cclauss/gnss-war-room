from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtGui import QResizeEvent
from PyQt6.QtCore import pyqtSignal, QByteArray
from palettes.palette import Palette
from gnss.satellite import SatelliteInView
from views.polarGrid.generate import readBasePolarGrid, prepareIntialPolarGrid
from views.polarGrid.update import addSatellitesToPolarGrid


class PolarGridWindow(QMainWindow):
	"""Window for displaying the positions of satellites"""

	satelliteReceivedEvent = pyqtSignal()

	def __init__(self, palette: Palette):
		super().__init__()

		self.customPalette = palette
		self.latestSatellites = []

		self.svgFile = self.generateNewGrid()
		self.polarGrid = QSvgWidget(parent=self)
		self.polarGrid.load(self.svgFile)
		self.polarGrid.setGeometry(0, 0, 400, 400)

		self.satelliteReceivedEvent.connect(self.newSatelliteDataEvent)

		self.setWindowTitle("Polar Grid")
		self.setStyleSheet(f"background-color: {palette.background}; color: {palette.foreground};")
		self.show()

	def generateNewGrid(self):
		svgData = readBasePolarGrid()
		svgData = prepareIntialPolarGrid(svgData, self.customPalette)
		self.basePolarGrid = svgData
		return QByteArray(svgData.encode())

	def updateGrid(self):
		svgData = addSatellitesToPolarGrid(
			self.basePolarGrid, self.customPalette, self.latestSatellites
		)
		return QByteArray(svgData.encode())

	def resizeEvent(self, event: QResizeEvent):
		newX = event.size().width()
		newY = event.size().height()
		minSize = min(newX, newY)
		self.polarGrid.setGeometry(
			int((newX - minSize) / 2), int((newY - minSize) / 2), minSize, minSize
		)

	def onNewData(self, satellites: list[SatelliteInView]):
		self.latestSatellites = satellites
		self.satelliteReceivedEvent.emit()

	def newSatelliteDataEvent(self):
		self.svgFile = self.updateGrid()
		self.polarGrid.load(self.svgFile)
