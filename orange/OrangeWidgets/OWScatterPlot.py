"""
<name>Scatterplot</name>
<description>Shows data using scatterplot</description>
<category>Visualization</category>
<icon>icons/ScatterPlot.png</icon>
<priority>100</priority>
"""
# ScatterPlot.py
#
# Show data using scatterplot
# 

from OWWidget import *
from OWScatterPlotOptions import *
from OWScatterPlotGraph import *
from OWVisTools import *


###########################################################################################
##### WIDGET : Scatterplot visualization
###########################################################################################
class OWScatterPlot(OWWidget):
    settingsList = ["pointWidth", "jitteringType", "showXAxisTitle",
                    "showYAxisTitle", "showVerticalGridlines", "showHorizontalGridlines",
                    "showLegend", "graphGridColor", "graphCanvasColor", "jitterSize", "jitterContinuous", "showFilledSymbols", "kNeighbours"]
    spreadType=["none","uniform","triangle","beta"]
    jitterSizeList = ['0.1','0.5','1','2','5','10', '15', '20']
    jitterSizeNums = [0.1,   0.5,  1,  2,  5,  10, 15, 20]
    kNeighboursList = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '12', '15', '17', '20', '25', '30', '40']
    kNeighboursNums = [ 1 ,  2 ,  3 ,  4 ,  5 ,  6 ,  7 ,  8 ,  9 ,  10 ,  12 ,  15 ,  17 ,  20 ,  25 ,  30 ,  40 ]

    def __init__(self,parent=None):
        #OWWidget.__init__(self, parent, "ScatterPlot", "Show data using scatterplot", TRUE, TRUE)
        apply(OWWidget.__init__, (self, parent, "ScatterPlot", "Show data using scatterplot", TRUE, TRUE)) 

        #set default settings
        self.pointWidth = 7
        self.kNeighbours = 1 
        self.jitteringType = "uniform"
        self.showXAxisTitle = 1
        self.showYAxisTitle = 1
        self.showVerticalGridlines = 0
        self.showHorizontalGridlines = 0
        self.showLegend = 1
        self.jitterContinuous = 0
        self.jitterSize = 5
        self.showFilledSymbols = 1
        self.graphGridColor = str(Qt.black.name())
        self.graphCanvasColor = str(Qt.white.name())

        self.data = None

        #load settings
        self.loadSettings()

        # add a settings dialog and initialize its values
        self.options = OWScatterPlotOptions()

        #GUI
        #add a graph widget
        self.box = QVBoxLayout(self.mainArea)
        self.graph = OWScatterPlotGraph(self.mainArea)
        self.box.addWidget(self.graph)
        self.connect(self.graphButton, SIGNAL("clicked()"), self.graph.saveToFile)

        # graph main tmp variables
        self.addInput("cdata")
        self.addInput("view")

        #connect settingsbutton to show options
        self.connect(self.settingsButton, SIGNAL("clicked()"), self.options.show)        
        self.connect(self.options.widthSlider, SIGNAL("valueChanged(int)"), self.setPointWidth)
        self.connect(self.options.jitteringButtons, SIGNAL("clicked(int)"), self.setSpreadType)
        self.connect(self.options.gSetXaxisCB, SIGNAL("toggled(bool)"), self.setXAxis)
        self.connect(self.options.gSetYaxisCB, SIGNAL("toggled(bool)"), self.setYAxis)
        self.connect(self.options.gSetVgridCB, SIGNAL("toggled(bool)"), self.setVerticalGridlines)
        self.connect(self.options.gSetHgridCB, SIGNAL("toggled(bool)"), self.setHorizontalGridlines)
        self.connect(self.options.gSetLegendCB, SIGNAL("toggled(bool)"), self.setShowLegend)
        self.connect(self.options.gShowFilledSymbolsCB, SIGNAL("toggled(bool)"), self.setFilledSymbols)
        self.connect(self.options.jitterContinuous, SIGNAL("toggled(bool)"), self.setJitterCont)
        self.connect(self.options.jitterSize, SIGNAL("activated(int)"), self.setJitterSize)
        self.connect(self.options, PYSIGNAL("gridColorChange(QColor &)"), self.setGridColor)
        self.connect(self.options, PYSIGNAL("canvasColorChange(QColor &)"), self.setCanvasColor)
        
        #add controls to self.controlArea widget
        self.attrSelGroup = QVGroupBox(self.controlArea)
        self.attrSelGroup.setTitle("Shown attributes")

        self.attrXGroup = QVButtonGroup("X axis attribute", self.attrSelGroup)
        self.attrX = QComboBox(self.attrXGroup)
        self.connect(self.attrX, SIGNAL('activated ( const QString & )'), self.updateGraph)

        self.attrYGroup = QVButtonGroup("Y axis attribute", self.attrSelGroup)
        self.attrY = QComboBox(self.attrYGroup)
        self.connect(self.attrY, SIGNAL('activated ( const QString & )'), self.updateGraph)

        self.attrColorGroup = QVButtonGroup("Coloring attribute", self.attrSelGroup)
        self.attrColorCB = QCheckBox('Enable coloring by', self.attrColorGroup)
        self.attrColorLegendCB = QCheckBox('Show color legend', self.attrColorGroup)
        self.attrColor = QComboBox(self.attrColorGroup)
        self.connect(self.attrColorCB, SIGNAL("clicked()"), self.updateGraph)
        self.connect(self.attrColorLegendCB, SIGNAL("clicked()"), self.updateGraph)
        self.connect(self.attrColor, SIGNAL('activated ( const QString & )'), self.updateGraph)

        self.attrShapeGroup = QVButtonGroup("Shaping attribute", self.attrSelGroup)
        self.attrShapeCB = QCheckBox('Enable shaping by', self.attrShapeGroup)
        self.attrShape = QComboBox(self.attrShapeGroup)
        self.connect(self.attrShapeCB, SIGNAL("clicked()"), self.updateGraph)
        self.connect(self.attrShape, SIGNAL('activated ( const QString & )'), self.updateGraph)        

        self.attrSizeGroup = QVButtonGroup("Sizing attribute", self.attrSelGroup)
        self.attrSizeShapeCB = QCheckBox('Enable sizing by', self.attrSizeGroup)
        self.attrSizeShape = QComboBox(self.attrSizeGroup)
        self.connect(self.attrSizeShapeCB, SIGNAL("clicked()"), self.updateGraph)
        self.connect(self.attrSizeShape, SIGNAL('activated ( const QString & )'), self.updateGraph)        


        # optimization
        self.attrOrderingButtons = QVButtonGroup("Attribute ordering", self.controlArea)
        self.optimizeSeparationButton = QPushButton('Optimize class separation', self.attrOrderingButtons)
        #self.optimizeAllSubsetSeparationButton = QPushButton('Optimize separation for subsets', self.attrOrderingButtons)
        self.interestingProjectionsButton = QPushButton('List of interesting projections', self.attrOrderingButtons)
        self.connect(self.optimizeSeparationButton, SIGNAL("clicked()"), self.optimizeSeparation)


        self.hbox2 = QHBox(self.attrOrderingButtons)
        self.attrOrdLabel = QLabel('Number of neighbours (k):', self.hbox2)
        self.attrKNeighbour = QComboBox(self.hbox2)

        self.interestingprojectionsDlg = InterestingProjections(None)
        self.interestingprojectionsDlg.parentName = "ScatterPlot"
        self.interestingprojectionsDlg.kValue = self.kNeighbours
        
        self.connect(self.interestingProjectionsButton, SIGNAL("clicked()"), self.interestingprojectionsDlg.show)
        self.connect(self.interestingprojectionsDlg.interestingList, SIGNAL("selectionChanged()"),self.showSelectedAttributes)
        self.connect(self.attrKNeighbour, SIGNAL("activated(int)"), self.setKNeighbours)
        
        self.statusBar = QStatusBar(self.mainArea)
        self.box.addWidget(self.statusBar)

        self.activateLoadedSettings()
        self.resize(900, 700)        

    # #########################
    # OPTIONS
    # #########################
    def activateLoadedSettings(self):
        self.options.jitteringButtons.setButton(self.spreadType.index(self.jitteringType))
        self.options.gSetXaxisCB.setChecked(self.showXAxisTitle)
        self.options.gSetYaxisCB.setChecked(self.showYAxisTitle)
        self.options.gSetVgridCB.setChecked(self.showVerticalGridlines)
        self.options.gSetHgridCB.setChecked(self.showHorizontalGridlines)
        self.options.gSetLegendCB.setChecked(self.showLegend)
        self.options.gShowFilledSymbolsCB.setChecked(self.showFilledSymbols)
        self.options.gSetGridColor.setNamedColor(str(self.graphGridColor))
        self.options.gSetCanvasColor.setNamedColor(str(self.graphCanvasColor))

        self.options.jitterContinuous.setChecked(self.jitterContinuous)
        for i in range(len(self.jitterSizeList)):
            self.options.jitterSize.insertItem(self.jitterSizeList[i])
        self.options.jitterSize.setCurrentItem(self.jitterSizeNums.index(self.jitterSize))

        # set items in k neighbours combo
        for i in range(len(self.kNeighboursList)):
            self.attrKNeighbour.insertItem(self.kNeighboursList[i])
        self.attrKNeighbour.setCurrentItem(self.kNeighboursNums.index(self.kNeighbours))

        self.options.widthSlider.setValue(self.pointWidth)
        self.options.widthLCD.display(self.pointWidth)

        self.graph.setJitteringOption(self.jitteringType)
        self.graph.setShowXaxisTitle(self.showXAxisTitle)
        self.graph.setShowYLaxisTitle(self.showYAxisTitle)
        self.graph.enableGridXB(self.showVerticalGridlines)
        self.graph.enableGridYL(self.showHorizontalGridlines)
        self.graph.enableGraphLegend(self.showLegend)
        self.graph.setGridColor(self.options.gSetGridColor)
        self.graph.setCanvasColor(self.options.gSetCanvasColor)
        self.graph.setPointWidth(self.pointWidth)
        self.graph.setJitterContinuous(self.jitterContinuous)
        self.graph.setJitterSize(self.jitterSize)
        self.graph.setShowFilledSymbols(self.showFilledSymbols)

    def setXAxis(self, b):
        self.showXAxisTitle = b
        self.graph.setShowXaxisTitle(self.showXAxisTitle)
        if self.data != None: self.updateGraph()

    def setYAxis(self, b):
        self.showYAxisTitle = b
        self.graph.setShowYLaxisTitle(self.showYAxisTitle)
        if self.data != None: self.updateGraph()

    def setVerticalGridlines(self, b):
        self.showVerticalGridlines = b
        self.graph.enableGridXB(self.showVerticalGridlines)
        if self.data != None: self.updateGraph()

    def setHorizontalGridlines(self, b):
        self.showHorizontalGridlines = b
        self.graph.enableGridYL(self.showHorizontalGridlines)
        if self.data != None: self.updateGraph()

    def setLegend(self, b):
        self.showLegend = b
        self.graph.enableGraphLegend(self.showLegend)
        if self.data != None: self.updateGraph()

    def setJitterCont(self, b):
        self.jitterContinuous = b
        self.graph.setJitterContinuous(self.jitterContinuous)
        if self.data != None: self.updateGraph()

    def setJitterSize(self, index):
        self.jitterSize = self.jitterSizeNums[index]
        self.graph.setJitterSize(self.jitterSize)
        if self.data != None: self.updateGraph()

    def setFilledSymbols(self, b):
        self.showFilledSymbols = b
        self.graph.setShowFilledSymbols(self.showFilledSymbols)
        if self.data != None: self.updateGraph()

    def setPointWidth(self, n):
        self.pointWidth = n
        self.graph.setPointWidth(n)
        if self.data != None: self.updateGraph()
        
    # jittering options
    def setSpreadType(self, n):
        self.jitteringType = self.spreadType[n]
        self.graph.setJitteringOption(self.spreadType[n])
        self.graph.setData(self.data)
        if self.data != None: self.updateGraph()

    # jittering options
    def setJitteringSize(self, n):
        self.jitterSize = self.jitterSizeNums[n]
        self.graph.setJitterSize(self.jitterSize)
        if self.data != None: self.updateGraph()

    def setCanvasColor(self, c):
        self.graphCanvasColor = c
        self.graph.setCanvasColor(c)

    def setGridColor(self, c):
        self.graphGridColor = c
        self.graph.setGridColor(c)

    def setShowLegend(self, b):
        self.showLegend = b
        self.graph.enableGraphLegend(b)
        if self.data != None: self.updateGraph()

    def setHGrid(self, b):
        self.showHorizontalGridlines = b
        self.graph.enableGridXB(b)
        if self.data != None: self.updateGraph()

    def setVGrid(self, b):
        self.showVerticalGridlines = b
        self.graph.enableGridYL(b)
        if self.data != None: self.updateGraph()

    def setKNeighbours(self, n):
        self.kNeighbours = self.kNeighboursNums[n]
        self.interestingprojectionsDlg.kValue = self.kNeighbours

    # ####################################
    # find optimal class separation for shown attributes
    def optimizeSeparation(self):
        if self.data != None:
            self.graph.scaleDataNoJittering()
            (list, value, fullList) = self.graph.getOptimalSeparation(None, self.data.domain.classVar.name, self.kNeighbours)
            if list == []: return

            # fill the "interesting visualizations" list box
            self.interestingprojectionsDlg.optimizedList = []
            self.interestingprojectionsDlg.interestingList.clear()
            for i in range(min(100, len(fullList))):
                ((acc, tableLen), list) = max(fullList)
                self.interestingprojectionsDlg.optimizedList.append(((acc, tableLen), list))
                fullList.remove(((acc, tableLen), list))
                self.interestingprojectionsDlg.interestingList.insertItem("(%.2f, %1.f) - %s"%(acc, tableLen, str(list)))  
                
            self.interestingprojectionsDlg.interestingList.setCurrentItem(0)

    def showSelectedAttributes(self):
        if self.interestingprojectionsDlg.interestingList.count() == 0: return
        index = self.interestingprojectionsDlg.interestingList.currentItem()
        (val, list) = self.interestingprojectionsDlg.optimizedList[index]

        attrNames = []
        for attr in self.data.domain:
            attrNames.append(attr.name)
        
        for item in list:
            if not item in attrNames:
                print "invalid settings"
                return

        self.setText(self.attrX, list[0])
        self.setText(self.attrY, list[1])
        if len(list)>2: self.setText(self.attrShape, list[2])
        else: self.attrShapeCB.setChecked(0)
        if len(list)>3: self.setText(self.attrSizeShape, list[2])
        else: self.attrSizeShapeCB.setChecked(0)
        self.setText(self.attrColor, self.data.domain.classVar.name)        
        
        self.updateGraph()

        
    # #############################
    # ATTRIBUTE SELECTION
    # #############################
    def initAttrValues(self):
        if self.data == None: return

        self.attrX.clear()
        self.attrY.clear()
        self.attrColor.clear()
        self.attrShape.clear()
        self.attrSizeShape.clear()

        self.attrColor.insertItem("(One color)")
        self.attrShape.insertItem("(One shape)")
        self.attrSizeShape.insertItem("(One size)")

        contList = []
        discList = []
        for attr in self.data.domain:
            self.attrX.insertItem(attr.name)
            self.attrY.insertItem(attr.name)
            self.attrColor.insertItem(attr.name)
            self.attrSizeShape.insertItem(attr.name)

            if attr.varType == orange.VarTypes.Continuous:
                contList.append(attr.name)
            if attr.varType == orange.VarTypes.Discrete:
                discList.append(attr.name)
                self.attrShape.insertItem(attr.name)
            

        if len(contList) == 0:
            self.setText(self.attrX, discList[0])
            self.setText(self.attrY, discList[0])
            if len(discList) > 1:
                self.setText(self.attrY, discList[1])                
        elif len(contList) == 1:
            self.setText(self.attrX, contList[0])
            self.setText(self.attrY, contList[0])

        if len(contList) >= 2:
            self.setText(self.attrY, contList[1])
            
        self.setText(self.attrColor, self.data.domain.classVar.name)
        self.attrColorCB.setChecked(1)
        self.setText(self.attrShape, "(One shape)")
        self.setText(self.attrSizeShape, "(One size)")
        

    def setText(self, combo, text):
        for i in range(combo.count()):
            if str(combo.text(i)) == text:
                combo.setCurrentItem(i)
                return

    def updateSettings(self):
        self.showXAxisTitle = self.options.gSetXaxisCB.isOn()
        self.showYAxisTitle = self.options.gSetYaxisCB.isOn()
        self.showVerticalGridlines = self.options.gSetVgridCB.isOn()
        self.showHorizontalGridlines = self.options.gSetHgridCB.isOn()
        self.showLegend = self.options.gSetLegendCB.isOn()
        self.jitterContinuous = self.options.jitterContinuous.isOn()
        self.jitterSize = self.jitterSizeNums[self.jitterSizeList.index(str(self.options.jitterSize.currentText()))]
        self.showFilledSymbols = self.options.gShowFilledSymbolsCB.isOn()

        self.graph.setShowXaxisTitle(self.showXAxisTitle)
        self.graph.setShowYLaxisTitle(self.showYAxisTitle)
        self.graph.enableGridXB(self.showVerticalGridlines)
        self.graph.enableGridYL(self.showHorizontalGridlines)
        self.graph.enableGraphLegend(self.showLegend)
        self.graph.setJitterContinuous(self.jitterContinuous)
        self.graph.setJitterSize(self.jitterSize)
        self.graph.setShowFilledSymbols(self.showFilledSymbols)

        if self.data != None:
            self.updateGraph()


    def updateGraph(self):
        xAttr = str(self.attrX.currentText())
        yAttr = str(self.attrY.currentText())
        colorAttr = ""
        shapeAttr = ""
        sizeShapeAttr = ""
        if self.attrColorCB.isOn():
            colorAttr = str(self.attrColor.currentText())
        if self.attrShapeCB.isOn():
            shapeAttr = str(self.attrShape.currentText())
        if self.attrSizeShapeCB.isOn():
            sizeShapeAttr = str(self.attrSizeShape.currentText())

        self.graph.updateData(xAttr, yAttr, colorAttr, shapeAttr, sizeShapeAttr, self.attrColorLegendCB.isOn(), self.statusBar)
        self.graph.update()
        self.repaint()

    ####### CDATA ################################
    # receive new data and update all fields
    def cdata(self, data):
        if data == None:
            self.data = None
            self.repaint()
            return
        
        #self.data = orange.Preprocessor_dropMissing(data.data)
        self.interestingprojectionsDlg.clear()
        self.data = data.data
        self.initAttrValues()
        self.graph.setData(self.data)
        self.updateGraph()
       
    #################################################

    ####### VIEW ################################
    # receive information about which attributes we want to show on x and y axis
    def view(self, (attr1, attr2)):
        if self.data == None:
            return

        ind1 = 0; ind2 = 0; classInd = 0
        for i in range(self.attrX.count()):
            if str(self.attrX.text(i)) == attr1: ind1 = i
            if str(self.attrX.text(i)) == attr2: ind2 = i

        for i in range(self.attrColor.count()):
            if str(self.attrColor.text(i)) == self.data.domain.classVar.name: classInd = i

        if ind1 == ind2 == classInd == 0:
            print "no valid attributes found"
            return    # something isn't right

        self.attrX.setCurrentItem(ind1)
        self.attrY.setCurrentItem(ind2)
        self.attrColorCB.setChecked(1)
        self.attrColor.setCurrentItem(classInd)
        self.attrShapeCB.setChecked(0)
        self.attrSizeShapeCB.setChecked(0)
        self.updateGraph()       
    #################################################


#test widget appearance
if __name__=="__main__":
    a=QApplication(sys.argv)
    ow=OWScatterPlot()
    a.setMainWidget(ow)
    ow.show()
    a.exec_loop()

    #save settings 
    ow.saveSettings()
