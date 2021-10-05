####################################################################################################
#SCRIPT: URT_atulshakya.py
#VERSION: 2.0
#AUTHOR: ATUL SHAKYA
#CREATION DATE: MAY 26, 2021

#RUNNING VERSION: v032
#LAST UPDATED: DEBUGGED THE CONTROL RIG SECTION AND ADDED IN ERROR MESSAGES. 
#              ADDED THE HELP BUTTON

#DESCRIPTION: GROUP OF RIGGING TOOLS IN MAYA
#REQUIREMENT: N/A
#RETURNS: N/A
####################################################################################################

from PySide2 import QtCore #Contains the base functionality of QT, except the codes for UI and Widgets
from PySide2 import QtWidgets #Containts the Widgets codes for PySide2
from PySide2 import QtGui #Used here to add icons to buttons
from shiboken2 import wrapInstance
from functools import partial

import maya.OpenMayaUI as omui #Contains helper methods for working with Qt 
import maya.OpenMaya as om #Contains methods to create warning or error message windows (among other things)

import maya.cmds as cmds
import maya.mel as mel

import pymel.core as pymel

#Creating a Helper Function
#Returns Maya's Main Window Widget as a Python Object (converting a C++ pointer [Maya's Windows] into a Python object)
#Parent out Dialog window below to Maya's main window (so our dialog window always stays on top of the Maya window)
def maya_main_window():
    main_window_pntr = omui.MQtUtil.mainWindow() #Returns Maya's main window as a pointer
    return wrapInstance(long(main_window_pntr), QtWidgets.QWidget) #Converts the pointer to a python object[QWidget]


#Creating an 'UndoContext' Class
#This class allows the script to group some lines of code together, so that it can all be Undo'ed at the same time (instead of it undo-ing every line of code individually )
class UndoContext(object):
    def __enter__(self):
        cmds.undoInfo(openChunk=True)
    def __exit__(self, *exc_info):
        cmds.undoInfo(closeChunk=True)
        
#Creating a QWidget Class
#Creating a Widget class to display images in the UI 
#This is a custom widget class, that works in similar ways as any other widgets, like a Push Button, a Label or a Spin Box
class CustomImageWidget (QtWidgets.QWidget):
    
    def __init__ (self, width, height, image_path, parent = None):
        super (CustomImageWidget, self).__init__(parent)
        
        self.setSize (width, height)
        self.setImage (image_path)
        self.setBackgroundColor(QtCore.Qt.transparent)
    
    #Setting the size of the image widget
    def setSize (self, width, height):
        self.setFixedSize(width, height)
    
    #Setting the image to be displayed
    def setImage (self, image_path):
        image = QtGui.QImage (image_path)
        image = image.scaled (self.width(),self.height(), QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
        
        self.pixmap = QtGui.QPixmap()
        self.pixmap.convertFromImage(image)
        
        self.update() #If the 'update' method is not called then the image won't change until the UI is resized
    
    #Setting up the background color for the image
    def setBackgroundColor (self, color):
        self.backgroundColor = color
        
        self.update() #If the 'update' method is not called then the background color won't change until the UI is resized
    
    #Paint Event is a default PySide Function/Method, which runs when the widget first loads up, when the size of the widget changes or when the 'update' method is called
    def paintEvent (self, event):
        painter = QtGui.QPainter(self)
        
        painter.fillRect(0, 0, self.width(), self.height(), self.backgroundColor) #Paints the background color through a rectangle
        painter.drawPixmap (self.rect(), self.pixmap) #Paints the image on top of the background rectangle

#Creating a QWidget Class
#This is the class that creates the selectable/changeable color swatches. [Used here in the 'Create Controller' window]
#Through this class we are EMBEDDING A MAYA CONTROL (here, colorSliderGrp) to a Qt UI
class CustomColorButton(QtWidgets.QWidget):

    colorChanged = QtCore.Signal(QtGui.QColor) #Creates a signal that can be emitted when certain thing is done. Like the 'clicked' signal that we use to know when the button is clicked.

    def __init__(self, color, parent=None):
        super(CustomColorButton, self).__init__(parent)

        self.setObjectName("CustomColorButton") #Setting an Object Name for the Class
        
        self.createControl()

        self.setSize(65, 15)
        self.setColor(color)
        
    def createControl (self):
        
        ''' 1. Create the colorSliderGrp'''
        #The 'Maya Controls' cannot be directly parented to a QtWidget, so we have to create a temporary maya window to create the maya controls
        window = cmds.window() #Creating a temporary window to store the MEL 'colorSliderGrp', this will not be shown and will be deleted below
        self._name = cmds.colorSliderGrp() #Creating the 'colorSliderGrp' and storing it in a private variable
        
        ''' 2. Find the colorSliderGrp widget'''
        colorSliderObj = omui.MQtUtil.findControl(self._name) #Searches for a Maya Control by the name and Returns a QWidget Pointer in C++        
        if colorSliderObj:
            self._colorSliderWidget = wrapInstance(long(colorSliderObj), QtWidgets.QWidget) #Converting the C++ pointer to a Python object
        
            ''' 3. Reparent the colorSliderGrp widget to this widget'''
            #Here, it takes the colorSliderWidget off of the Maya Window and parents it to the QtWidget (window)
            mainLayout = QtWidgets.QVBoxLayout(self)
            mainLayout.setObjectName("mainLayout") #Setting an Object Name for the Layout
            mainLayout.setContentsMargins(0, 0, 0, 0)
            mainLayout.addWidget(self._colorSliderWidget)
                    
            ''' 4. Update the colorSliderGrp control name (used by Maya)'''
            #Because we changed the parent of the 'colorSliderGrp' from Maya's window to Qt's window, the control name for the created 'colorSliderGrp' has changed.
            #We are looking for the new control name of the newly parented 'colorSliderGrp', so we can edit/query the control. Without the upadted control name, we can no longer able to access the control.
            self._name = omui.MQtUtil.fullName(long(colorSliderObj)) #This will return the full name of an object (needs the C++ pointer)
                    
            ''' 5. Identify/Store the colorSliderGrp's child widget (and hide if required)'''
            
            #Checking the child widgets included in the control (here, 'colorSliderGrp') and getting their names
            '''
            children = self._colorSliderWidget.children()
            for child in children:
                print (child)
                print (child.objectName())
            '''
            
            #Using the names of the child widget, printed from the commented lines of code above, to edit the children of the widget
            self._sliderWidget = self._colorSliderWidget.findChild(QtWidgets.QWidget, "slider") #Getting the Slider widget
            if self._sliderWidget:
                self._sliderWidget.hide() #Hiding the slider from the colorSliderGrp
            
            self._colorSwatchWidget = self._colorSliderWidget.findChild(QtWidgets.QWidget, "port") #Getting the Color Swatch Widget
            
            cmds.colorSliderGrp(self._name, edit = True, changeCommand = partial(self.onColorChanged)) #Asking the 'colorSliderGrp' to call 'onColorChanged' method, when the color in the widget is changed
        
        cmds.deleteUI(window, window = True) #Deleting the temp window
    
    #Sets the size of the color label (where the colors can be seen)
    #This area is also used to determine the click box for the click function below
    def setSize(self, width, height):
        self._colorSliderWidget.setFixedWidth(width)
        self._colorSliderWidget.setFixedHeight(height)

    #Sets the selected color in the UI/Label
    def setColor(self, color):
        color = QtGui.QColor(color) #Making sure that the color is an QColor object
        
        cmds.colorSliderGrp(self._name, edit = True, rgbValue = (color.redF(), color.greenF(), color.blueF())) #Editing the 'colorSliderGrp's current color 
        self.onColorChanged()

    #Used to get the current selected color in the UI/Label
    def getColor(self):
        color = cmds.colorSliderGrp(self._colorSliderWidget.objectName(), q = True, rgbValue = True) #Gets the color from the colorSliderGrp and gives a value from 0.0 to 1.0 for each rgb color

        color = QtGui.QColor(color[0] * 255, color[1] * 255, color[2] * 255) #Coverting the color to QColor and the value to range from 0 to 255 for each rgb color 
        return color
    
    #This method is called when the user changes the color in the widget
    def onColorChanged (self, *args):
        self.colorChanged.emit (self.getColor())

'''
####################################################################################################
UI BUILDING PHASE
START
####################################################################################################
'''        
#Creating a QDialog Class
#This is where all the UI stuff takes place, like putting buttons or text fields and so on...
class MainDialog (QtWidgets.QDialog):
    
    #'self' denotes the instance of the dialog class [here.. 'Main Dialog']
    
    #Creating a list of file filter for the file path dialog box below (open file window)
    FILE_FILTERS = "Maya (*.ma *.mb);;Python Script (*.py);; Max (*.max);; All (*.*)"
    
    selected_filter = "Maya (*.ma *.mb)" #Setting up the default selection for the filter
    
    dlg_instance = None
    
    #To check if the window already exists or not when opening through shelf buttons/menus..
    #If the window doesn't exist then opens a new one, if it does exists then shows the old window
    @classmethod
    def showDialog (cls):
        if not cls.dlg_instance:
            cls.dlg_instance = MainDialog()
        
        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show() #If the window is hidden then shows the window
        else:
            #If it's not hidden and is behind other maya windows, it brings it to the front and activates the window
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()
                
    
    #'__init__' Initializes the 'MainDialog' class. This is what runs first when you call the 'MainDialog' class.
    #You can also add the parameters that the class might need here..
    #For e.g. def __init__ (self, width, height, parent = maya_main_window()), when calling this class you'll need to include the 'width' and the 'height' parameters as well i.e. MainDialog (550,490)
    def __init__ (self, parent = maya_main_window()):
       super (MainDialog, self).__init__(parent)
       
       self.setWindowTitle("URT v 2.0")
       self.setMinimumWidth (550)
       self.setMinimumHeight (515)
       
       #Removing the 'question mark' button from top of the window
       #'self.setWindowFlags()' - let's you change the look of the dialog [window]
       #'self.windowFlags()' - returns all of the current flags
       self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
       
       self.create_widgets()
       self.create_layouts()
       self.create_connection()
    
    #Creates the widgets for the window   
    def create_widgets (self):    
        self.create_controller_image()
        '''
        Creating the main combo box
        '''
        self.main_comboBox = QtWidgets.QComboBox()
        self.main_comboBox.addItems(["Helper Scripts", 
                                    "Built-In", 
                                    "Control Rig"])
        self.default_main_comboBox = self.main_comboBox.itemText(0)
        
        '''
        Creating the list for the custom-panel
        '''
        self.custom_list = QtWidgets.QListWidget()
        self.custom_list.addItems(["Search/Replace Names",
                                   "Create Controllers", 
                                   "Create Controller from Text",
                                   "Export To FBX",
                                   "Range of Motion (ROM)",
                                   "Miscellaneous"])
        self.custom_list.setMaximumWidth(150)
        self.custom_list.setMinimumWidth(150)
        self.custom_list.setCurrentRow(0)
        
        '''
        Search and Replace Name Widgets
        '''
        self.search_name_le = QtWidgets.QLineEdit()
        self.replace_name_le = QtWidgets.QLineEdit()
        self.hierachy_name_rb = QtWidgets.QRadioButton("Hierarchy")
        self.hierachy_name_rb.setChecked(True)   
        self.selected_name_rb = QtWidgets.QRadioButton("Selected")
        self.all_name_rb = QtWidgets.QRadioButton("All")   
        self.search_apply_btn = QtWidgets.QPushButton("Apply")
        self.addPrefix_le = QtWidgets.QLineEdit()
        self.addPrefix_btn = QtWidgets.QPushButton("Add")
        self.addSuffix_le = QtWidgets.QLineEdit()
        self.addSuffix_btn = QtWidgets.QPushButton("Add")
        self.numRename_le = QtWidgets.QLineEdit()
        self.startNumber_sb = QtWidgets.QSpinBox()
        self.startNumber_sb.setValue(1)
        self.paddingNumber_sb = QtWidgets.QSpinBox()
        self.paddingNumber_sb.setValue (1)
        self.paddingNumber_sb.setMinimum (1)
        self.stepsNumber_sb = QtWidgets.QSpinBox()
        self.stepsNumber_sb.setValue (1)
        self.stepsNumber_sb.setMinimum (1)
        self.numRename_btn = QtWidgets.QPushButton("Rename")
        
        '''
        Create Widgets for the Create Controller Tab
        '''
        self.controller_list = QtWidgets.QListWidget()
        self.controller_list.addItems(["Circle",
                                   "Square", 
                                   "Cube",
                                   "Hexagon",
                                   "Sphere",
                                   "Cross",
                                   "Arrow",
                                   "Arc Arrow",
                                   "Double Arrow",
                                   "Curved Arrow",
                                   "Tube",
                                   "Gear",
                                   "Plus",
                                   "Triangle",
                                   "Pyramid",
                                   "3D Diamond",
                                   "2D Diamond",
                                   "Diamond Sphere"])
        self.controller_list.setMaximumWidth(120)
        self.controller_list.setCurrentRow(0)
        
        self.controllerName_le = QtWidgets.QLineEdit()
        self.controllerSuffix_le = QtWidgets.QLineEdit()
        self.controllerSuffix_le.setText("_ctrl")
        self.controllerSize_sb = QtWidgets.QDoubleSpinBox()
        self.controllerSize_sb.setValue(1.0)
        self.controllerSize_sb.setFixedWidth (80)
        self.controllerSize_sb.setRange (0.01 , 150.0)
        self.controllerSize_sb.setSingleStep (0.1)
        self.controllerColor_ccb = CustomColorButton(QtCore.Qt.yellow)
        self.controllerForceLabel_cb = QtWidgets.QCheckBox("Force Label")
        self.controllerSnapSelected_cb = QtWidgets.QCheckBox("Snap to Selected")
        self.controllerSnapSelected_cb.setChecked(True)
        self.controller_apply_btn = QtWidgets.QPushButton ("Apply")
        
        self.controllerGroup_sb = QtWidgets.QSpinBox()
        self.controllerGroup_sb.setValue(1)
        self.controllerGroup_sb.setFixedWidth (80)
        self.controllerGroup_sb.setRange (0 , 4)
        self.controllerGroup_sb.setSingleStep (1)
        self.firstGroupSuffix_le = QtWidgets.QLineEdit()
        self.firstGroupSuffix_le.setText("_offset")
        self.secondGroupSuffix_le = QtWidgets.QLineEdit()
        self.secondGroupSuffix_le.setText("_con")
        self.secondGroupSuffix_le.setEnabled(False)
        self.thirdGroupSuffix_le = QtWidgets.QLineEdit()
        self.thirdGroupSuffix_le.setText("_grp")
        self.thirdGroupSuffix_le.setEnabled(False)
        self.fourthGroupSuffix_le = QtWidgets.QLineEdit()
        self.fourthGroupSuffix_le.setText("_grp")
        self.fourthGroupSuffix_le.setEnabled(False)
        
        '''
        Create Controller from Text Widgets
        '''
        self.controller_text_name_le = QtWidgets.QLineEdit()
        self.controller_text_font_combo = QtWidgets.QFontComboBox()
        self.controller_text_font_combo.FontFilter (QtWidgets.QFontComboBox.MonospacedFonts)
        self.controller_text_btn = QtWidgets.QPushButton("Create")
        
        '''
        Create Widgets for Import/Export Tab
        '''
        self.exportSelected_rb = QtWidgets.QRadioButton("Selected")
        self.exportSelected_rb.setChecked(True)
        self.exportModel_rb = QtWidgets.QRadioButton("Models")
        self.exportModelRig_rb = QtWidgets.QRadioButton("Models and Rig")
        self.exportAnimationModel_rb = QtWidgets.QRadioButton("Animations with Model")
        self.exportAnimation_rb = QtWidgets.QRadioButton("Animations without Model")
        self.exportAll_rb = QtWidgets.QRadioButton("All")
        
        self.unityEngineSelected_rb = QtWidgets.QRadioButton("Unity          ") #Spaces are there to fix the spacing in the UI
        self.unrealEngineSelected_rb = QtWidgets.QRadioButton("Unreal ")
        self.noneEngineSelected_rb = QtWidgets.QRadioButton("None")
        self.noneEngineSelected_rb.setChecked(True)
        
        self.exportProjectPath_le = QtWidgets.QLineEdit()
        self.exportProjectPath_le.setEnabled(False)
        self.exportProjecPath_btn = QtWidgets.QPushButton("")
        self.exportProjecPath_btn.setIcon(QtGui.QIcon(":fileOpen.png")) #Adding a icon to the button instead of a text (':' tells Qt that the '.png' file is a maya resource)
        self.exportProjecPath_btn.setToolTip ("Select File") #Adding a tooltip to the button
        self.exportProjecPath_btn.setEnabled(False)
        
        self.exportOptions_comboBox = QtWidgets.QComboBox()
        self.exportOptions_comboBox.addItems(["Automatic", 
                                    "Manual"])
        self.default_exportOptions_comboBox = self.main_comboBox.itemText(0)
        
        self.exportSmoothingGrp_cb = QtWidgets.QCheckBox("Smoothing Groups")
        self.exportSmoothingGrp_cb.setChecked(True)
        self.exportSmoothMesh_cb = QtWidgets.QCheckBox("Smooth Mesh   ")
        self.exportSmoothMesh_cb.setChecked(True)
        self.exportRac_cb = QtWidgets.QCheckBox("Referenced Assests Content")
        self.exportRac_cb.setChecked(True)
        self.exportTraingulate_cb = QtWidgets.QCheckBox("Triangulate")
        self.exportSmoothingGrp_cb.setEnabled(False)
        self.exportSmoothMesh_cb.setEnabled(False)
        self.exportRac_cb.setEnabled(False)
        self.exportTraingulate_cb.setEnabled(False)
        
        self.exportAnimations_cb = QtWidgets.QCheckBox("Animation")
        self.exportAnimations_cb.setEnabled(False)
        
        self.exportBakeAnimation_cb = QtWidgets.QCheckBox("Bake Animation")
        self.exportBakeAnimation_cb.setEnabled(False)
        self.exportBakeStart_sb = QtWidgets.QSpinBox()
        self.exportBakeStart_sb.setRange(-5,1000000)
        self.exportBakeStart_sb.setFixedWidth (80)
        self.exportBakeStart_sb.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.exportBakeStart_sb.setValue(cmds.playbackOptions (query = True, minTime = True))
        self.exportBakeEnd_sb = QtWidgets.QSpinBox()
        self.exportBakeEnd_sb.setRange(-5,1000000)
        self.exportBakeEnd_sb.setFixedWidth (80)
        self.exportBakeEnd_sb.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.exportBakeEnd_sb.setValue(cmds.playbackOptions (query = True, maxTime = True))
        self.exportBakeSteps_sb = QtWidgets.QSpinBox()
        self.exportBakeSteps_sb.setFixedWidth (80)
        self.exportBakeSteps_sb.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.exportBakeSteps_sb.setValue(1)
        self.exportReSample_cb = QtWidgets.QCheckBox("Resample All")
        self.exportBakeStart_sb.setEnabled(False)
        self.exportBakeEnd_sb.setEnabled(False)
        self.exportBakeSteps_sb.setEnabled(False)
        self.exportReSample_cb.setEnabled(False)
        
        self.exportUnitsAuto_cb = QtWidgets.QCheckBox("Automatic")
        self.exportUnitsAuto_cb.setChecked(True)
        self.exportUnitsAuto_cb.setEnabled(False)
        self.exportUnit_comboBox = QtWidgets.QComboBox()
        self.exportUnit_comboBox.addItems(["centimeters", 
                                    "millimeters",
                                    "decimeters",
                                    "meters",
                                    "kilometeres",
                                    "inches",
                                    "feet",
                                    "yards",
                                    "miles"])
        self.default_exportUnit_comboBox = self.main_comboBox.itemText(0)
        self.exportUnit_comboBox.setEnabled(False)
        
        self.exportUpAxis_comboBox = QtWidgets.QComboBox()
        self.exportUpAxis_comboBox.addItems(["Y", 
                                    "Z"])
        self.default_exportUpAxis_comboBox = self.main_comboBox.itemText(0)
        self.exportUpAxis_comboBox.setEnabled(False)
        
        '''
        Create Widgets for Miscellaneous Tab
        '''
        self.optimize_rig_btn = QtWidgets.QPushButton ("Remove Unknown Nodes")
        self.combine_shapeNode_btn = QtWidgets.QPushButton("Combine Shape")
        self.select_skinnedJnts_btn = QtWidgets.QPushButton("Select Skinned Joints")
        
        self.createIKControllerSize_sb = QtWidgets.QDoubleSpinBox()
        self.createIKControllerSize_sb.setValue(1.0)
        self.createIKControllerSize_sb.setFixedWidth (80)
        self.createIKControllerSize_sb.setRange (0.01 , 150.0)
        self.createIKControllerSize_sb.setSingleStep (0.1)
        
        self.create_IK_btn = QtWidgets.QPushButton("Setup IK")
        
        '''
        Range of Motion (ROM) Widgets
        '''
        #Creating CheckBoxes for X,Y,Z values
        self.rotXP_cb = QtWidgets.QCheckBox()
        self.rotXP_cb.setChecked(True)
        self.rotYP_cb = QtWidgets.QCheckBox()
        self.rotYP_cb.setChecked(True)
        self.rotZP_cb = QtWidgets.QCheckBox()
        self.rotZP_cb.setChecked(True)
        self.rotXN_cb = QtWidgets.QCheckBox()
        self.rotXN_cb.setChecked(True)
        self.rotYN_cb = QtWidgets.QCheckBox()
        self.rotYN_cb.setChecked(True)
        self.rotZN_cb = QtWidgets.QCheckBox()
        self.rotZN_cb.setChecked(True)
        
        #Creatinig Labels for the UI
        self.emptyLabel_label = QtWidgets.QLabel("")
        self.XLabel_label = QtWidgets.QLabel("X")
        self.YLabel_label = QtWidgets.QLabel("Y")
        self.ZLabel_label = QtWidgets.QLabel("Z")
        self.PLabel_label = QtWidgets.QLabel("+ve")
        self.NLabel_label = QtWidgets.QLabel("-ve")
        
        #Creating Spin Box for the Timeline Values
        self.angleBox_sb = QtWidgets.QDoubleSpinBox()
        self.angleBox_sb.setValue(60)
        self.framePad_sb = QtWidgets.QSpinBox()
        self.framePad_sb.setValue(20)
        self.frameStart_sb = QtWidgets.QSpinBox()
        self.frameStart_sb.setValue(0)
        
        #Creating Buttons
        self.rom_delete_key_btn = QtWidgets.QPushButton("Delete Keys")
        self.rom_apply_btn = QtWidgets.QPushButton("Create")
        self.rom_apply_btn.hide()
        
        '''
        Create Control Rig Widgets
        '''
        self.left_joints_le = QtWidgets.QLineEdit()
        self.right_joints_le = QtWidgets.QLineEdit()
        self.controllerSize_controlRig_sb = QtWidgets.QDoubleSpinBox()
        self.controllerSize_controlRig_sb.setValue(10.0)
        self.controllerSize_controlRig_sb.setFixedWidth (65)
        self.controllerSize_controlRig_sb.setRange (0.01 , 150.0)
        self.controllerSize_controlRig_sb.setSingleStep (0.1)
        
        self.pelvis_le = QtWidgets.QLineEdit()
        self.pelvis_btn = QtWidgets.QPushButton("<<")
        self.spine1_le = QtWidgets.QLineEdit()
        self.spine1_btn = QtWidgets.QPushButton("<<")
        self.chest_le = QtWidgets.QLineEdit()
        self.chest_btn = QtWidgets.QPushButton("<<")
        self.neck_le = QtWidgets.QLineEdit()
        self.neck_btn = QtWidgets.QPushButton("<<")
        self.head_le = QtWidgets.QLineEdit()
        self.head_btn = QtWidgets.QPushButton("<<")
        
        self.armIK_cb = QtWidgets.QCheckBox("IK")
        self.armIK_cb.setChecked(True)
        self.armFK_cb = QtWidgets.QCheckBox("FK")
        self.armFK_cb.setChecked(True)
        self.clavicle_le = QtWidgets.QLineEdit()
        self.clavicle_btn = QtWidgets.QPushButton("<<")
        self.shoulder_le = QtWidgets.QLineEdit()
        self.shoulder_btn = QtWidgets.QPushButton("<<")
        self.elbow_le = QtWidgets.QLineEdit()
        self.elbow_btn = QtWidgets.QPushButton("<<")
        self.wrist_le = QtWidgets.QLineEdit()
        self.wrist_btn = QtWidgets.QPushButton("<<")
        
        self.legIK_cb = QtWidgets.QCheckBox("IK")
        self.legIK_cb.setChecked(True)
        self.legFK_cb = QtWidgets.QCheckBox("FK")
        self.legFK_cb.setChecked(True)
        self.thigh_le = QtWidgets.QLineEdit()
        self.thigh_btn = QtWidgets.QPushButton("<<")
        self.knee_le = QtWidgets.QLineEdit()
        self.knee_btn = QtWidgets.QPushButton("<<")
        self.ankle_le = QtWidgets.QLineEdit()
        self.ankle_btn = QtWidgets.QPushButton("<<")
        self.ball_le = QtWidgets.QLineEdit()
        self.ball_btn = QtWidgets.QPushButton("<<")
        
        self.footRollControls_cb = QtWidgets.QCheckBox("Foot Roll Controls")
        
        '''
        Create Built-In Buttons
        '''
        self.builtIn_label = QtWidgets.QLabel ("** Right-Click the Buttons to Access the Option Window")
        self.builtIn_label.setAlignment(QtCore.Qt.AlignRight)
        builtIn_label_font = QtGui.QFont()
        builtIn_label_font.setBold(True)
        builtIn_label_font.setWeight(81)
        builtIn_label_font.setPointSize(8)
        self.builtIn_label.setFont(builtIn_label_font)
        
        #General Options
        self.deleteKeys_built_btn = QtWidgets.QPushButton ("DK")
        self.deleteKeys_built_btn.setIcon(QtGui.QIcon(":menuIconEdit.png"))
        self.deleteKeys_built_btn.setToolTip ("Delete Keys on Selected")
        self.deleteHistory_built_btn = QtWidgets.QPushButton ("Hist")
        self.deleteHistory_built_btn.setIcon(QtGui.QIcon(":menuIconEdit.png"))
        self.deleteHistory_built_btn.setToolTip ("Delete History")
        self.duplicate_built_btn = QtWidgets.QPushButton ("Dupl")
        self.duplicate_built_btn.setIcon(QtGui.QIcon(":menuIconEdit.png"))
        self.duplicate_built_btn.setToolTip ("Duplicate")
        self.parent_built_btn = QtWidgets.QPushButton ("Pare")
        self.parent_built_btn.setIcon(QtGui.QIcon(":menuIconEdit.png"))
        self.parent_built_btn.setToolTip ("Parent")
        self.unParent_built_btn = QtWidgets.QPushButton ("Unpa")
        self.unParent_built_btn.setIcon(QtGui.QIcon(":menuIconEdit.png"))
        self.unParent_built_btn.setToolTip ("UnParent")
        self.locator_built_btn = QtWidgets.QPushButton ("LOC")
        self.locator_built_btn.setIcon(QtGui.QIcon(":locator.png"))
        self.locator_built_btn.setToolTip ("Create Locator")
        self.hierachy_built_btn = QtWidgets.QPushButton ("Hier")
        self.hierachy_built_btn.setIcon(QtGui.QIcon(":menuIconSelect.png"))
        self.hierachy_built_btn.setToolTip ("Select Hierarchy")
        self.freezeTrans_built_btn = QtWidgets.QPushButton ("FT")
        self.freezeTrans_built_btn.setIcon(QtGui.QIcon(":menuIconModify.png"))
        self.freezeTrans_built_btn.setToolTip ("Freeze Transformations")
        self.resetTrans_built_btn = QtWidgets.QPushButton ("RT")
        self.resetTrans_built_btn.setIcon(QtGui.QIcon(":menuIconModify.png"))
        self.resetTrans_built_btn.setToolTip ("Reset Transformations")
        self.centerPivot_built_btn = QtWidgets.QPushButton ("CP")
        self.centerPivot_built_btn.setIcon(QtGui.QIcon(":menuIconModify.png"))
        self.centerPivot_built_btn.setToolTip ("Centre Pivot")
        self.disHideLRA_built_btn = QtWidgets.QPushButton ("LRA")
        self.disHideLRA_built_btn.setIcon(QtGui.QIcon(":menuIconDisplay.png"))
        self.disHideLRA_built_btn.setToolTip ("Toggle Local Rotation Axis Visibility")
        
        #Joints
        self.createJoint_built_btn = QtWidgets.QPushButton ("")
        self.createJoint_built_btn.setIcon(QtGui.QIcon(":kinJoint.png"))
        self.createJoint_built_btn.setToolTip ("Create Joint")
        self.mirrorJoint_built_btn = QtWidgets.QPushButton ("")
        self.mirrorJoint_built_btn.setIcon(QtGui.QIcon(":kinMirrorJoint_S.png"))
        self.mirrorJoint_built_btn.setToolTip ("Mirror Joint")
        self.orientJoint_built_btn = QtWidgets.QPushButton ("")
        self.orientJoint_built_btn.setIcon(QtGui.QIcon(":orientJoint.png"))
        self.orientJoint_built_btn.setToolTip ("Orient Joint")
        self.createIKJoint_built_btn = QtWidgets.QPushButton ("")
        self.createIKJoint_built_btn.setIcon(QtGui.QIcon(":kinHandle.png"))
        self.createIKJoint_built_btn.setToolTip ("Create IK Handle")
        self.splineIKJoint_built_btn = QtWidgets.QPushButton ("")
        self.splineIKJoint_built_btn.setIcon(QtGui.QIcon(":kinSplineHandle.png"))
        self.splineIKJoint_built_btn.setToolTip ("Create Spline IK Handle")
        self.jointSizeJoint_built_btn = QtWidgets.QPushButton ("")
        self.jointSizeJoint_built_btn.setIcon(QtGui.QIcon(":ikEffector.svg"))
        self.jointSizeJoint_built_btn.setToolTip ("Change Joint Size")
        
        #Skinning
        self.bindSkin_built_btn = QtWidgets.QPushButton ("")
        self.bindSkin_built_btn.setIcon(QtGui.QIcon(":smoothSkin.png"))
        self.bindSkin_built_btn.setToolTip ("Bind Skin")
        self.unBindSkin_built_btn = QtWidgets.QPushButton ("")
        self.unBindSkin_built_btn.setIcon(QtGui.QIcon(":detachSkin.png"))
        self.unBindSkin_built_btn.setToolTip ("Unbind Skin")
        self.bindPoseSkin_built_btn = QtWidgets.QPushButton ("")
        self.bindPoseSkin_built_btn.setIcon(QtGui.QIcon(":goToBindPose.png"))
        self.bindPoseSkin_built_btn.setToolTip ("Go To Bind Pose")
        self.paintSkin_built_btn = QtWidgets.QPushButton ("")
        self.paintSkin_built_btn.setIcon(QtGui.QIcon(":paintSkinWeights.png"))
        self.paintSkin_built_btn.setToolTip ("Paint Skin Weights")
        self.mirrorSkin_built_btn = QtWidgets.QPushButton ("")
        self.mirrorSkin_built_btn.setIcon(QtGui.QIcon(":mirrorSkinWeight.png"))
        self.mirrorSkin_built_btn.setToolTip ("Mirror Skin Weights")
        self.copyWeightsSkin_built_btn = QtWidgets.QPushButton ("")
        self.copyWeightsSkin_built_btn.setIcon(QtGui.QIcon(":copySkinWeight.png"))
        self.copyWeightsSkin_built_btn.setToolTip ("Copy Skin Weights")
        self.smoothSkin_built_btn = QtWidgets.QPushButton ("")
        self.smoothSkin_built_btn.setIcon(QtGui.QIcon(":smoothSkinWeights.png"))
        self.smoothSkin_built_btn.setToolTip ("Smooth Skin Weights")
        self.copyVertexSkin_built_btn = QtWidgets.QPushButton ("")
        self.copyVertexSkin_built_btn.setIcon(QtGui.QIcon(":nConstraintTransform.png"))
        self.copyVertexSkin_built_btn.setToolTip ("Copy Vertex Weights")
        self.pasteVertexSkin_built_btn = QtWidgets.QPushButton ("")
        self.pasteVertexSkin_built_btn.setIcon(QtGui.QIcon(":nConstraintWeldBorders.png"))
        self.pasteVertexSkin_built_btn.setToolTip ("Paste Vertex Weights")
        self.pruneSkin_built_btn = QtWidgets.QPushButton ("")
        self.pruneSkin_built_btn.setIcon(QtGui.QIcon(":meshVarGroup.svg"))
        self.pruneSkin_built_btn.setToolTip ("Prune Skin Weights")
        self.setInfluenceSkin_built_btn = QtWidgets.QPushButton ("")
        self.setInfluenceSkin_built_btn.setIcon(QtGui.QIcon(":setMaxInfluence.png"))
        self.setInfluenceSkin_built_btn.setToolTip ("Set Max Influence")
        self.addInfluenceSkin_built_btn = QtWidgets.QPushButton ("")
        self.addInfluenceSkin_built_btn.setIcon(QtGui.QIcon(":addWrapInfluence.png"))
        self.addInfluenceSkin_built_btn.setToolTip ("Add Skin Influence")
        self.removeInfluenceSkin_built_btn = QtWidgets.QPushButton ("")
        self.removeInfluenceSkin_built_btn.setIcon(QtGui.QIcon(":removeWrapInfluence.png"))
        self.removeInfluenceSkin_built_btn.setToolTip ("Remove Skin Influence")
        self.bakeDeformSkin_built_btn = QtWidgets.QPushButton ("")
        self.bakeDeformSkin_built_btn.setIcon(QtGui.QIcon(":substGeometry.png"))
        self.bakeDeformSkin_built_btn.setToolTip ("Bake Deformation to Skin Weights")
        
        #Deform
        self.blendShapeDeform_built_btn = QtWidgets.QPushButton ("")
        self.blendShapeDeform_built_btn.setIcon(QtGui.QIcon(":blendShape.png"))
        self.blendShapeDeform_built_btn.setToolTip ("Create a new Blendshape")
        #self.blendShapeDeform_built_btn.setFixedSize(30,30)
        self.poseSpaceDeform_built_btn = QtWidgets.QPushButton ("")
        self.poseSpaceDeform_built_btn.setIcon(QtGui.QIcon(":pi-add.png"))
        self.poseSpaceDeform_built_btn.setToolTip ("Create a Pose Intropolator Node")
        self.clusterDeform_built_btn = QtWidgets.QPushButton ("")
        self.clusterDeform_built_btn.setIcon(QtGui.QIcon(":cluster.png"))
        self.clusterDeform_built_btn.setToolTip ("Create a Cluster")
        
        #Constraint
        self.parentConstraint_built_btn = QtWidgets.QPushButton ("")
        self.parentConstraint_built_btn.setIcon(QtGui.QIcon(":parentConstraint.png"))
        self.parentConstraint_built_btn.setToolTip ("Parent Constraint")
        self.pointConstraint_built_btn = QtWidgets.QPushButton ("")
        self.pointConstraint_built_btn.setIcon(QtGui.QIcon(":posConstraint.png"))
        self.pointConstraint_built_btn.setToolTip ("Point Constraint")
        self.orientConstraint_built_btn = QtWidgets.QPushButton ("")
        self.orientConstraint_built_btn.setIcon(QtGui.QIcon(":orientConstraint.png"))
        self.orientConstraint_built_btn.setToolTip ("Orient Constraint")
        self.scaleConstraint_built_btn = QtWidgets.QPushButton ("")
        self.scaleConstraint_built_btn.setIcon(QtGui.QIcon(":scaleConstraint.png"))
        self.scaleConstraint_built_btn.setToolTip ("Scale Constraint")
        self.poleVectorConstraint_built_btn = QtWidgets.QPushButton ("")
        self.poleVectorConstraint_built_btn.setIcon(QtGui.QIcon(":poleVectorConstraint.png"))
        self.poleVectorConstraint_built_btn.setToolTip ("Pole Vector Constraint")
        self.aimConstraint_built_btn = QtWidgets.QPushButton ("")
        self.aimConstraint_built_btn.setIcon(QtGui.QIcon(":aimConstraint.png"))
        self.aimConstraint_built_btn.setToolTip ("Aim Constraint")
        
        #Windows
        self.componentWindow_built_btn = QtWidgets.QPushButton ("CpEd")
        self.componentWindow_built_btn.setIcon(QtGui.QIcon(":menuIconWindow.png"))
        self.componentWindow_built_btn.setToolTip ("Component Editor")
        self.connectionWindow_built_btn = QtWidgets.QPushButton ("CE")
        self.connectionWindow_built_btn.setIcon(QtGui.QIcon(":menuIconWindow.png"))
        self.connectionWindow_built_btn.setToolTip ("Connection Editor")
        self.nodeWindow_built_btn = QtWidgets.QPushButton ("NE")
        self.nodeWindow_built_btn.setIcon(QtGui.QIcon(":menuIconWindow.png"))
        self.nodeWindow_built_btn.setToolTip ("Node Editor")
        self.graphWindow_built_btn = QtWidgets.QPushButton ("")
        self.graphWindow_built_btn.setIcon(QtGui.QIcon(":teGraphEditor.png"))
        self.graphWindow_built_btn.setToolTip ("Graph Editor")
        self.channelWindow_built_btn = QtWidgets.QPushButton ("CC")
        self.channelWindow_built_btn.setIcon(QtGui.QIcon(":menuIconWindow.png"))
        self.setDrivenKeyWindow_built_btn = QtWidgets.QPushButton ("")
        self.setDrivenKeyWindow_built_btn.setIcon(QtGui.QIcon(":setDrivenKeyframe.png"))
        self.setDrivenKeyWindow_built_btn.setToolTip ("Set Driven Key")
        self.channelWindow_built_btn.setToolTip ("Channel Control")
        self.shapeWindow_built_btn = QtWidgets.QPushButton ("")
        self.shapeWindow_built_btn.setIcon(QtGui.QIcon(":blendShapeEditor.png"))
        self.shapeWindow_built_btn.setToolTip ("Shape Editor")
        self.poseWindow_built_btn = QtWidgets.QPushButton ("")
        self.poseWindow_built_btn.setIcon(QtGui.QIcon(":poseEditor.png"))
        self.poseWindow_built_btn.setToolTip ("Pose Editor")
        
        
        '''       
        Creating Cancel/Accept/Help Buttons
        '''
        self.helpDocs_btn = QtWidgets.QPushButton ("Help")
        self.exportApply_btn = QtWidgets.QPushButton("Export")
        self.exportApply_btn.hide()
        self.accept_btn = QtWidgets.QPushButton("Accept")
        self.accept_btn.hide()
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
    
    #Function to create controller images in the UI
    def create_controller_image (self):
        self.image_path =  "D:/_RMIT/Semester 4/Studio 4/urt_atulshakya/icons/"
                
        self.controllerImage_ciw = CustomImageWidget(205, 50, "{0}circle.png".format(self.image_path))
    
    #Puts the above widgets into a layout (vertical or horizontal)
    def create_layouts (self): 
        '''
        Cancel Button Layout
        '''
        button_layout = QtWidgets.QHBoxLayout() #Creating a horizontal layout for the buttons, which is going to be parented to the 'main_layout' below
        button_layout.addWidget(self.helpDocs_btn)
        button_layout.addStretch() #Creates the space in front of the 'ok' button
        button_layout.addWidget(self.accept_btn)
        button_layout.addWidget(self.exportApply_btn)
        button_layout.addWidget(self.rom_apply_btn)
        button_layout.addWidget(self.cancel_btn)
        self.button_grp = QtWidgets.QFrame()
        self.button_grp.setLayout(button_layout)
        
        '''
        Main Dropdown Layout
        '''
        mainCombo_layout = QtWidgets.QHBoxLayout()
        mainCombo_layout.addStretch()
        mainCombo_layout.addWidget(self.main_comboBox)
        
        '''
        CUSTOM WINDOW LAYOUT
        START
        '''
        '''
        Search and Replace Name Layout
        '''
        searchReplace_gridLayout = QtWidgets.QGridLayout()
        searchReplace_gridLayout.setHorizontalSpacing(5)
        searchReplace_gridLayout.setColumnStretch(0,0)
        searchReplace_gridLayout.setColumnStretch(1,1)
        searchReplace_gridLayout.setColumnStretch(2,1)
        searchReplace_gridLayout.setColumnStretch(3,1)
        
        searchReplace_gridLayout.addWidget (self.hierachy_name_rb, 0, 1)
        searchReplace_gridLayout.addWidget (self.selected_name_rb, 0, 2)
        searchReplace_gridLayout.addWidget (self.all_name_rb, 0, 3)
        
        self.search_lbl = QtWidgets.QLabel("Search")
        searchReplace_gridLayout.addWidget(self.search_lbl, 1, 0, QtCore.Qt.AlignRight)
        searchReplace_gridLayout.addWidget(self.search_name_le, 1, 1, 1, 3)
        
        self.replace_lbl = QtWidgets.QLabel("Replace")
        searchReplace_gridLayout.addWidget(self.replace_lbl, 2, 0, QtCore.Qt.AlignRight)
        searchReplace_gridLayout.addWidget(self.replace_name_le, 2, 1, 1, 3)
        
        searchReplace_gridLayout.addWidget(self.search_apply_btn, 3, 1)
        
        self.prefix_lbl = QtWidgets.QLabel("Prefix")
        searchReplace_gridLayout.addWidget(self.prefix_lbl, 4, 0, QtCore.Qt.AlignRight)
        searchReplace_gridLayout.addWidget(self.addPrefix_le, 4, 1, 1, 3)
        
        searchReplace_gridLayout.addWidget(self.addPrefix_btn, 5, 1)
        
        self.suffix_lbl = QtWidgets.QLabel("Suffix")
        searchReplace_gridLayout.addWidget(self.suffix_lbl, 6, 0, QtCore.Qt.AlignRight)
        searchReplace_gridLayout.addWidget(self.addSuffix_le, 6, 1, 1, 3)
        
        searchReplace_gridLayout.addWidget(self.addSuffix_btn, 7, 1)
        
        self.rename_lbl = QtWidgets.QLabel("Rename")
        searchReplace_gridLayout.addWidget(self.rename_lbl, 8, 0, QtCore.Qt.AlignRight)
        searchReplace_gridLayout.addWidget(self.numRename_le, 8, 1, 1, 3)
                
        self.start_lbl = QtWidgets.QLabel("Start #")
        searchReplace_gridLayout.addWidget(self.start_lbl, 9, 0, QtCore.Qt.AlignRight)
        searchReplace_gridLayout.addWidget(self.startNumber_sb, 9, 1)
        
        self.steps_lbl = QtWidgets.QLabel("Steps")
        searchReplace_gridLayout.addWidget(self.steps_lbl, 10, 0, QtCore.Qt.AlignRight)
        searchReplace_gridLayout.addWidget(self.stepsNumber_sb, 10, 1)
        
        self.length_lbl = QtWidgets.QLabel("Padding")
        searchReplace_gridLayout.addWidget(self.length_lbl, 11, 0, QtCore.Qt.AlignRight)
        searchReplace_gridLayout.addWidget(self.paddingNumber_sb, 11, 1)
        
        searchReplace_gridLayout.addWidget(self.numRename_btn, 12, 1)
        
        search_bottomSpacer = QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        searchReplace_gridLayout.addItem (search_bottomSpacer, 13, 0, 1, 4)
        
        self.search_replace_frame = QtWidgets.QGroupBox("Search and Replace Names")
        self.search_replace_frame.setAlignment(QtCore.Qt.AlignCenter)
        self.search_replace_frame.setLayout(searchReplace_gridLayout)
        
        '''
        Create Controllers Layout
        '''
        createControllerSide_formLayout = QtWidgets.QFormLayout()
        createControllerSide_formLayout.addRow ("", self.controllerForceLabel_cb)
        createControllerSide_formLayout.addRow ("", self.controllerSnapSelected_cb)
        createControllerSide_formLayout.addRow ("Label", self.controllerName_le)
        createControllerSide_formLayout.addRow ("Suffix", self.controllerSuffix_le)
        createControllerSide_formLayout.addRow ("Size", self.controllerSize_sb)
        createControllerSide_formLayout.addRow ("Color", self.controllerColor_ccb)
        createControllerSide_formLayout.addRow ("Groups", self.controllerGroup_sb)
        createControllerSide_formLayout.addRow ("Suffix 1", self.firstGroupSuffix_le)
        createControllerSide_formLayout.addRow ("Suffix 2", self.secondGroupSuffix_le)
        createControllerSide_formLayout.addRow ("Suffix 3", self.thirdGroupSuffix_le)
        createControllerSide_formLayout.addRow ("Suffix 4", self.fourthGroupSuffix_le)
        createControllerSide_formLayout.addRow ("", self.controller_apply_btn)
        
        createControllerImage_layout = QtWidgets.QVBoxLayout()
        createControllerImage_layout.addWidget(self.controllerImage_ciw)
        createControllerImage_layout.addLayout(createControllerSide_formLayout)
        
        createController_layout = QtWidgets.QHBoxLayout()
        createController_layout.addWidget(self.controller_list)
        createController_layout.addLayout(createControllerImage_layout) 
        
        self.createController_layout_frame = QtWidgets.QGroupBox("Create Controller")
        self.createController_layout_frame.setAlignment(QtCore.Qt.AlignCenter)
        self.createController_layout_frame.setLayout(createController_layout)
        self.createController_layout_frame.hide()
        
        '''
        Controller from Text layout
        '''
        controllerText_formLayout = QtWidgets.QFormLayout()
        controllerText_formLayout.addRow ("Text", self.controller_text_name_le)
        controllerText_formLayout.addRow("Font", self.controller_text_font_combo)
        controllerText_formLayout.addRow ("", self.controller_text_btn)
        
        self.controllerText_frame = QtWidgets.QGroupBox("Create Controller from Input Text")
        self.controllerText_frame.setAlignment(QtCore.Qt.AlignCenter)
        self.controllerText_frame.setLayout(controllerText_formLayout)
        self.controllerText_frame.hide()
        
        '''
        Export Tab Layout
        '''
        exportOptions_layout = QtWidgets.QGridLayout()
        exportOptions_layout.setHorizontalSpacing(30)
        exportOptions_layout.addWidget(self.exportSelected_rb,0,0)
        exportOptions_layout.addWidget(self.exportModel_rb,0,1)
        exportOptions_layout.addWidget(self.exportModelRig_rb,0,2)
        exportOptions_layout.addWidget(self.exportAnimation_rb,1,0)
        exportOptions_layout.addWidget(self.exportAnimationModel_rb,1,1)
        exportOptions_layout.addWidget(self.exportAll_rb,1,2)
        exportOptions_layout_grp = QtWidgets.QGroupBox("")
        exportOptions_layout_grp.setLayout(exportOptions_layout)
        
        exportEngine_layout = QtWidgets.QGridLayout()
        exportEngine_layout.setHorizontalSpacing(112)
        exportEngine_layout.addWidget(self.unityEngineSelected_rb,0,1)
        exportEngine_layout.addWidget(self.unrealEngineSelected_rb,0,2)
        exportEngine_layout.addWidget(self.noneEngineSelected_rb,0,3)
        exportEngine_layout_grp = QtWidgets.QGroupBox("")
        exportEngine_layout_grp.setLayout(exportEngine_layout)
        
        exportFilePath_layout = QtWidgets.QHBoxLayout()
        exportFilePath_layout.addWidget(self.exportProjectPath_le)
        exportFilePath_layout.addWidget(self.exportProjecPath_btn)
        
        exportGeometry_layout = QtWidgets.QGridLayout()
        exportGeometry_layout.setHorizontalSpacing(70)
        exportGeometry_layout.addWidget(self.exportSmoothingGrp_cb,0,1)
        exportGeometry_layout.addWidget(self.exportSmoothMesh_cb,0,2)
        exportGeometry_layout.addWidget(self.exportRac_cb,0,3)
        exportGeometry_layout.addWidget(self.exportTraingulate_cb,1,1)
        
        exportTab_layout = QtWidgets.QFormLayout()
        exportTab_layout.setVerticalSpacing(15)
        exportTab_layout.addRow("Export: ", exportOptions_layout_grp)
        exportTab_layout.addRow("Unity or Unreal: ", exportEngine_layout_grp)
        exportTab_layout.addRow("Unity/Unreal Project Path: ", exportFilePath_layout)
        exportTab_layout.addRow("Export Options: ", self.exportOptions_comboBox)
        exportTab_layout.addRow("Geometry: ", exportGeometry_layout)
        exportTab_layout.addRow("Animation: ", self.exportAnimations_cb)
        exportTab_layout.addRow("", self.exportBakeAnimation_cb)
        exportTab_layout.addRow("Start: ", self.exportBakeStart_sb)
        exportTab_layout.addRow("End: ", self.exportBakeEnd_sb)
        exportTab_layout.addRow("Steps: ", self.exportBakeSteps_sb)
        exportTab_layout.addRow("", self.exportReSample_cb)
        exportTab_layout.addRow("Units Coversion: ", self.exportUnitsAuto_cb)
        exportTab_layout.addRow("Units Converted To: ", self.exportUnit_comboBox)
        exportTab_layout.addRow("Up Axis: ", self.exportUpAxis_comboBox)
        
        self.exportTab_layout_frame = QtWidgets.QGroupBox("Export To FBX")
        self.exportTab_layout_frame.setAlignment(QtCore.Qt.AlignCenter)
        self.exportTab_layout_frame.setLayout(exportTab_layout)
        self.exportTab_layout_frame.hide()
        
        '''
        Miscellaneous Tab Layout
        '''
        misc_tab_layout = QtWidgets.QVBoxLayout()
        
        optimizeButton = QtWidgets.QVBoxLayout()
        optimizeButton.addWidget(self.optimize_rig_btn)
        optimizeButton_grp = QtWidgets.QGroupBox("Optimize Rig")
        optimizeButton_grp.setAlignment(QtCore.Qt.AlignCenter)
        optimizeButton_grp.setLayout(optimizeButton)
        misc_tab_layout.addWidget(optimizeButton_grp)
        
        combineShape = QtWidgets.QVBoxLayout()
        combineShape.addWidget(self.combine_shapeNode_btn)
        combineShape_grp = QtWidgets.QGroupBox("Select the Objects to Combine its Shape")
        combineShape_grp.setAlignment(QtCore.Qt.AlignCenter)
        combineShape_grp.setLayout(combineShape)
        misc_tab_layout.addWidget(combineShape_grp)
        
        selectSkinnedJnts = QtWidgets.QVBoxLayout()
        selectSkinnedJnts.addWidget(self.select_skinnedJnts_btn)
        selectSkinnedJnts_grp = QtWidgets.QGroupBox("Select Mesh and Click the Button")
        selectSkinnedJnts_grp.setAlignment(QtCore.Qt.AlignCenter)
        selectSkinnedJnts_grp.setLayout(selectSkinnedJnts)
        misc_tab_layout.addWidget(selectSkinnedJnts_grp)
                
        createIKControllerSize_layout = QtWidgets.QFormLayout()
        createIKControllerSize_layout.addRow ("Controller Size", self.createIKControllerSize_sb)
        createIKControllerSize_layout.setAlignment(QtCore.Qt.AlignCenter)
        
        createIK = QtWidgets.QVBoxLayout()
        createIK.addLayout(createIKControllerSize_layout)
        createIK.addWidget(self.create_IK_btn)
        createIK_grp = QtWidgets.QGroupBox("Select 3 Joints in a Chain to Create IK")
        createIK_grp.setAlignment(QtCore.Qt.AlignCenter)
        createIK_grp.setLayout(createIK)
        misc_tab_layout.addWidget(createIK_grp)
        
        misc_tab_layout.addStretch(0)       
        
        self.misc_layout_frame = QtWidgets.QGroupBox("Miscellaneous")
        self.misc_layout_frame.setAlignment(QtCore.Qt.AlignCenter)
        self.misc_layout_frame.setLayout(misc_tab_layout)
        self.misc_layout_frame.hide()
                 
        '''
        Range of Motion (ROM) Layout
        '''   
                   
        rom_main_gridLayout = QtWidgets.QGridLayout()
        rom_main_gridLayout.setHorizontalSpacing(5)
        rom_main_gridLayout.setColumnStretch(0,0)
        rom_main_gridLayout.setColumnStretch(1,1)
        rom_main_gridLayout.setColumnStretch(2,1)
        rom_main_gridLayout.setColumnStretch(3,1)
        
        rom_main_gridLayout.setColumnMinimumWidth (1,50)
        rom_main_gridLayout.setColumnMinimumWidth (2,50)
        rom_main_gridLayout.setColumnMinimumWidth (3,50)
        
        
        rom_main_gridLayout.addWidget (QtWidgets.QLabel(""), 0, 0)
        rom_main_gridLayout.addWidget (self.XLabel_label, 0, 1)
        rom_main_gridLayout.addWidget (self.YLabel_label, 0, 2)
        rom_main_gridLayout.addWidget (self.ZLabel_label, 0, 3)
        
        rom_main_gridLayout.addWidget (QtWidgets.QLabel("+ve"), 1, 0)
        rom_main_gridLayout.addWidget (self.rotXP_cb, 1, 1)
        rom_main_gridLayout.addWidget (self.rotYP_cb, 1, 2)
        rom_main_gridLayout.addWidget (self.rotZP_cb, 1, 3)
        
        rom_main_gridLayout.addWidget (QtWidgets.QLabel("-ve"), 2, 0)
        rom_main_gridLayout.addWidget (self.rotXN_cb, 2, 1)
        rom_main_gridLayout.addWidget (self.rotYN_cb, 2, 2)
        rom_main_gridLayout.addWidget (self.rotZN_cb, 2, 3)
        
        rom_main_gridLayout.addWidget (QtWidgets.QLabel(""), 3, 0, 1, 4)
        
        rom_main_gridLayout.addWidget (QtWidgets.QLabel("Rotate Angle"), 4, 0)
        rom_main_gridLayout.addWidget (self.angleBox_sb, 4, 1)
        
        rom_main_gridLayout.addWidget (QtWidgets.QLabel("Frame Padding"), 5, 0)
        rom_main_gridLayout.addWidget (self.framePad_sb, 5, 1)
        
        rom_main_gridLayout.addWidget (QtWidgets.QLabel("Rotate Angle"), 6, 0)
        rom_main_gridLayout.addWidget (self.frameStart_sb, 6, 1)
        
        rom_main_gridLayout.addWidget (QtWidgets.QLabel(""), 7, 0, 1, 4)
        
        rom_main_gridLayout.addWidget (self.rom_delete_key_btn, 8, 0, 1, 4)
        
        rom_bottomSpacing = QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        rom_main_gridLayout.addItem (rom_bottomSpacing, 9, 0)
        
        self.rom_layout_frame = QtWidgets.QGroupBox("Range of Motion (ROM)")
        self.rom_layout_frame.setAlignment(QtCore.Qt.AlignCenter)
        self.rom_layout_frame.setLayout(rom_main_gridLayout)
        self.rom_layout_frame.hide()
                 
        
        '''
        Custom Window Items Layout
        '''
        custom_window_items_layout = QtWidgets.QVBoxLayout()
        custom_window_items_layout.addWidget(self.search_replace_frame)
        custom_window_items_layout.addWidget(self.createController_layout_frame)
        custom_window_items_layout.addWidget(self.controllerText_frame)
        custom_window_items_layout.addWidget(self.exportTab_layout_frame)
        custom_window_items_layout.addWidget(self.rom_layout_frame)
        custom_window_items_layout.addWidget(self.misc_layout_frame)
        
        '''       
        Custom Window Layout
        '''
        custom_window_layout = QtWidgets.QHBoxLayout()
        custom_window_layout.addWidget(self.custom_list)  
        custom_window_layout.addLayout(custom_window_items_layout) 
        self.custom_window_layout_frame = QtWidgets.QFrame()
        self.custom_window_layout_frame.setLayout(custom_window_layout)
        
        '''
        CUSTOM WINDOW LAYOUT
        END
        '''
        
        '''
        BUILT-IN WINDOW LAYOUT
        START
        '''
        '''
        General Buttons
        '''
        builtIn_general_layout1 = QtWidgets.QHBoxLayout()
        builtIn_general_layout1.addWidget(self.locator_built_btn)
        builtIn_general_layout1.addWidget(self.deleteKeys_built_btn)
        builtIn_general_layout1.addWidget(self.deleteHistory_built_btn)
        builtIn_general_layout1.addWidget(self.duplicate_built_btn)
        builtIn_general_layout1.addWidget(self.parent_built_btn)
        builtIn_general_layout1.addWidget(self.unParent_built_btn)
        builtIn_general_layout2 = QtWidgets.QHBoxLayout()
        builtIn_general_layout2.addWidget(self.hierachy_built_btn)
        builtIn_general_layout2.addWidget(self.freezeTrans_built_btn)
        builtIn_general_layout2.addWidget(self.resetTrans_built_btn)
        builtIn_general_layout2.addWidget(self.centerPivot_built_btn)
        builtIn_general_layout2.addWidget(self.disHideLRA_built_btn)
        
        builtIn_general_layout = QtWidgets.QVBoxLayout()
        builtIn_general_layout.addLayout(builtIn_general_layout1)
        builtIn_general_layout.addLayout(builtIn_general_layout2)
        builtIn_general_layout_grp = QtWidgets.QGroupBox ("General")
        builtIn_general_layout_grp.setAlignment(QtCore.Qt.AlignCenter)
        builtIn_general_layout_grp.setLayout(builtIn_general_layout)
        
        '''
        Joint Buttons
        '''
        builtIn_joint_layout = QtWidgets.QHBoxLayout()
        builtIn_joint_layout.addWidget(self.createJoint_built_btn)
        builtIn_joint_layout.addWidget(self.mirrorJoint_built_btn)
        builtIn_joint_layout.addWidget(self.orientJoint_built_btn)
        builtIn_joint_layout.addWidget(self.createIKJoint_built_btn)
        builtIn_joint_layout.addWidget(self.splineIKJoint_built_btn)
        builtIn_joint_layout.addWidget(self.jointSizeJoint_built_btn)
        builtIn_joint_layout_grp = QtWidgets.QGroupBox ("Joint")
        builtIn_joint_layout_grp.setAlignment(QtCore.Qt.AlignCenter)
        builtIn_joint_layout_grp.setLayout(builtIn_joint_layout)
        
        '''
        Skinning Buttons
        '''
        builtIn_skinning_layout1 = QtWidgets.QHBoxLayout()
        builtIn_skinning_layout1.addWidget(self.bindSkin_built_btn)
        builtIn_skinning_layout1.addWidget(self.unBindSkin_built_btn)
        builtIn_skinning_layout1.addWidget(self.bindPoseSkin_built_btn)
        builtIn_skinning_layout1.addWidget(self.paintSkin_built_btn)
        builtIn_skinning_layout1.addWidget(self.mirrorSkin_built_btn)
        builtIn_skinning_layout1.addWidget(self.copyWeightsSkin_built_btn)
        builtIn_skinning_layout2 = QtWidgets.QHBoxLayout()     
        builtIn_skinning_layout2.addWidget(self.smoothSkin_built_btn)   
        builtIn_skinning_layout2.addWidget(self.copyVertexSkin_built_btn)
        builtIn_skinning_layout2.addWidget(self.pasteVertexSkin_built_btn)
        builtIn_skinning_layout2.addWidget(self.setInfluenceSkin_built_btn)
        builtIn_skinning_layout2.addWidget(self.addInfluenceSkin_built_btn)
        builtIn_skinning_layout2.addWidget(self.removeInfluenceSkin_built_btn)
        builtIn_skinning_layout3 = QtWidgets.QHBoxLayout()     
        builtIn_skinning_layout3.addWidget(self.pruneSkin_built_btn)
        builtIn_skinning_layout3.addWidget(self.bakeDeformSkin_built_btn)
        
        builtIn_skinning_layout = QtWidgets.QVBoxLayout()
        builtIn_skinning_layout.addLayout(builtIn_skinning_layout1)
        builtIn_skinning_layout.addLayout(builtIn_skinning_layout2)
        builtIn_skinning_layout.addLayout(builtIn_skinning_layout3)
        builtIn_skinning_layout_grp = QtWidgets.QGroupBox ("Skinning")
        builtIn_skinning_layout_grp.setAlignment(QtCore.Qt.AlignCenter)
        builtIn_skinning_layout_grp.setLayout(builtIn_skinning_layout)
        
        '''
        Deform Buttons
        '''
        builtIn_deform_layout = QtWidgets.QHBoxLayout()
        builtIn_deform_layout.addWidget(self.blendShapeDeform_built_btn)
        builtIn_deform_layout.addWidget(self.poseSpaceDeform_built_btn)
        builtIn_deform_layout.addWidget(self.clusterDeform_built_btn)
        builtIn_deform_layout_grp = QtWidgets.QGroupBox ("Deform")
        builtIn_deform_layout_grp.setAlignment(QtCore.Qt.AlignCenter)
        builtIn_deform_layout_grp.setLayout(builtIn_deform_layout)
        
        '''
        Constraint Buttons
        '''
        builtIn_constraint_layout = QtWidgets.QHBoxLayout()
        builtIn_constraint_layout.addWidget(self.parentConstraint_built_btn)
        builtIn_constraint_layout.addWidget(self.pointConstraint_built_btn)
        builtIn_constraint_layout.addWidget(self.orientConstraint_built_btn)
        builtIn_constraint_layout.addWidget(self.scaleConstraint_built_btn)
        builtIn_constraint_layout.addWidget(self.poleVectorConstraint_built_btn)
        builtIn_constraint_layout.addWidget(self.aimConstraint_built_btn)
        builtIn_constraint_layout_grp = QtWidgets.QGroupBox ("Constraint")
        builtIn_constraint_layout_grp.setAlignment(QtCore.Qt.AlignCenter)
        builtIn_constraint_layout_grp.setLayout(builtIn_constraint_layout)
        
        '''
        Windows Buttons
        '''
        builtIn_editor_layout1 = QtWidgets.QHBoxLayout()
        builtIn_editor_layout1.addWidget(self.connectionWindow_built_btn)
        builtIn_editor_layout1.addWidget(self.componentWindow_built_btn)
        builtIn_editor_layout1.addWidget(self.nodeWindow_built_btn)
        builtIn_editor_layout1.addWidget(self.channelWindow_built_btn)
        builtIn_editor_layout2 = QtWidgets.QHBoxLayout()
        builtIn_editor_layout2.addWidget(self.setDrivenKeyWindow_built_btn)
        builtIn_editor_layout2.addWidget(self.shapeWindow_built_btn)
        builtIn_editor_layout2.addWidget(self.poseWindow_built_btn)
        builtIn_editor_layout2.addWidget(self.graphWindow_built_btn)
        
        builtIn_editor_layout = QtWidgets.QVBoxLayout()
        builtIn_editor_layout.addLayout(builtIn_editor_layout1)
        builtIn_editor_layout.addLayout(builtIn_editor_layout2)
        builtIn_editor_layout_grp = QtWidgets.QGroupBox ("Windows")
        builtIn_editor_layout_grp.setAlignment(QtCore.Qt.AlignCenter)
        builtIn_editor_layout_grp.setLayout(builtIn_editor_layout)
        
        
        '''
        Built-In Window Items
        '''
        builtIn_window_layout = QtWidgets.QVBoxLayout()
        builtIn_window_layout.addWidget (builtIn_general_layout_grp)
        builtIn_window_layout.addWidget (builtIn_joint_layout_grp)
        builtIn_window_layout.addWidget (builtIn_skinning_layout_grp)
        builtIn_window_layout.addWidget (builtIn_deform_layout_grp)
        builtIn_window_layout.addWidget (builtIn_constraint_layout_grp)
        builtIn_window_layout.addWidget (builtIn_editor_layout_grp)
        builtIn_window_layout.addWidget (self.builtIn_label)
        self.builtIn_window_layout_frame = QtWidgets.QFrame()
        self.builtIn_window_layout_frame.setLayout(builtIn_window_layout)
        self.builtIn_window_layout_frame.hide()
        '''
        BUILT-IN WINDOW LAYOUT
        END
        '''
        
        '''
        CONTROL RIG WINDOW LAYOUT
        START
        '''
        '''
        Control Rig Form Layout
        '''
        controlRig_layout = QtWidgets.QVBoxLayout()
        
        sideIndicator_form_layout = QtWidgets.QFormLayout()
        sideIndicator_form_layout.addRow("Left Joint Indicator:", self.left_joints_le)
        sideIndicator_form_layout.addRow("Right Joint Indicator:", self.right_joints_le)
        sideIndicator_form_layout.addRow("Controller Size:", self.controllerSize_controlRig_sb)
        controlRig_layout.addLayout(sideIndicator_form_layout)
        
        pelvis_layout = QtWidgets.QHBoxLayout()
        pelvis_layout.addWidget(self.pelvis_le)
        pelvis_layout.addWidget(self.pelvis_btn)
        
        spine1_layout = QtWidgets.QHBoxLayout()
        spine1_layout.addWidget(self.spine1_le)
        spine1_layout.addWidget(self.spine1_btn)
        
        chest_layout = QtWidgets.QHBoxLayout()
        chest_layout.addWidget(self.chest_le)
        chest_layout.addWidget(self.chest_btn)
        
        neck_layout = QtWidgets.QHBoxLayout()
        neck_layout.addWidget(self.neck_le)
        neck_layout.addWidget(self.neck_btn)
        
        head_layout = QtWidgets.QHBoxLayout()
        head_layout.addWidget(self.head_le)
        head_layout.addWidget(self.head_btn)
        
        clavicle_layout = QtWidgets.QHBoxLayout()
        clavicle_layout.addWidget(self.clavicle_le)
        clavicle_layout.addWidget(self.clavicle_btn)
        
        armIKFK_layout = QtWidgets.QHBoxLayout()
        armIKFK_layout.addWidget(self.armFK_cb)
        armIKFK_layout.addWidget(self.armIK_cb)
        
        shoulder_layout = QtWidgets.QHBoxLayout()
        shoulder_layout.addWidget(self.shoulder_le)
        shoulder_layout.addWidget(self.shoulder_btn)
        
        elbow_layout = QtWidgets.QHBoxLayout()
        elbow_layout.addWidget(self.elbow_le)
        elbow_layout.addWidget(self.elbow_btn)
        
        wrist_layout = QtWidgets.QHBoxLayout()
        wrist_layout.addWidget(self.wrist_le)
        wrist_layout.addWidget(self.wrist_btn)
        
        
        legIKFK_layout = QtWidgets.QHBoxLayout()
        legIKFK_layout.addWidget(self.legFK_cb)
        legIKFK_layout.addWidget(self.legIK_cb)
        
        thigh_layout = QtWidgets.QHBoxLayout()
        thigh_layout.addWidget(self.thigh_le)
        thigh_layout.addWidget(self.thigh_btn)
        
        knee_layout = QtWidgets.QHBoxLayout()
        knee_layout.addWidget(self.knee_le)
        knee_layout.addWidget(self.knee_btn)
        
        ankle_layout = QtWidgets.QHBoxLayout()
        ankle_layout.addWidget(self.ankle_le)
        ankle_layout.addWidget(self.ankle_btn)
        
        ball_layout = QtWidgets.QHBoxLayout()
        ball_layout.addWidget(self.ball_le)
        ball_layout.addWidget(self.ball_btn)
    
        jointInput_form_layout = QtWidgets.QFormLayout()
        jointInput_form_layout.addRow("Pelvis", pelvis_layout)
        jointInput_form_layout.addRow("Base Spine", spine1_layout)
        jointInput_form_layout.addRow("Chest", chest_layout)
        jointInput_form_layout.addRow("Base Neck", neck_layout)
        jointInput_form_layout.addRow("Head", head_layout)
        jointInput_form_layout.addRow("Clavicle", clavicle_layout)
        jointInput_form_layout.addRow("Arm", armIKFK_layout)
        jointInput_form_layout.addRow("Shoulder", shoulder_layout)
        jointInput_form_layout.addRow("Elbow", elbow_layout)
        jointInput_form_layout.addRow("Wrist", wrist_layout)
        jointInput_form_layout.addRow("Leg", legIKFK_layout)
        jointInput_form_layout.addRow("Thigh", thigh_layout)
        jointInput_form_layout.addRow("Knee", knee_layout)
        jointInput_form_layout.addRow("Ankle", ankle_layout)
        jointInput_form_layout.addRow("Ball", ball_layout)
        jointInput_form_layout.addRow("", self.footRollControls_cb)
        
        jointInput_form_layout_frame = QtWidgets.QGroupBox("Select from the Left Side of the Character")
        jointInput_form_layout_frame.setAlignment(QtCore.Qt.AlignCenter)
        jointInput_form_layout_frame.setLayout(jointInput_form_layout)
        controlRig_layout.addWidget(jointInput_form_layout_frame)
        
        
        self.controlRig_form_layout_frame = QtWidgets.QGroupBox("Create Biped Control Rig")
        self.controlRig_form_layout_frame.setAlignment(QtCore.Qt.AlignCenter)
        self.controlRig_form_layout_frame.setLayout(controlRig_layout)
        self.controlRig_form_layout_frame.hide()
        
        '''
        CONTROL RIG WINDOW LAYOUT
        END
        '''    
           
        '''
        Main Layout
        '''
        main_layout = QtWidgets.QVBoxLayout(self) #Determines the layout type for the window and parents itself to 'self' (the instance of the dialog)
 
        main_layout.addLayout(mainCombo_layout)
        main_layout.addWidget (self.custom_window_layout_frame)
        main_layout.addWidget (self.builtIn_window_layout_frame)
        main_layout.addWidget(self.controlRig_form_layout_frame)
        main_layout.addWidget(self.button_grp) #Adding the horizontal button layout from above to the 'main_layout'
    
    #Place to create connections between the widgets in the window (for eg: what to do when button clicked or what to do when textfiled is edited)
    def create_connection (self):
        #Closes the window when the cancel button is pressed/clicked
        self.cancel_btn.clicked.connect(self.close)
        
        self.helpDocs_btn.clicked.connect(showHelp)
        
        self.custom_list.currentItemChanged.connect(self.custom_list_change)
        
        self.main_comboBox.activated[str].connect(self.on_activated_text) #Looks for the method/function 'on_activated_text' when the item on the dropdown is changed
        
        '''
        SEARCH/REPLACE NAMES
        START
        '''
        #Search and Replace Names
        self.search_apply_btn.clicked.connect (lambda: searchReplaceNames(self.search_name_le.text(), self.replace_name_le.text(), self.hierachy_name_rb.isChecked(), self.selected_name_rb.isChecked(), self.all_name_rb.isChecked()))
        #Prefix Name
        self.addPrefix_btn.clicked.connect(lambda: prefixName(self.addPrefix_le.text(), self.hierachy_name_rb.isChecked(), self.selected_name_rb.isChecked(), self.all_name_rb.isChecked()))
        #Suffix Name
        self.addSuffix_btn.clicked.connect(lambda: suffixName(self.addSuffix_le.text(), self.hierachy_name_rb.isChecked(), self.selected_name_rb.isChecked(), self.all_name_rb.isChecked()))
        #Padding Rename
        self.numRename_btn.clicked.connect (lambda: paddingRename (self.numRename_le.text(), self.startNumber_sb.value(), self.paddingNumber_sb.value(), self.stepsNumber_sb.value(), self.hierachy_name_rb.isChecked(), self.selected_name_rb.isChecked(), self.all_name_rb.isChecked()))
        '''
        SEARCH/REPLACE NAMES
        END
        '''
        
        '''
        CREATE CONTROLLERS
        START
        '''
        self.controllerGroup_sb.valueChanged.connect(self.groupNumber_createController)
        self.controller_list.currentItemChanged.connect(self.controller_list_change)
        self.controller_apply_btn.clicked.connect(lambda: createController(self.controllerName_le.text(), self.controllerSuffix_le.text(), self.controllerSize_sb.value(), self.controllerForceLabel_cb.checkState(), self.controllerSnapSelected_cb.checkState(), self.controller_list.item(self.controller_list.currentRow()).text(), self.controllerGroup_sb.value(), self.firstGroupSuffix_le.text(), self.secondGroupSuffix_le.text(), self.thirdGroupSuffix_le.text(), self.fourthGroupSuffix_le.text(), self.controllerColor_ccb.getColor()))
        '''
        CREATE CONTROLLERS
        END
        '''
        
        '''
        CREATE CONTROLLER FROM TEXT CONNECTION
        START
        '''
        #Button to create the controller from the given text
        #'lambda:' allows me to pass arguments through the functions (without lambda, I cannot pass the text value to the 'createControllerText' function)
        self.controller_text_btn.clicked.connect(lambda: createControllerText(self.controller_text_name_le.text(), self.controller_text_font_combo.currentText()))
        '''
        CREATE CONTROLLER FROM TEXT CONNECTION
        END
        '''
        
        '''
        EXPORT TO FBX CONNECTION
        START
        '''
        self.exportSelected_rb.toggled.connect(self.deSelectAnimationBox)
        self.exportModel_rb.toggled.connect(self.deSelectAnimationBox)
        self.exportModelRig_rb.toggled.connect(self.deSelectAnimationBox)
        self.exportAll_rb.toggled.connect(self.deSelectAnimationBox)
        self.exportAnimation_rb.toggled.connect(self.selectAnimationBox)
        self.exportAnimationModel_rb.toggled.connect(self.selectAnimationBox)
        
        self.exportProjecPath_btn.clicked.connect(self.select_unityUnreal_export_location)
        
        self.unityEngineSelected_rb.toggled.connect(self.exportPathDefUnity)
        self.unrealEngineSelected_rb.toggled.connect(self.exportPathDefUnreal)
        self.noneEngineSelected_rb.toggled.connect(self.exportPathDefNone)
        
        self.exportOptions_comboBox.activated[str].connect(self.exportOptionComboActivated)
        
        self.exportAnimations_cb.toggled.connect(self.exportAnimationToggle)
        self.exportBakeAnimation_cb.toggled.connect(self.exportBakeAnimationToggle)
        self.exportUnitsAuto_cb.toggled.connect(self.exportUnitAutoToggle)
        
        self.exportApply_btn.clicked.connect (self.exportButtonPressed)
        '''
        EXPORT TO FBX CONNECTION
        END
        '''
                
        '''
        RANGE OF MOTION (ROM) CONNECTION
        START
        '''
        self.rom_delete_key_btn.clicked.connect (cmds.DeleteKeys)
        
        self.rom_apply_btn.clicked.connect(lambda: createROM(self.rotXP_cb.checkState(),self.rotYP_cb.checkState(),self.rotZP_cb.checkState(),self.rotXN_cb.checkState(),self.rotYN_cb.checkState(),self.rotZN_cb.checkState(),self.angleBox_sb.value(),self.framePad_sb.value(),self.frameStart_sb.value()))
        '''
        RANGE OF MOTION (ROM) CONNECTION
        START
        '''  
        
        '''
        MISCELLANEOUS TAB BUTTONS CONNECTION
        START
        '''
        #Button to create the IK Chain
        self.create_IK_btn.clicked.connect(lambda: createIKChain(self.createIKControllerSize_sb.value()))
        
        #Button to delete Unknown Nodes
        self.optimize_rig_btn.clicked.connect(deleteUnknownNodes)
        
        #Button to selected skinned joints in a mesh
        self.select_skinnedJnts_btn.clicked.connect(selectSkinnedJoints)
        
        #Button for Combine Shape Nodes
        self.combine_shapeNode_btn.clicked.connect(combineShape)
        '''
        MISCELLANEOUS TAB BUTTONS CONNECTION
        END
        '''
        
        '''
        BUILT-IN BUTTON CONNECTIONS
        START
        '''
        #General Options
        self.locator_built_btn.clicked.connect (cmds.CreateLocator)
        
        self.deleteKeys_built_btn.clicked.connect (cmds.DeleteKeys)
        self.deleteKeys_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.deleteKeys_built_btn.customContextMenuRequested.connect(cmds.DeleteKeysOptions)
        
        self.deleteHistory_built_btn.clicked.connect (cmds.DeleteHistory())
        
        self.duplicate_built_btn.clicked.connect (cmds.Duplicate)
        
        self.parent_built_btn.clicked.connect (cmds.Parent)
        self.parent_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.parent_built_btn.customContextMenuRequested.connect(cmds.ParentOptions)
        
        self.unParent_built_btn.clicked.connect (cmds.Unparent)
        self.unParent_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.unParent_built_btn.customContextMenuRequested.connect(cmds.UnparentOptions)
        
        self.hierachy_built_btn.clicked.connect (cmds.SelectHierarchy)
        
        self.freezeTrans_built_btn.clicked.connect (cmds.FreezeTransformations)
        self.freezeTrans_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.freezeTrans_built_btn.customContextMenuRequested.connect(cmds.FreezeTransformationsOptions)
        
        self.resetTrans_built_btn.clicked.connect (cmds.ResetTransformations)
        self.resetTrans_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.resetTrans_built_btn.customContextMenuRequested.connect(cmds.ResetTransformationsOptions)
        
        self.centerPivot_built_btn.clicked.connect (cmds.CenterPivot)
        
        self.disHideLRA_built_btn.clicked.connect (cmds.ToggleLocalRotationAxes)
        
        #Joints
        self.createJoint_built_btn.clicked.connect (cmds.JointTool)
        self.createJoint_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.createJoint_built_btn.customContextMenuRequested.connect(cmds.JointToolOptions)
        
        self.mirrorJoint_built_btn.clicked.connect (cmds.MirrorJoint)
        self.mirrorJoint_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.mirrorJoint_built_btn.customContextMenuRequested.connect(cmds.MirrorJointOptions)
        
        self.orientJoint_built_btn.clicked.connect (cmds.OrientJoint)
        self.orientJoint_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.orientJoint_built_btn.customContextMenuRequested.connect(cmds.OrientJointOptions)
        
        self.createIKJoint_built_btn.clicked.connect (cmds.IKHandleTool)
        self.createIKJoint_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.createIKJoint_built_btn.customContextMenuRequested.connect(cmds.IKHandleToolOptions)
        
        self.splineIKJoint_built_btn.clicked.connect (cmds.IKSplineHandleTool)
        self.splineIKJoint_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.splineIKJoint_built_btn.customContextMenuRequested.connect(cmds.IKSplineHandleToolOptions)
        
        self.jointSizeJoint_built_btn.clicked.connect (cmds.JdsWin)
        
        #Skinning
        self.bindSkin_built_btn.clicked.connect (cmds.SmoothBindSkin)
        self.bindSkin_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.bindSkin_built_btn.customContextMenuRequested.connect(cmds.SmoothBindSkinOptions)
        
        self.unBindSkin_built_btn.clicked.connect (cmds.DetachSkin)
        self.unBindSkin_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.unBindSkin_built_btn.customContextMenuRequested.connect(cmds.DetachSkinOptions)
        
        self.bindPoseSkin_built_btn.clicked.connect (cmds.GoToBindPose)
        
        self.paintSkin_built_btn.clicked.connect (cmds.ArtPaintSkinWeightsTool)
        self.paintSkin_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.paintSkin_built_btn.customContextMenuRequested.connect(cmds.ArtPaintSkinWeightsToolOptions)
        
        self.mirrorSkin_built_btn.clicked.connect (cmds.MirrorSkinWeights)
        self.mirrorSkin_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.mirrorSkin_built_btn.customContextMenuRequested.connect(cmds.MirrorSkinWeightsOptions)
        
        self.copyWeightsSkin_built_btn.clicked.connect (cmds.CopySkinWeights)
        self.copyWeightsSkin_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.copyWeightsSkin_built_btn.customContextMenuRequested.connect(cmds.CopySkinWeightsOptions)
        
        self.smoothSkin_built_btn.clicked.connect (cmds.SmoothSkinWeights)
        self.smoothSkin_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.smoothSkin_built_btn.customContextMenuRequested.connect(cmds.SmoothSkinWeightsOptions)
        
        self.copyVertexSkin_built_btn.clicked.connect (cmds.CopyVertexWeights)
        
        self.pasteVertexSkin_built_btn.clicked.connect (cmds.PasteVertexWeights)
        
        self.setInfluenceSkin_built_btn.clicked.connect (cmds.SetMaxInfluences)
        
        self.addInfluenceSkin_built_btn.clicked.connect (cmds.AddInfluence)
        self.addInfluenceSkin_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.addInfluenceSkin_built_btn.customContextMenuRequested.connect(cmds.AddInfluenceOptions)
        
        self.removeInfluenceSkin_built_btn.clicked.connect (cmds.RemoveInfluence)
        
        self.pruneSkin_built_btn.clicked.connect (cmds.PruneSmallWeights)
        self.pruneSkin_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.pruneSkin_built_btn.customContextMenuRequested.connect(cmds.PruneSmallWeightsOptions)
        
        self.bakeDeformSkin_built_btn.clicked.connect (cmds.BakeDeformerTool)
        
        #Deform
        self.blendShapeDeform_built_btn.clicked.connect (cmds.CreateBlendShape)
        self.blendShapeDeform_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.blendShapeDeform_built_btn.customContextMenuRequested.connect(cmds.CreateBlendShapeOptions)
        
        self.poseSpaceDeform_built_btn.clicked.connect (cmds.CreatePoseInterpolator)
        self.poseSpaceDeform_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.poseSpaceDeform_built_btn.customContextMenuRequested.connect(cmds.CreatePoseInterpolatorOptions)
        
        self.clusterDeform_built_btn.clicked.connect (cmds.CreateCluster)
        self.clusterDeform_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.clusterDeform_built_btn.customContextMenuRequested.connect(cmds.CreateClusterOptions)
        
        #Constraint
        self.parentConstraint_built_btn.clicked.connect (cmds.ParentConstraint)
        self.parentConstraint_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.parentConstraint_built_btn.customContextMenuRequested.connect(cmds.ParentConstraintOptions)
        
        self.pointConstraint_built_btn.clicked.connect (cmds.PointConstraint)
        self.pointConstraint_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.pointConstraint_built_btn.customContextMenuRequested.connect(cmds.PointConstraintOptions)
        
        self.orientConstraint_built_btn.clicked.connect (cmds.OrientConstraint)
        self.orientConstraint_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.orientConstraint_built_btn.customContextMenuRequested.connect(cmds.OrientConstraintOptions)
        
        self.scaleConstraint_built_btn.clicked.connect (cmds.ScaleConstraint)
        self.scaleConstraint_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.scaleConstraint_built_btn.customContextMenuRequested.connect(cmds.ScaleConstraintOptions)
        
        self.poleVectorConstraint_built_btn.clicked.connect (cmds.PoleVectorConstraint)
        self.poleVectorConstraint_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.poleVectorConstraint_built_btn.customContextMenuRequested.connect(cmds.PoleVectorConstraintOptions)
        
        self.aimConstraint_built_btn.clicked.connect (cmds.AimConstraint)
        self.aimConstraint_built_btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) #Creating a right mouse click option
        self.aimConstraint_built_btn.customContextMenuRequested.connect(cmds.AimConstraintOptions)
        
        #Windows 
        self.connectionWindow_built_btn.clicked.connect(cmds.ConnectionEditor)
        self.componentWindow_built_btn.clicked.connect(cmds.ComponentEditor)
        self.nodeWindow_built_btn.clicked.connect(cmds.NodeEditorWindow)
        self.channelWindow_built_btn.clicked.connect(cmds.ChannelControlEditor)
        self.setDrivenKeyWindow_built_btn.clicked.connect(cmds.SetDrivenKey)
        self.shapeWindow_built_btn.clicked.connect(cmds.ShapeEditor)
        self.poseWindow_built_btn.clicked.connect(cmds.PoseEditor)
        self.graphWindow_built_btn.clicked.connect(cmds.GraphEditor)
        '''
        BUILT-IN BUTTON CONNECTIONS
        END
        '''
        
        '''
        CUSTOM RIG BUTTON CONNECTIONS
        START
        '''
        self.pelvis_btn.clicked.connect(lambda: self.controlRigButtonPressed("pelvis"))
        self.spine1_btn.clicked.connect(lambda: self.controlRigButtonPressed("spine1"))
        self.chest_btn.clicked.connect(lambda: self.controlRigButtonPressed("chest"))
        self.neck_btn.clicked.connect(lambda: self.controlRigButtonPressed("neck"))
        self.head_btn.clicked.connect(lambda: self.controlRigButtonPressed("head"))
        self.clavicle_btn.clicked.connect(lambda: self.controlRigButtonPressed("clavicle"))
        self.shoulder_btn.clicked.connect(lambda: self.controlRigButtonPressed("shoulder"))
        self.elbow_btn.clicked.connect(lambda: self.controlRigButtonPressed("elbow"))
        self.wrist_btn.clicked.connect(lambda: self.controlRigButtonPressed("wrist"))
        self.thigh_btn.clicked.connect(lambda: self.controlRigButtonPressed("thigh"))
        self.knee_btn.clicked.connect(lambda: self.controlRigButtonPressed("knee"))
        self.ankle_btn.clicked.connect(lambda: self.controlRigButtonPressed("ankle"))
        self.ball_btn.clicked.connect(lambda: self.controlRigButtonPressed("ball"))
        self.footRollControls_cb.toggled.connect (self.footRollControlToggle)
        
        self.accept_btn.clicked.connect (lambda: createBipedControlRig(self.left_joints_le.text(), self.right_joints_le.text(), self.pelvis_le.text(), self.spine1_le.text(), self.chest_le.text(), self.neck_le.text(), self.head_le.text(), self.clavicle_le.text(), self.shoulder_le.text(), self.elbow_le.text(), self.wrist_le.text(), self.thigh_le.text(), self.knee_le.text(), self.ankle_le.text(), self.ball_le.text(), self.armFK_cb.checkState(), self.armIK_cb.checkState(), self.legFK_cb.checkState(), self.legIK_cb.checkState(), self.controllerSize_controlRig_sb.value(),self.footRollControls_cb.checkState()))
        '''
        CUSTOM RIG BUTTON CONNECTIONS
        START
        '''
    
    '''
    Create Controller Group Number Change
    '''
    def groupNumber_createController(self, value):
        if (value == 0):
            self.firstGroupSuffix_le.setEnabled(False)
            self.secondGroupSuffix_le.setEnabled(False)
            self.thirdGroupSuffix_le.setEnabled(False)
            self.fourthGroupSuffix_le.setEnabled(False)            
        elif (value == 1):
            self.firstGroupSuffix_le.setEnabled(True)
            self.secondGroupSuffix_le.setEnabled(False)
            self.thirdGroupSuffix_le.setEnabled(False)
            self.fourthGroupSuffix_le.setEnabled(False)
        elif (value == 2):
            self.firstGroupSuffix_le.setEnabled(True)
            self.secondGroupSuffix_le.setEnabled(True)
            self.thirdGroupSuffix_le.setEnabled(False)
            self.fourthGroupSuffix_le.setEnabled(False)
        elif (value == 3):
            self.firstGroupSuffix_le.setEnabled(True)
            self.secondGroupSuffix_le.setEnabled(True)
            self.thirdGroupSuffix_le.setEnabled(True)
            self.fourthGroupSuffix_le.setEnabled(False)
        elif (value == 4):
            self.firstGroupSuffix_le.setEnabled(True)
            self.secondGroupSuffix_le.setEnabled(True)
            self.thirdGroupSuffix_le.setEnabled(True)
            self.fourthGroupSuffix_le.setEnabled(True)
    
    '''
    Custom List Change Method
    '''
    def custom_list_change(self, item):
        selected_item = item.text()
        
        if (selected_item == "Search/Replace Names"):
            self.search_replace_frame.show()
            self.createController_layout_frame.hide()
            self.controllerText_frame.hide()
            self.exportTab_layout_frame.hide()
            self.rom_layout_frame.hide()
            self.misc_layout_frame.hide()
            self.setMinimumHeight(515)
            self.setMinimumWidth(550)
            self.resize (550,515)
            self.exportApply_btn.hide()
            self.rom_apply_btn.hide()
        elif (selected_item == "Create Controllers"):
            self.search_replace_frame.hide()
            self.createController_layout_frame.show()
            self.controllerText_frame.hide()
            self.exportTab_layout_frame.hide()
            self.rom_layout_frame.hide()
            self.misc_layout_frame.hide()
            self.setMinimumHeight(515)
            self.setMinimumWidth(560)
            self.resize (560,515)
            self.exportApply_btn.hide()
            self.rom_apply_btn.hide()
        elif (selected_item == "Create Controller from Text"):
            self.search_replace_frame.hide()
            self.createController_layout_frame.hide()
            self.controllerText_frame.show()
            self.exportTab_layout_frame.hide()
            self.rom_layout_frame.hide()
            self.misc_layout_frame.hide()
            self.setMinimumHeight(300)
            self.setMinimumWidth(460)
            self.resize (460,300)
            self.exportApply_btn.hide()
            self.rom_apply_btn.hide()
        elif (selected_item == "Export To FBX"):
            self.search_replace_frame.hide()
            self.createController_layout_frame.hide()
            self.controllerText_frame.hide()
            self.exportTab_layout_frame.show()
            self.rom_layout_frame.hide()
            self.misc_layout_frame.hide()
            self.setMinimumHeight(700)
            self.setMinimumWidth(893)
            self.resize (893,700)
            self.exportApply_btn.show()
            self.rom_apply_btn.hide()
        elif (selected_item == "Range of Motion (ROM)"):
            self.search_replace_frame.hide()
            self.createController_layout_frame.hide()
            self.controllerText_frame.hide()
            self.exportTab_layout_frame.hide()
            self.rom_layout_frame.show()
            self.misc_layout_frame.hide()
            self.setMinimumHeight(350)
            self.setMinimumWidth(490)
            self.resize (490,350)
            self.exportApply_btn.hide()
            self.rom_apply_btn.show()
        else:
            self.search_replace_frame.hide()
            self.createController_layout_frame.hide()
            self.controllerText_frame.hide()
            self.exportTab_layout_frame.hide()
            self.rom_layout_frame.hide()
            self.misc_layout_frame.show()
            self.setMinimumHeight(440)
            self.setMinimumWidth(460)
            self.resize (460,440)
            self.exportApply_btn.hide()
            self.rom_apply_btn.hide()
    
    '''
    Controller List Changed Variable
    '''    
    def controller_list_change (self, item):
        selected_controller_type = item.text()
        
        if (selected_controller_type == "Circle"):
            self.controllerImage_ciw.setImage("{0}circle.png".format(self.image_path))
        elif (selected_controller_type == "Square"):
            self.controllerImage_ciw.setImage("{0}square.png".format(self.image_path))
        elif (selected_controller_type == "Cube"):
            self.controllerImage_ciw.setImage("{0}cube.png".format(self.image_path))
        elif (selected_controller_type == "Hexagon"):
            self.controllerImage_ciw.setImage("{0}hexagon.png".format(self.image_path))
        elif (selected_controller_type == "Sphere"):
            self.controllerImage_ciw.setImage("{0}sphere.png".format(self.image_path))
        elif (selected_controller_type == "Cross"):
            self.controllerImage_ciw.setImage("{0}cross.png".format(self.image_path))
        elif (selected_controller_type == "Arrow"):
            self.controllerImage_ciw.setImage("{0}arrow.png".format(self.image_path))
        elif (selected_controller_type == "Arc Arrow"):
            self.controllerImage_ciw.setImage("{0}arcArrow.png".format(self.image_path))
        elif (selected_controller_type == "Double Arrow"):
            self.controllerImage_ciw.setImage("{0}doubleArrow.png".format(self.image_path))
        elif (selected_controller_type == "Curved Arrow"):
            self.controllerImage_ciw.setImage("{0}curvedArrow.png".format(self.image_path))
        elif (selected_controller_type == "Tube"):
            self.controllerImage_ciw.setImage("{0}tube.png".format(self.image_path))
        elif (selected_controller_type == "Gear"):
            self.controllerImage_ciw.setImage("{0}gear.png".format(self.image_path))
        elif (selected_controller_type == "Plus"):
            self.controllerImage_ciw.setImage("{0}plus.png".format(self.image_path))
        elif (selected_controller_type == "Triangle"):
            self.controllerImage_ciw.setImage("{0}triangle.png".format(self.image_path))
        elif (selected_controller_type == "Pyramid"):
            self.controllerImage_ciw.setImage("{0}pyramid.png".format(self.image_path))
        elif (selected_controller_type == "3D Diamond"):
            self.controllerImage_ciw.setImage("{0}3dDiamond.png".format(self.image_path))
        elif (selected_controller_type == "2D Diamond"):
            self.controllerImage_ciw.setImage("{0}2dDiamond.png".format(self.image_path))
        elif (selected_controller_type == "Diamond Sphere"):
            self.controllerImage_ciw.setImage("{0}diamondSphere.png".format(self.image_path))
            
    '''
    Export to FBX
    '''
    def deSelectAnimationBox(self):
        self.exportAnimations_cb.setChecked(False)
    
    def selectAnimationBox(self):
        self.exportAnimations_cb.setChecked(True)
        
        if (self.exportOptions_comboBox.currentText() == "Automatic"):
            self.exportBakeAnimation_cb.setEnabled(False)
        
    def select_unityUnreal_export_location (self):
        self.file_path = cmds.fileDialog2 (fileMode = 3, ds = 2, okc = "Select", caption = "Select Unity/Unreal Project Folder")
        if self.file_path:
            self.exportProjectPath_le.setText(self.file_path[0])
            
    def exportPathDefUnity(self, item):
        self.exportProjecPath_btn.setEnabled(True)
    
    def exportPathDefUnreal(self, item):
        self.exportProjecPath_btn.setEnabled(True)
    
    def exportPathDefNone(self, item):
        self.exportProjecPath_btn.setEnabled(False)
        
    @QtCore.Slot(str) #this decorator has the 'str' value
    def exportOptionComboActivated (self, textName):#To send the text for the item
        if (textName == "Automatic"):
            self.exportSmoothingGrp_cb.setEnabled(False)
            self.exportSmoothMesh_cb.setEnabled(False)
            self.exportRac_cb.setEnabled(False)
            self.exportTraingulate_cb.setEnabled(False)
            self.exportAnimations_cb.setEnabled(False)
            self.exportBakeAnimation_cb.setEnabled(False)
            self.exportBakeStart_sb.setEnabled(False)
            self.exportBakeEnd_sb.setEnabled(False)
            self.exportBakeSteps_sb.setEnabled(False)
            self.exportReSample_cb.setEnabled(False)
            self.exportUnitsAuto_cb.setEnabled(False)
            self.exportUnitsAuto_cb.setChecked(True)
            self.exportUpAxis_comboBox.setEnabled(False)
        else:
            self.exportSmoothingGrp_cb.setEnabled(True)
            self.exportSmoothMesh_cb.setEnabled(True)
            self.exportRac_cb.setEnabled(True)
            self.exportTraingulate_cb.setEnabled(True)
            self.exportAnimations_cb.setEnabled(True)
            self.exportUnitsAuto_cb.setEnabled(True)
            self.exportUpAxis_comboBox.setEnabled(True)
            
            if (self.exportAnimations_cb.isChecked()):
                self.exportBakeAnimation_cb.setEnabled(True)
            
            if (self.exportBakeAnimation_cb.isChecked()):
                self.exportBakeStart_sb.setEnabled(True)
                self.exportBakeEnd_sb.setEnabled(True)
                self.exportBakeSteps_sb.setEnabled(True)
                self.exportReSample_cb.setEnabled(True)
                
                
    
    def exportAnimationToggle(self, item):
        if item:
            self.exportBakeAnimation_cb.setEnabled(True)
        else:
            self.exportBakeAnimation_cb.setChecked(False)
            self.exportBakeAnimation_cb.setEnabled(False)
            
    def exportBakeAnimationToggle(self, item):
        if item:
            self.exportBakeStart_sb.setEnabled(True)
            self.exportBakeEnd_sb.setEnabled(True)
            self.exportBakeSteps_sb.setEnabled(True)
            self.exportReSample_cb.setEnabled(True)
        else:
            self.exportBakeStart_sb.setEnabled(False)
            self.exportBakeEnd_sb.setEnabled(False)
            self.exportBakeSteps_sb.setEnabled(False)
            self.exportReSample_cb.setEnabled(False)
            self.exportReSample_cb.setChecked(False)
        
    def exportUnitAutoToggle(self, item):
        if item:
            self.exportUnit_comboBox.setEnabled(False)
        else:
            self.exportUnit_comboBox.setEnabled(True)
    
    def exportButtonPressed(self):
        # Sending the values for export options script
        if (self.exportSmoothingGrp_cb.isChecked()):
            getSmoothingGRP = True
        else:
            getSmoothingGRP = False
        
        if (self.exportSmoothMesh_cb.isChecked()):
            getSmoothMesh = True
        else:
            getSmoothMesh = False
        
        if (self.exportRac_cb.isChecked()):
            getRAC = True
        else:
            getRAC = False
        
        if (self.exportTraingulate_cb.isChecked()):
            getTraingulate = True
        else:
            getTraingulate = False
        
        if (self.exportAnimations_cb.isChecked()):
            getAnimation = True
        else:
            getAnimation = False
        
        if (self.exportBakeAnimation_cb.isChecked()):
            getBakeAnimation = True
        else:
            getBakeAnimation = False
        
        getBakeStart = self.exportBakeStart_sb.value()
        getBakeEnd = self.exportBakeEnd_sb.value()
        getBakeStep = self.exportBakeSteps_sb.value()
        
        if (self.exportReSample_cb.isChecked()):
            getBakeReSample = True
        else:
            getBakeReSample = False
        
        if (self.exportUnitsAuto_cb.isChecked()):
            getUnits = True
        else:
            getUnits = False
        
        getUnitsConvert = self.exportUnit_comboBox.currentText()
        getAxisConvert = self.exportUpAxis_comboBox.currentText()
        
        selectedValuesForExport = [getSmoothingGRP, getSmoothMesh, getRAC, getTraingulate, getAnimation, getBakeAnimation, getBakeStart, getBakeEnd, getBakeStep, getBakeReSample, getUnits, getUnitsConvert, getAxisConvert]
        
        #Checking Selected Export Option
        if (self.exportSelected_rb.isChecked()):
            selectedExportOption = "Selected"
        elif (self.exportModel_rb.isChecked()):
            selectedExportOption = "Models"
        elif (self.exportModelRig_rb.isChecked()):
            selectedExportOption = "Models_and_Rig"
        elif (self.exportAnimationModel_rb.isChecked()):
            selectedExportOption = "Animations_with_Model"
        elif (self.exportAnimation_rb.isChecked()):
            selectedExportOption = "Animations_without_Model"
        elif (self.exportAll_rb.isChecked()):
            selectedExportOption = "All"
        
        #Checking if Automatic is selected or manual
        if (self.exportOptions_comboBox.currentText() == "Automatic"):
            autoManualOption = "Automatic"
            if (self.exportAnimationModel_rb.isChecked() or self.exportAnimation_rb.isChecked()):
                bakeSimulationBool = True
            else:
                bakeSimulationBool = False
        else:
            autoManualOption = "Manual"
            if (getBakeAnimation):
                bakeSimulationBool = True
            else:                
                bakeSimulationBool = True
                
        #Checking the selected engine
        if (self.unityEngineSelected_rb.isChecked()):
            gameEngineDir = self.file_path[0] + "/Assets"
        elif (self.unrealEngineSelected_rb.isChecked()):
            gameEngineDir = self.file_path[0] + "/Content"
        else:
            gameEngineDir = ""
        
        exportFileFilters = "FBX Export (*.fbx)"
        exportLocation = cmds.fileDialog2 (fileMode = 0, ds = 2, fileFilter = exportFileFilters, startingDirectory = gameEngineDir)
        
        exportSaveButtonPush (selectedExportOption, exportLocation, selectedValuesForExport, bakeSimulationBool, autoManualOption)
    '''
    Main Combo Button Method
    '''
    @QtCore.Slot(str) #this decorator has the 'str' value
    def on_activated_text (self, textName):#To send the text for the item
        self.default_main_comboBox = textName
        print ("ComboBox Text: {0}". format (self.default_main_comboBox))
        
        if (self.default_main_comboBox == "Built-In"):
            self.custom_window_layout_frame.hide ()
            self.controlRig_form_layout_frame.hide()
            self.builtIn_window_layout_frame.show()
            self.accept_btn.hide()
            self.exportApply_btn.hide()
            self.setMinimumHeight (700)
            self.setMinimumWidth (500)
            self.resize (500,700)
        elif (self.default_main_comboBox == "Helper Scripts"):
            self.custom_window_layout_frame.show ()
            self.controlRig_form_layout_frame.hide()
            self.builtIn_window_layout_frame.hide()
            self.accept_btn.hide()
            
            customItem = self.custom_list.currentItem()
            self.custom_list_change(customItem)
        else:
            self.custom_window_layout_frame.hide ()
            self.controlRig_form_layout_frame.show()
            self.builtIn_window_layout_frame.hide()
            self.accept_btn.show()
            self.exportApply_btn.hide()
            self.setMinimumHeight (750)
            self.setMinimumWidth (500)
            self.resize (500,750)
            
    '''
    Button Pressed Methods for Custom Rig Controls
    '''
    def controlRigButtonPressed(self, selected):
        selectedItem = cmds.ls(sl = True)
        if (len(selectedItem) == 1):
            if (selected == "pelvis"):
                self.pelvis_le.setText(selectedItem[0])
            elif (selected == "spine1"):
                self.spine1_le.setText(selectedItem[0])
            elif (selected == "chest"):
                self.chest_le.setText(selectedItem[0])
            elif (selected == "neck"):
                self.neck_le.setText(selectedItem[0])
            elif (selected == "head"):
                self.head_le.setText(selectedItem[0])
            elif (selected == "clavicle"):
                self.clavicle_le.setText(selectedItem[0])
            elif (selected == "shoulder"):
                self.shoulder_le.setText(selectedItem[0])
            elif (selected == "elbow"):
                self.elbow_le.setText(selectedItem[0])
            elif (selected == "wrist"):
                self.wrist_le.setText(selectedItem[0])
            elif (selected == "thigh"):
                self.thigh_le.setText(selectedItem[0])
            elif (selected == "knee"):
                self.knee_le.setText(selectedItem[0])
            elif (selected == "ankle"):
                self.ankle_le.setText(selectedItem[0])
            elif (selected == "ball"):
                self.ball_le.setText(selectedItem[0])
        else:
            #Give out an error message
            om.MGlobal.displayError("SELECT ONLY ONE JOINT PER TEXT FIELD")
            return
    
    def footRollControlToggle(self, item):
        with UndoContext():
            if item:
                self.heelLoc = cmds.spaceLocator(n = "L_heelPos_LOC", p = (0,0,0), a = True)
                cmds.setAttr ("L_heelPos_LOC.ty", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_heelPos_LOC.rx", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_heelPos_LOC.ry", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_heelPos_LOC.rz", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_heelPos_LOC.sx", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_heelPos_LOC.sy", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_heelPos_LOC.sz", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_heelPos_LOC.v", lock = True, keyable = False, channelBox = False)
                cmds.CenterPivot()
                
                self.ankleInLoc = cmds.spaceLocator(n = "L_ankleRollInPos_LOC", p = (0,0,0), a = True)
                cmds.move(-0.5,0,1)
                cmds.setAttr ("L_ankleRollInPos_LOC.ty", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_ankleRollInPos_LOC.rx", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_ankleRollInPos_LOC.ry", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_ankleRollInPos_LOC.rz", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_ankleRollInPos_LOC.sx", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_ankleRollInPos_LOC.sy", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_ankleRollInPos_LOC.sz", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_ankleRollInPos_LOC.v", lock = True, keyable = False, channelBox = False)
                cmds.CenterPivot()
                
                self.ankleOutLoc = cmds.spaceLocator(n = "L_ankleRollOutPos_LOC", p = (0,0,0), a = True)
                cmds.move(0.5,0,1)
                cmds.setAttr ("L_ankleRollOutPos_LOC.ty", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_ankleRollOutPos_LOC.rx", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_ankleRollOutPos_LOC.ry", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_ankleRollOutPos_LOC.rz", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_ankleRollOutPos_LOC.sx", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_ankleRollOutPos_LOC.sy", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_ankleRollOutPos_LOC.sz", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_ankleRollOutPos_LOC.v", lock = True, keyable = False, channelBox = False)
                cmds.CenterPivot()
                
                self.toeTipLoc = cmds.spaceLocator(n = "L_toeTipPos_LOC", p = (0,0,0), a = True)
                cmds.move(0,0,2)
                cmds.setAttr ("L_toeTipPos_LOC.ty", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_toeTipPos_LOC.rx", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_toeTipPos_LOC.ry", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_toeTipPos_LOC.rz", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_toeTipPos_LOC.sx", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_toeTipPos_LOC.sy", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_toeTipPos_LOC.sz", lock = True, keyable = False, channelBox = False)
                cmds.setAttr ("L_toeTipPos_LOC.v", lock = True, keyable = False, channelBox = False)
                cmds.CenterPivot()
                
                footRoll_grp = cmds.group(n = "L_footRollInfo_doNotDelete", em = True)
                cmds.parent(self.heelLoc, self.ankleInLoc, self.ankleOutLoc, self.toeTipLoc, footRoll_grp, r = False)
                
                controllerScale = self.controllerSize_controlRig_sb.value()
                cmds.select(footRoll_grp, r = True)
                cmds.scale (controllerScale * 0.5, controllerScale * 0.5, controllerScale * 0.5, r = True)
            
            else:
                if cmds.objExists ('L_footRollInfo_doNotDelete'):
                    cmds.delete('L_footRollInfo_doNotDelete')
                else:
                    return
            
        
'''
####################################################################################################
UI BUILDING PHASE
END
####################################################################################################
''' 

'''
####################################################################################################
SEARCH AND REPLACE NAMES
START
####################################################################################################
'''
def searchReplaceNames (searchName, replaceName, hierarchy, selected, allSelect):
    
    if searchName == "":        
            om.MGlobal.displayError("'SEARCH' FIELD EMPTY")
            return
    
    with UndoContext():        
        if hierarchy:
            pymel.select (hi = True)
            selectedItems = pymel.ls (sl = True, dag = True, transforms = True)
        elif selected:
            selectedItems = pymel.ls (sl = True, transforms = True)
        else:
            selectedItems = pymel.select (r = True, allDagObjects = True, hi = True)
            selectedItems = pymel.ls (sl = True, transforms = True)
            
        for obj in selectedItems:
            oldName = str (obj)
            newName = oldName.replace (searchName, replaceName)
            cmds.rename (oldName, newName)
            cmds.select (d = True)
        print "{0} --> {1}".format(searchName,replaceName)
        
def prefixName (prefixText, hierarchy, selected, allSelect):
    with UndoContext():        
        if hierarchy:
            pymel.select (hi = True)
            selectedItems = pymel.ls (sl = True, dag = True, transforms = True)
        elif selected:
            selectedItems = pymel.ls (sl = True, transforms = True)
        else:
            selectedItems = pymel.select (r = True, allDagObjects = True, hi = True)
            selectedItems = pymel.ls (sl = True, transforms = True)
            
        for obj in selectedItems:
            oldName = str (obj)
            newName = prefixText + oldName
            cmds.rename (oldName, newName)
            cmds.select (d = True)
    
def suffixName (suffixText, hierarchy, selected, allSelect):
    with UndoContext():        
        if hierarchy:
            pymel.select (hi = True)
            selectedItems = pymel.ls (sl = True, dag = True, transforms = True)
        elif selected:
            selectedItems = pymel.ls (sl = True, transforms = True)
        else:
            selectedItems = pymel.select (r = True, allDagObjects = True, hi = True)
            selectedItems = pymel.ls (sl = True, transforms = True)
            
        for obj in selectedItems:
            oldName = str (obj)
            newName = oldName + suffixText
            cmds.rename (oldName, newName)
            cmds.select (d = True)
            
def paddingRename(renameText, startNumber, paddingNumber, steps, hierarchy, selected, allSelect):
    
    if renameText == "":        
            om.MGlobal.displayError("'RENAME' FIELD EMPTY")
            return
    
    with UndoContext():        
        if hierarchy:
            pymel.select (hi = True)
            selectedItems = pymel.ls (sl = True, dag = True, transforms = True)
        elif selected:
            selectedItems = pymel.ls (sl = True, transforms = True)
        else:
            selectedItems = pymel.select (r = True, allDagObjects = True, hi = True)
            selectedItems = pymel.ls (sl = True, transforms = True)
                    
        for obj in selectedItems:                   
            oldName = str (obj)
            newName = renameText + str(startNumber).zfill(paddingNumber) #'zfill' creates a padding for the number, decides how many digits number to add
            cmds.rename (oldName, newName)
            startNumber =  startNumber + steps            
        
        
'''
####################################################################################################
SEARCH AND REPLACE NAMES
END
####################################################################################################
'''

'''
####################################################################################################
CREATE CONTROLLER W GROUP
START
####################################################################################################
'''
def createController(controllerName, controllerSufix, controllerSize, forceLabel, snapSelected, selectedController, groupNumber, group1, group2, group3, group4, controllerColor):
    with UndoContext(): 
        selectedItems = cmds.ls(selection = True)
        newControllerName = controllerName + controllerSufix
        
        print ("Selected Controller Color: {0}, {1}, {2}".format(controllerColor.red(), controllerColor.green(), controllerColor.blue()))
        
        if (len(selectedItems) == 0):
            makeController(newControllerName, controllerSize, selectedController, controllerColor)
            createGroups(newControllerName, groupNumber, group1, group2, group3, group4)
        else:
            for item in selectedItems:
                if forceLabel:
                    name = newControllerName #If 'force label' on then takes the label names as the new controller name
                else:
                    name = item + controllerSufix #If 'force label' off then takes the selected item name as the new controller name
                
                if snapSelected:                    
                    makeController(name, controllerSize, selectedController, controllerColor)
                    groupSelectName = createGroups(name, groupNumber, group1, group2, group3, group4)
                    cmds.select (item, groupSelectName, r = True)
                    cmds.delete (cmds.parentConstraint (weight = 1))
                else:
                    makeController(name, controllerSize, selectedController, controllerColor)
                    createGroups(name, groupNumber, group1, group2, group3, group4)

#To create the controller from the given inputs            
def makeController(newControllerName, controllerSize, selectedController, controllerColor):
    if (selectedController == "Circle"):
        newController = cmds.circle (c = (0,0,0), nr = (0,1,0), sw = 360, r = 1, d = 3, ut = 0, tol = 0.01, s = 8, ch = 1, n = newControllerName)[0]
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "Square"):
        newController = mel.eval ("curve -d 1 -p -1 0 1 -p -1 0 -1 -p 1 0 -1 -p 1 0 1 -p -1 0 1 -k 0 -k 1 -k 2 -k 3 -k 4 ;")
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "Cube"):
        newController = mel.eval ("curve -d 1 -p -0.5 -0.5 -0.5 -p 0.5 -0.5 -0.5 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 -0.5 -0.5 -p -0.5 -0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 -0.5 -0.5 -p 0.5 0.5 -0.5 -p 0.5 0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 0.5 0.5 -p -0.5 0.5 0.5 -p -0.5 -0.5 0.5 -p -0.5 0.5 0.5 -p -0.5 0.5 -0.5 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 ;")
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "Hexagon"):
        newController = mel.eval ("curve -d 1 -p 0.501607 0 -0.868807 -p 1.003213 0 0 -p 0.501607 0 0.868809 -p -0.501607 0 0.868809 -p -1.003213 0 0 -p -0.501607 0 -0.868808 -p 0.501607 0 -0.868807 -p -0.501607 0 0.868809 -p -1.003213 0 0 -p -0.501607 0 -0.868808 -p 0.501607 0 0.868809 -p 1.003213 0 0 -p -1.003213 0 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 ;")
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "Sphere"):
        newController = mel.eval ("curve -d 1 -p 0 1 0 -p -0.258819 0.965926 0 -p -0.5 0.866025 0 -p -0.707107 0.707107 0 -p -0.866025 0.5 0 -p -0.965926 0.258819 0 -p -1 0 0 -p -0.965926 -0.258819 0 -p -0.866025 -0.5 0 -p -0.707107 -0.707107 0 -p -0.5 -0.866025 0 -p -0.258819 -0.965926 0 -p 0 -1 0 -p 0.258819 -0.965926 0 -p 0.5 -0.866025 0 -p 0.707107 -0.707107 0 -p 0.866025 -0.5 0 -p 0.965926 -0.258819 0 -p 1 0 0 -p 0.965926 0.258819 0 -p 0.866025 0.5 0 -p 0.707107 0.707107 0 -p 0.5 0.866025 0 -p 0.258819 0.965926 0 -p 0 1 0 -p 0 0.965926 -0.258819 -p 0 0.866025 -0.5 -p 0 0.707107 -0.707107 -p 0 0.5 -0.866025 -p 0 0.258819 -0.965926 -p 0 0 -1 -p 0 -0.258819 -0.965926 -p 0 -0.5 -0.866025 -p 0 -0.707107 -0.707107 -p 0 -0.866025 -0.5 -p 0 -0.965926 -0.258819 -p 0 -1 0 -p 0 -0.965926 0.258819 -p 0 -0.866025 0.5 -p 0 -0.707107 0.707107 -p 0 -0.5 0.866025 -p 0 -0.258819 0.965926 -p 0 0 1 -p 0 0.258819 0.965926 -p 0 0.5 0.866025 -p 0 0.707107 0.707107 -p 0 0.866025 0.5 -p 0 0.965926 0.258819 -p 0 1 0 -p 0.258819 0.965926 0 -p 0.5 0.866025 0 -p 0.707107 0.707107 0 -p 0.866025 0.5 0 -p 0.965926 0.258819 0 -p 1 0 0 -p 0.866025 0 -0.5 -p 0.5 0 -0.866025 -p 0 0 -1 -p -0.5 0 -0.866025 -p -0.866025 0 -0.5 -p -1 0 0 -p -0.866025 0 0.5 -p -0.5 0 0.866025 -p 0 0 1 -p 0.5 0 0.866025 -p 0.866025 0 0.5 -p 1 0 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 -k 17 -k 18 -k 19 -k 20 -k 21 -k 22 -k 23 -k 24 -k 25 -k 26 -k 27 -k 28 -k 29 -k 30 -k 31 -k 32 -k 33 -k 34 -k 35 -k 36 -k 37 -k 38 -k 39 -k 40 -k 41 -k 42 -k 43 -k 44 -k 45 -k 46 -k 47 -k 48 -k 49 -k 50 -k 51 -k 52 -k 53 -k 54 -k 55 -k 56 -k 57 -k 58 -k 59 -k 60 -k 61 -k 62 -k 63 -k 64 -k 65 -k 66;")
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "Cross"):
        newController = mel.eval ("curve -d 1 -p 0 0 -0.9857426965 -p -0.2950522357 0 -0.543164343 -p -0.1475261178 0 -0.543164343 -p -0.1475261178 0 -0.1475261178 -p -0.543164343 0 -0.1475261178 -p -0.543164343 0 -0.2950522357 -p -0.9857426965 0 0 -p -0.543164343 0 0.2950522357 -p -0.543164343 0 0.1475261178 -p -0.1475261178 0 0.1475261178 -p -0.1475261178 0 0.543164343 -p -0.2950522357 0 0.543164343 -p 0 0 0.9857426965 -p 0.2950522357 0 0.543164343 -p 0.1475261178 0 0.543164343 -p 0.1475261178 0 0.1475261178 -p 0.543164343 0 0.1475261178 -p 0.543164343 0 0.2950522357 -p 0.9857426965 0 0 -p 0.543164343 0 -0.2950522357 -p 0.543164343 0 -0.1475261178 -p 0.1475261178 0 -0.1475261178 -p 0.1475261178 0 -0.543164343 -p 0.2950522357 0 -0.543164343 -p 0 0 -0.98574269651;")
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "Arrow"):
        newController = mel.eval ("curve -d 1 -p 0 0 0 -p 0.4 0 -0.4 -p 0.2 0 -0.4 -p 0.2 0 -1 -p -0.2 0 -1 -p -0.2 0 -0.4 -p -0.4 0 -0.4 -p 0 0 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 ;")
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "Arc Arrow"):
        newController = mel.eval ("curve -d 3 -p -0.35703261 0 0.63881379 -p -0.35703261 0 0.63881379 -p -0.35703261 0 0.63881379 -p -0.43555158 0 0.28326996 -p -0.43555158 0 0.28326996 -p -0.43555158 0 0.28326996 -p -0.43555158 0 0.28326996 -p -0.10092762 0 0.88816986 -p -0.10092762 0 0.88816986 -p -0.10092762 0 0.88816986 -p -0.10092762 0 0.88816986 -p -0.79049277 0 0.83941839 -p -0.79049277 0 0.83941839 -p -0.79049277 0 0.83941839 -p -0.79049277 0 0.83941839 -p -0.45433386 0 0.76645116 -p -0.45433386 0 0.76645116 -p -0.45433386 0 0.76645116 -p -0.45433386 0 0.76645116 -p -0.64641969 0 0.64640673 -p -0.84458862 0 0.34986654 -p -0.91422432 0 0 -p -0.84458862 0 -0.34986654 -p -0.64641969 0 -0.64640673 -p -0.45283779 0 -0.76484979 -p -0.45283779 0 -0.76484979 -p -0.45283779 0 -0.76484979 -p -0.45283779 0 -0.76484979 -p -0.79049277 0 -0.83941839 -p -0.79049277 0 -0.83941839 -p -0.79049277 0 -0.83941839 -p -0.79049277 0 -0.83941839 -p -0.10092762 0 -0.88816986 -p -0.10092762 0 -0.88816986 -p -0.10092762 0 -0.88816986 -p -0.10092762 0 -0.88816986 -p -0.43555158 0 -0.28326996 -p -0.43555158 0 -0.28326996 -p -0.43555158 0 -0.28326996 -p -0.43555158 0 -0.28326996 -p -0.35575119 0 -0.63632061 -p -0.35575119 0 -0.63632061 -p -0.35575119 0 -0.63632061 -p -0.35575119 0 -0.63632061 -p -0.52874856 0 -0.52892838 -p -0.69110901 0 -0.28621998 -p -0.74792646 0 0 -p -0.69110901 0 0.28621998 -p -0.52874856 0 0.52892838 -p -0.35703261 0 0.63881379;")
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "Double Arrow"):
        newController = mel.eval ("curve -d 1 -p 0 0 0 -p 0 0.4 -0.4 -p 0 0.2 -0.4 -p 0 0.2 -1 -p 0 -0.2 -1 -p 0 -0.2 -0.4 -p 0 -0.4 -0.4 -p 0 0 0 -p -0.4 0 -0.4 -p -0.2 0 -0.4 -p -0.2 0 -1 -p 0.2 0 -1 -p 0.2 0 -0.4 -p 0.4 0 -0.4 -p 0 0 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 ;")
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "Curved Arrow"):
        newController = mel.eval ("curve -d 3 -p 0.0959835 0.604001 -0.0987656 -p 0.500783 0.500458 -0.0987656 -p 0.751175 0.327886 -0.0987656 -p 0.751175 0.327886 -0.0987656 -p 0.751175 0.327886 -0.336638 -p 0.751175 0.327886 -0.336638 -p 1.001567 0 0 -p 1.001567 0 0 -p 0.751175 0.327886 0.336638 -p 0.751175 0.327886 0.336638 -p 0.751175 0.327886 0.0987656 -p 0.751175 0.327886 0.0987656 -p 0.500783 0.500458 0.0987656 -p 0.0959835 0.604001 0.0987656 -p 0.0959835 0.604001 0.0987656 -p 0.0959835 0.500458 0.500783 -p 0.0959835 0.327886 0.751175 -p 0.0959835 0.327886 0.751175 -p 0.336638 0.327886 0.751175 -p 0.336638 0.327886 0.751175 -p 0 0 1.001567 -p 0 0 1.001567 -p -0.336638 0.327886 0.751175 -p -0.336638 0.327886 0.751175 -p -0.0959835 0.327886 0.751175 -p -0.0959835 0.327886 0.751175 -p -0.0959835 0.500458 0.500783 -p -0.0959835 0.604001 0.0987656 -p -0.0959835 0.604001 0.0987656 -p -0.500783 0.500458 0.0987656 -p -0.751175 0.327886 0.0987656 -p -0.751175 0.327886 0.0987656 -p -0.751175 0.327886 0.336638 -p -0.751175 0.327886 0.336638 -p -1.001567 0 0 -p -1.001567 0 0 -p -0.751175 0.327886 -0.336638 -p -0.751175 0.327886 -0.336638 -p -0.751175 0.327886 -0.0987656 -p -0.751175 0.327886 -0.0987656 -p -0.500783 0.500458 -0.0987656 -p -0.0959835 0.604001 -0.0987656 -p -0.0959835 0.604001 -0.0987656 -p -0.0959835 0.500458 -0.500783 -p -0.0959835 0.327886 -0.751175 -p -0.0959835 0.327886 -0.751175 -p -0.336638 0.327886 -0.751175 -p -0.336638 0.327886 -0.751175 -p 0 0 -1.001567 -p 0 0 -1.001567 -p 0.336638 0.327886 -0.751175 -p 0.336638 0.327886 -0.751175 -p 0.0959835 0.327886 -0.751175 -p 0.0959835 0.327886 -0.751175 -p 0.0959835 0.500458 -0.500783 -p 0.0959835 0.604001 -0.0987656 -k 0 -k 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 -k 17 -k 18 -k 19 -k 20 -k 21 -k 22 -k 23 -k 24 -k 25 -k 26 -k 27 -k 28 -k 29 -k 30 -k 31 -k 32 -k 33 -k 34 -k 35 -k 36 -k 37 -k 38 -k 39 -k 40 -k 41 -k 42 -k 43 -k 44 -k 45 -k 46 -k 47 -k 48 -k 49 -k 50 -k 51 -k 52 -k 53 -k 53 -k 53;")
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "Tube"):
        newController = mel.eval ("curve -d 1 -p -1.5 0.366667 0.366667 -p -1.5 0.366667 -0.366667 -p -1.5 -0.366667 -0.366667 -p -1.5 -0.366667 0.366667 -p -1.5 0.366667 0.366667 -p -2 0.366667 0.366667 -p -2 0.366667 -0.366667 -p -1.5 0.366667 -0.366667 -p -2 0.366667 -0.366667 -p -2 -0.366667 -0.366667 -p -1.5 -0.366667 -0.366667 -p -2 -0.366667 -0.366667 -p -2 -0.366667 0.366667 -p -1.5 -0.366667 0.366667 -p -2 -0.366667 0.366667 -p -2 0.366667 0.366667 -p -1.5 0.366667 0.366667 -p -1.5 0.366667 0.366667 -p -1.5 0.366667 0.366667 -p -1.5 0.25 0.25 -p -1.5 0.25 -0.25 -p -1.5 0.366667 -0.366667 -p -1.5 -0.366667 -0.366667 -p -1.5 -0.25 -0.25 -p -1.5 -0.366667 -0.366667 -p -1.5 -0.366667 0.366667 -p -1.5 -0.25 0.25 -p -1.5 0.25 0.25 -p -1.5 0.25 -0.25 -p -1.5 -0.25 -0.25 -p -1.5 -0.25 0.25 -p 1.5 -0.25 0.25 -p 1.5 0.25 0.25 -p -1.5 0.25 0.25 -p -1.5 0.25 -0.25 -p 1.5 0.25 -0.25 -p 1.5 0.25 0.25 -p 1.5 -0.25 0.25 -p 1.5 -0.25 -0.25 -p -1.5 -0.25 -0.25 -p 1.5 -0.25 -0.25 -p 1.5 -0.25 0.25 -p 1.5 0.25 0.25 -p 1.5 0.25 -0.25 -p 1.5 -0.25 -0.25 -p 1.5 0.25 -0.25 -p 1.5 0.366667 -0.366667 -p 1.5 -0.366667 -0.366667 -p 1.5 -0.25 -0.25 -p 1.5 -0.366667 -0.366667 -p 1.5 -0.366667 0.366667 -p 1.5 -0.25 0.25 -p 1.5 -0.366667 0.366667 -p 1.5 0.366667 0.366667 -p 1.5 0.25 0.25 -p 1.5 0.366667 0.366667 -p 1.5 0.366667 -0.366667 -p 2 0.366667 -0.366667 -p 2 -0.366667 -0.366667 -p 1.5 -0.366667 -0.366667 -p 2 -0.366667 -0.366667 -p 2 -0.366667 0.366667 -p 1.5 -0.366667 0.366667 -p 2 -0.366667 0.366667 -p 2 0.366667 0.366667 -p 2 0.366667 -0.366667 -p 2 0.366667 0.366667 -p 1.5 0.366667 0.366667 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 -k 17 -k 18 -k 19 -k 20 -k 21 -k 22 -k 23 -k 24 -k 25 -k 26 -k 27 -k 28 -k 29 -k 30 -k 31 -k 32 -k 33 -k 34 -k 35 -k 36 -k 37 -k 38 -k 39 -k 40 -k 41 -k 42 -k 43 -k 44 -k 45 -k 46 -k 47 -k 48 -k 49 -k 50 -k 51 -k 52 -k 53 -k 54 -k 55 -k 56 -k 57 -k 58 -k 59 -k 60 -k 61 -k 62 -k 63 -k 64 -k 65 -k 66 -k 67;")
        cmds.scale( 0.5, 1, 1, newController, r = True)
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "Gear"):
        newController = mel.eval ("curve -d 1 -p -1.541097 0 -0.407608 -p -1.997943 0 -0.287409 -p -1.996633 0 0.292773 -p -1.540642 0 0.404437 -p -1.376247 0 0.800967 -p -1.614601 0 1.209387 -p -1.206218 0 1.618289 -p -0.802518 0 1.37467 -p -0.406558 0 1.538403 -p -0.285068 0 1.998563 -p 0.293543 0 1.996772 -p 0.405503 0 1.538183 -p 0.800499 0 1.376064 -p 1.209852 0 1.613362 -p 1.618868 0 1.206081 -p 1.37717 0 0.803675 -p 1.540102 0 0.406725 -p 1.997785 0 0.285372 -p 1.997147 0 -0.294228 -p 1.540467 0 -0.405926 -p 1.377365 0 -0.800905 -p 1.615038 0 -1.210376 -p 1.206209 0 -1.619887 -p 0.802833 0 -1.375844 -p 0.40785 0 -1.540751 -p 0.28608 0 -1.998594 -p -0.29285 0 -1.997769 -p -0.405278 0 -1.539256 -p -0.801016 0 -1.37748 -p -1.208227 0 -1.614979 -p -1.619464 0 -1.206488 -p -1.37182 0 -0.798064 -p -1.541097 0 -0.407608 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 -k 17 -k 18 -k 19 -k 20 -k 21 -k 22 -k 23 -k 24 -k 25 -k 26 -k 27 -k 28 -k 29 -k 30 -k 31 -k 32;")
        delController = mel.eval ("circle -c 0 0 0 -r 0.8 -nr 0 1 0")
        delControllerShapes = cmds.listRelatives(delController, shapes = True)
        cmds.select (delControllerShapes, r = True)
        cmds.select (newController, add = True)
        cmds.parent (r = True, s = True)
        cmds.delete (delController)
        cmds.scale( 0.5, 0.5, 0.5, newController, r = True)
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "Plus"):
        newController = mel.eval ("curve -d 1 -p -0.574074 0 -0.522716 -p -2 0 -0.522716 -p -2 0 0.522716 -p -0.574074 0 0.522716 -p -0.574074 0 2 -p 0.574074 0 2 -p 0.574074 0 0.522716 -p 2 0 0.522716 -p 2 0 -0.522716 -p 0.574074 0 -0.522716 -p 0.574074 0 -2 -p -0.574074 0 -2 -p -0.574074 0 -0.522716 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 ;")
        cmds.scale( 0.5, 0.5, 0.5, newController, r = True)
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "Triangle"):
        newController = mel.eval ("curve -d 1 -p -1 0 -1 -p 1 0 -1 -p 0 0 1 -p -1 0 -1 -k 0 -k 1 -k 2 -k 3 ;")
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "Pyramid"):
        newController = mel.eval ("curve -d 1 -p 0 0 1 -p 1 0 0 -p 0 1 0 -p 0 0 1 -p -1 0 0 -p 0 1 0 -p 0 0 -1 -p -1 0 0 -p 0 0 -1 -p 1 0 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 ;")
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "3D Diamond"):
        newController = mel.eval ("curve -d 1 -p 0 1 0 -p 0 0 1 -p 1 0 0 -p 0 0 -1 -p -1 0 0 -p 0 0 1 -p -1 0 0 -p 0 1 0 -p 0 0 -1 -p 1 0 0 -p 0 1 0 -p 1 0 0 -p 0 -1 0 -p 0 0 -1 -p -1 0 0 -p 0 -1 0 -p 0 0 1 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 ;")
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "2D Diamond"):
        newController = mel.eval ("$diamondCurve = `circle -c 0 0 0 -nr 0 1 0 -sw 360 -r 1 -d 3 -ut 0 -tol 0.01 -s 8 -ch 1`; \nselect -r $diamondCurve.cv[0] $diamondCurve.cv[2] $diamondCurve.cv[4] $diamondCurve.cv[6] ; \nhilite $diamondCurve.cv[0] $diamondCurve.cv[2] $diamondCurve.cv[4] $diamondCurve $diamondCurve.cv[6] ;\nscale -r -p 0cm 0cm 0cm 0.26 0.26 0.26 ;\nhilite -u $diamondCurve ;\nselect -r $diamondCurve;\nscale -ws -r 1.2 1.2 1.2;\nmakeIdentity -a true -r 1 -t 1 -s 1 -n 0;")
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    elif (selectedController == "Diamond Sphere"):
        newController = mel.eval ("curve -d 1 -p -0.723607 0.525731 0.447214 -p 0 0 1 -p 0.276393 0.850651 0.447214 -p -0.723607 0.525731 0.447214 -p -0.276393 0.850651 -0.447214 -p 0.276393 0.850651 0.447214 -p 0.723607 0.525731 -0.447214 -p -0.276393 0.850651 -0.447214 -p 0 0 -1 -p 0.723607 0.525731 -0.447214 -p 0.723607 -0.525731 -0.447214 -p 0 0 -1 -p -0.276393 -0.850651 -0.447214 -p 0.723607 -0.525731 -0.447214 -p 0.276393 -0.850651 0.447214 -p -0.276393 -0.850651 -0.447214 -p -0.894427 -7.81933e-08 -0.447214 -p 0 0 -1 -p -0.276393 0.850651 -0.447214 -p -0.894427 -7.81933e-08 -0.447214 -p -0.723607 0.525731 0.447214 -p -0.723607 -0.525731 0.447214 -p -0.894427 -7.81933e-08 -0.447214 -p -0.276393 -0.850651 -0.447214 -p -0.723607 -0.525731 0.447214 -p 0.276393 -0.850651 0.447214 -p 0 0 1 -p -0.723607 -0.525731 0.447214 -p 0 0 1 -p 0.894427 0 0.447214 -p 0.276393 0.850651 0.447214 -p 0.723607 0.525731 -0.447214 -p 0.894427 0 0.447214 -p 0.276393 -0.850651 0.447214 -p 0.723607 -0.525731 -0.447214 -p 0.894427 0 0.447214 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 -k 17 -k 18 -k 19 -k 20 -k 21 -k 22 -k 23 -k 24 -k 25 -k 26 -k 27 -k 28 -k 29 -k 30 -k 31 -k 32 -k 33 -k 34 -k 35 ;")
        newController = cmds.rename (newController, newControllerName)
        cmds.scale(controllerSize, controllerSize, controllerSize, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
    
    #Adding in Color to the New Controllers
    cmds.select (newController, r = True)
    shapesSelect = cmds.ls (selection = 1, shapes = True, dag = True) #Selecting all the shapes from the newly created controller
    
    #Going through all the shapes and changing the RGB color through the 'Drawing Overrides'
    for shape in shapesSelect:
        cmds.setAttr(shape + ".overrideEnabled", 1)
        cmds.setAttr(shape + ".overrideRGBColors", 1)
        cmds.setAttr(shape + ".overrideColorRGB", controllerColor.red(), controllerColor.green(), controllerColor.blue())
    
        
def createGroups(controllerName, groupNumber, group1, group2, group3, group4):
    if (groupNumber == 0):
        return controllerName
    elif (groupNumber == 1):
        group1Created = cmds.group(n = controllerName + group1)
        return group1Created
    elif (groupNumber == 2):
        group1Created = cmds.group(n = controllerName + group2)
        group2Created = cmds.group(n = controllerName + group1)
        return group2Created
    elif (groupNumber == 3):
        group1Created = cmds.group(n = controllerName + group3)
        group2Created = cmds.group(n = controllerName + group2)
        group3Created = cmds.group(n = controllerName + group1)
        return group3Created
    elif (groupNumber == 4):
        group1Created = cmds.group(n = controllerName + group4)
        group2Created = cmds.group(n = controllerName + group3)
        group3Created = cmds.group(n = controllerName + group2)
        group4Created = cmds.group(n = controllerName + group1)
        return group4Created
        
'''
####################################################################################################
CREATE CONTROLLER W GROUP
END
####################################################################################################
'''
    
'''
####################################################################################################
CREATE CONTROLLER FROM TEXT
START
####################################################################################################
'''
def createControllerText (controlText, font):
    with UndoContext():
        if (controlText != ""):
            #Creating the curves from the given text and font
            cmds.textCurves (f = font, t = controlText)
            
            transformNode = cmds.ls (selection = True)
            #Selecting the shape nodes for all the transforms created
            selected = cmds.ls(selection = True, dag = True, s = True)
            
            #Selecting the immediate childer of the main transform node
            immediateChildren = cmds.listRelatives(transformNode, children = True)
            cmds.select(immediateChildren, r = True)
            
            #Breaking the connection in the translate of the transform nodes
            for child in immediateChildren:
                mel.eval("source channelBoxCommand; CBdeleteConnection {0}.translate;". format (child))
            
            #Freezing Transformations and Deleting History
            cmds.select (transformNode, r = True)
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            
            #Combining the shape nodes to the main transform node
            cmds.select(selected, transformNode, r = True)
            cmds.parent (r = True, s= True)
            
            #Deleting the empty groups in the hierachy
            cmds.delete(immediateChildren)          
            
        else:
            #Give out an error message
            om.MGlobal.displayError("TEXT FIELD IS EMPTY")
            return
'''
####################################################################################################
CREATE CONTROLLER FROM TEXT
END
####################################################################################################
'''

'''
####################################################################################################
EXPORT TO FBX
START
####################################################################################################
'''
def exportSaveButtonPush (exportOption, exportLocation, exportValues, bakeSimulationBool, autoManualOption):
        # SETTING THE VALUES FOR EXPORT OPTIONS
    cmds.FBXExportSmoothingGroups ('-v', exportValues [0])
    cmds.FBXExportSmoothMesh ('-v', exportValues [1])
    cmds.FBXExportReferencedAssetsContent ('-v', exportValues [2])
    cmds.FBXExportTriangulate ('-v', exportValues [3])

    if (exportValues[4] == True):
        cmds.FBXProperty ('Export|IncludeGrp|Animation', '-v', 1)
    else:
        cmds.FBXProperty ('Export|IncludeGrp|Animation', '-v', 0)

    if (exportValues[10] == True):
        cmds.FBXProperty ('Export|AdvOptGrp|UnitsGrp|DynamicScaleConversion', '-v', 1)
    else:
        cmds.FBXProperty ('Export|AdvOptGrp|UnitsGrp|DynamicScaleConversion', '-v', 0)

    cmds.FBXExportConvertUnitString (exportValues[11])
    cmds.FBXExportUpAxis (exportValues [12])

    # Turning off the constraint and skeleton definations options for Exporting
    cmds.FBXProperty ('Export|IncludeGrp|Animation|ConstraintsGrp|Constraint', '-v', 0)
    cmds.FBXProperty ('Export|IncludeGrp|Animation|ConstraintsGrp|Character', '-v', 0)

    # Export in FBX format to the file directory below with the given options
    if (exportOption == 'Selected'):
        print ("You choose the Export Selected Option")

        cmds.file (exportLocation, force = True, type = 'FBX export', exportSelected = True) 

    elif (exportOption == 'Models'):
        print ("You choose the Export Models Option")

        cmds.SelectAllPolygonGeometry()

        cmds.file (exportLocation, force = True, type = 'FBX export', exportSelected = True) 

    elif (exportOption == 'Models_and_Rig'):
        print ("You choose the Export Models and Rig Option")

        cmds.select (clear = True)
        cmds.SelectAllPolygonGeometry()
        jointSelect = cmds.ls (type = 'joint')
        cmds.select (jointSelect, add = True)

        cmds.file (exportLocation, force = True, type = 'FBX export', exportSelected = True) 

    elif (exportOption == 'Animations_with_Model'):
        print ("You choose the Export Animations with Model Option")

        # Baking the animations to the joints when the Export is set to AUTOMATIC
        if (bakeSimulationBool):
            allSkinnedJoints = []

            cmds.select (clear = 1)
            cmds.SelectAllPolygonGeometry()
            transforms = cmds.ls (sl = 1)

            for geo in transforms:
                indSkinCluster = mel.eval ("findRelatedSkinCluster " + geo) #Finds the skinCluster attached to the GEO
                attachedJoints = cmds.skinCluster (indSkinCluster, q = 1, inf = 1) #Finds the joints attached to the skinCluster
                allSkinnedJoints = allSkinnedJoints + attachedJoints
                
            allSkinnedJoints = list(dict.fromkeys(allSkinnedJoints)) #Removes the duplicates from the list

            cmds.select (allSkinnedJoints, r = 1) #Select all the skinned joints
            
            if (autoManualOption == "Automatic"):
                startTime = cmds.playbackOptions (query = True, minTime = True)
                endTime = cmds.playbackOptions (query = True, maxTime = True)
                steps = 1
            elif (autoManualOption == "Manual"):
                startTime = exportValues[6]
                endTime = exportValues[7]
                steps = exportValues[8]
                
            cmds.bakeResults (allSkinnedJoints, simulation = True, time = (startTime,endTime), sampleBy = steps, sparseAnimCurveBake = False, removeBakedAttributeFromLayer = False, removeBakedAnimFromLayer = False, bakeOnOverrideLayer = False, minimizeRotation = True, controlPoints = False, shape = True)
        
        cmds.select (clear = True)
        cmds.SelectAllPolygonGeometry()
        cmds.select (allSkinnedJoints, add = True)

        cmds.file (exportLocation, force = True, type = 'FBX export', exportSelected = True) 

    elif (exportOption == 'Animations_without_Model'):
        print ("You choose the Export Animations w/o Model Option")

        # Baking the animations to the joints when the Export is set to AUTOMATIC
        if (bakeSimulationBool):
            allSkinnedJoints = []

            cmds.select (clear = 1)
            cmds.SelectAllPolygonGeometry()
            transforms = cmds.ls (sl = 1)

            for geo in transforms:
                indSkinCluster = mel.eval ("findRelatedSkinCluster " + geo) #Finds the skinCluster attached to the GEO
                attachedJoints = cmds.skinCluster (indSkinCluster, q = 1, inf = 1) #Finds the joints attached to the skinCluster
                allSkinnedJoints = allSkinnedJoints + attachedJoints
                
            allSkinnedJoints = list(dict.fromkeys(allSkinnedJoints)) #Removes the duplicates from the list

            cmds.select (allSkinnedJoints, r = 1) #Select all the skinned joints
            
            if (autoManualOption == "Automatic"):
                startTime = cmds.playbackOptions (query = True, minTime = True)
                endTime = cmds.playbackOptions (query = True, maxTime = True)
                steps = 1
            elif (autoManualOption == "Manual"):
                startTime = exportValues[6]
                endTime = exportValues[7]
                steps = exportValues[8]
                
            cmds.bakeResults (allSkinnedJoints, simulation = True, time = (startTime,endTime), sampleBy = steps, sparseAnimCurveBake = False, removeBakedAttributeFromLayer = False, removeBakedAnimFromLayer = False, bakeOnOverrideLayer = False, minimizeRotation = True, controlPoints = False, shape = True)

        cmds.select (allSkinnedJoints, replace = True)

        cmds.file (exportLocation, force = True, type = 'FBX export', exportSelected = True) 

    else:
        print ("You choose the Export All Option")
        cmds.file (exportLocation, force = True, type = 'FBX export', exportAll = True) 

    print exportLocation
'''
####################################################################################################
EXPORT TO FBX
END
####################################################################################################
'''

'''
####################################################################################################
CREATE IK CHAIN METHOD
START
####################################################################################################
'''    
def createIKChain(controllerScale):
    with UndoContext(): #Using the 'UndoContext' class to create a block, that Undos at the same time, instead of undoing every line individually (which PySide tend to do)
        selectedJoints = cmds.ls(selection = True)
        
        if (len(selectedJoints) == 3):
            
            for items in selectedJoints:
                if not (cmds.objectType (items, isType = 'joint')):                    
                    #Give out an error message
                    om.MGlobal.displayError("ONE OR MORE OF THE SELECTED ITEM/S IS NOT A JOINT")
                    return
                
            #Joints Input from Window
            firstJNT = selectedJoints[0]
            secondJNT = selectedJoints[1]
            thirdJNT = selectedJoints[2]
            
            #Creating IK Controllers for the Setup
            #Pole Vector Controller
            secondCTRL = mel.eval ("curve -d 1 -p 0 1 0 -p -0.258819 0.965926 0 -p -0.5 0.866025 0 -p -0.707107 0.707107 0 -p -0.866025 0.5 0 -p -0.965926 0.258819 0 -p -1 0 0 -p -0.965926 -0.258819 0 -p -0.866025 -0.5 0 -p -0.707107 -0.707107 0 -p -0.5 -0.866025 0 -p -0.258819 -0.965926 0 -p 0 -1 0 -p 0.258819 -0.965926 0 -p 0.5 -0.866025 0 -p 0.707107 -0.707107 0 -p 0.866025 -0.5 0 -p 0.965926 -0.258819 0 -p 1 0 0 -p 0.965926 0.258819 0 -p 0.866025 0.5 0 -p 0.707107 0.707107 0 -p 0.5 0.866025 0 -p 0.258819 0.965926 0 -p 0 1 0 -p 0 0.965926 -0.258819 -p 0 0.866025 -0.5 -p 0 0.707107 -0.707107 -p 0 0.5 -0.866025 -p 0 0.258819 -0.965926 -p 0 0 -1 -p 0 -0.258819 -0.965926 -p 0 -0.5 -0.866025 -p 0 -0.707107 -0.707107 -p 0 -0.866025 -0.5 -p 0 -0.965926 -0.258819 -p 0 -1 0 -p 0 -0.965926 0.258819 -p 0 -0.866025 0.5 -p 0 -0.707107 0.707107 -p 0 -0.5 0.866025 -p 0 -0.258819 0.965926 -p 0 0 1 -p 0 0.258819 0.965926 -p 0 0.5 0.866025 -p 0 0.707107 0.707107 -p 0 0.866025 0.5 -p 0 0.965926 0.258819 -p 0 1 0 -p 0.258819 0.965926 0 -p 0.5 0.866025 0 -p 0.707107 0.707107 0 -p 0.866025 0.5 0 -p 0.965926 0.258819 0 -p 1 0 0 -p 0.866025 0 -0.5 -p 0.5 0 -0.866025 -p 0 0 -1 -p -0.5 0 -0.866025 -p -0.866025 0 -0.5 -p -1 0 0 -p -0.866025 0 0.5 -p -0.5 0 0.866025 -p 0 0 1 -p 0.5 0 0.866025 -p 0.866025 0 0.5 -p 1 0 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 -k 17 -k 18 -k 19 -k 20 -k 21 -k 22 -k 23 -k 24 -k 25 -k 26 -k 27 -k 28 -k 29 -k 30 -k 31 -k 32 -k 33 -k 34 -k 35 -k 36 -k 37 -k 38 -k 39 -k 40 -k 41 -k 42 -k 43 -k 44 -k 45 -k 46 -k 47 -k 48 -k 49 -k 50 -k 51 -k 52 -k 53 -k 54 -k 55 -k 56 -k 57 -k 58 -k 59 -k 60 -k 61 -k 62 -k 63 -k 64 -k 65 -k 66;")
            secondCTRL = cmds.rename (secondCTRL, secondJNT + "_IK_CTRL")
            cmds.select(secondCTRL, r = True)
            cmds.scale(controllerScale, controllerScale, controllerScale, r = True)
            cmds.rotate (0, -90, 0)
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            
            secondGRP_con = cmds.group (n = secondCTRL + "_CON")
            secondGRP_off = cmds.group (n = secondCTRL + "_0")
            
            #Main Controller
            mainCTRL = cmds.curve (d = 1, n = thirdJNT + "_IK_CTRL", p = [(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1), (-1, 0, -1)], k = [0, 1, 2, 3, 4])
            cmds.select(mainCTRL, r = True)
            cmds.scale(controllerScale, controllerScale, controllerScale, r = True)   
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory() 
            
            mainGRP_con = cmds.group (n = mainCTRL + "_CON")
            mainGRP_off = cmds.group (n = mainCTRL + "_0")
            
            #Creating locators to calculate the position for the elbow controller
            cmds.spaceLocator (p = (0,0,0), name = "locatorA")
            cmds.group(name = "groupA")
            cmds.spaceLocator (p = (0,0,0), name = "locatorB")
            cmds.group(name = "groupB")
            
            cmds.select (firstJNT, thirdJNT, "groupA", r = True)
            cmds.pointConstraint (offset = (0,0,0), weight = 1)
            
            cmds.select (secondJNT, "groupA", r = True)
            cmds.aimConstraint(offset = (0,0,0), weight = 1, aimVector = (1,0,0), upVector = (0,1,0), worldUpType = "scene")
            
            cmds.select(secondJNT, "locatorA", r = True)
            cmds.pointConstraint(offset = (0,0,0), skip = ("y","z"), weight = 1)
            
            cmds.select(secondJNT, "groupB", r = True)
            cmds.pointConstraint(offset = (0,0,0), weight = 1)
            
            cmds.select("locatorA", "groupB", r = True)
            cmds.aimConstraint(offset = (0,0,0), weight = 1, aimVector = (0,0,1), upVector = (0,1,0), worldUpType = "scene")
            
            cmds.select("locatorB")
            cmds.move (0, 0, 0, r = True, os = True, wd = True)
            
            #Grabing the postition of the locator to position the pole vector controller
            locatorPos = cmds.xform ("locatorB", q = True, worldSpace = True, translation = True)
            cmds.select(secondGRP_off, r = True)
            cmds.move (locatorPos[0], locatorPos[1], locatorPos[2], a = True)
            
            cmds.delete("groupA", "groupB")
            
            #Position the Main Controller
            cmds.select (thirdJNT, mainGRP_off, r = True)
            mainCONST = cmds.parentConstraint (weight = 1, maintainOffset = False)
            cmds.delete (mainCONST)
            
            #Creating the IK Handles
            IKHandle = cmds.ikHandle (n = thirdJNT + "_IKH", shf = False, s = "sticky", fs = True, sj = firstJNT, ee = thirdJNT)
            cmds.rename(IKHandle[1], thirdJNT + "_EFF")
            
            #Parenting the IKH to the main controller and creating a pole vector constraint
            cmds.select(IKHandle[0], mainCTRL, r = True)
            cmds.parent()
            cmds.select(secondCTRL, IKHandle[0], r = True)
            poleVector = cmds.poleVectorConstraint (weight = 1)
            
            #Hide the IK Handle
            cmds.setAttr(IKHandle[0] + ".v", 0)
            
            cmds.select(mainCTRL, thirdJNT, r = True)
            cmds.orientConstraint (offset = (0,0,0), weight = 1)
            
            #Adding a follow attribute to the pole vector controller
            cmds.select(secondCTRL, r = True)
            cmds.addAttr (ln = "follow", at = "enum", en = "<none>:{0}:".format(mainCTRL), k = True)
            
            cmds.select(mainCTRL, secondGRP_con, r = True)
            secondGrpCONST = cmds.parentConstraint (maintainOffset = True, weight = 1)
            
            #Creating connection for the above created attributes using SDK
            cmds.setDrivenKeyframe (secondGrpCONST[0] + "." + mainCTRL + "W0", dv = 0, v = 0, cd = secondCTRL + '.follow')
            cmds.setDrivenKeyframe (secondGrpCONST[0] + "." + mainCTRL + "W0", dv = 1, v = 1, cd = secondCTRL + '.follow')
        
        else:
            #Give out an error message
            om.MGlobal.displayError("SELECT 3 JOINTS THAT ARE IN A CHAIN TO SETUP IK")
            return
'''
####################################################################################################
CREATE IK CHAIN METHOD
END
####################################################################################################
'''    

'''
####################################################################################################
REMOVE UNKOWN NODES
START
####################################################################################################
'''
def deleteUnknownNodes():
    with UndoContext(): #Using the 'UndoContext' class to create a block, that Undos at the same time, instead of undoing every line individually (which PySide tend to do)
        unknownNodes = cmds.ls (type = "unknown")
        unknownNodes += cmds.ls(type = "unknownDag")
        
        if (len(unknownNodes) == 0):
            print ("No Unknown Objects in the Scene")
            return
        
        for item in unknownNodes:
            if cmds.objExists(item):
                print ("Removed Unknown Node : {0}".format(item))
                cmds.lockNode(item, lock=False)
                cmds.delete(item)
'''
####################################################################################################
REMOVE UNKOWN NODES
END
####################################################################################################
'''   

'''
####################################################################################################
SELECT SKINNED JOINTS IN A MESH
START
####################################################################################################
'''
def selectSkinnedJoints():
    with UndoContext(): #Using the 'UndoContext' class to create a block, that Undos at the same time, instead of undoing every line individually (which PySide tend to do)
        allSkinnedJoints = []

        transforms = cmds.ls (selection = 1)

        transforms = list(dict.fromkeys(transforms)) #Removes the duplicates from the list

        for geo in transforms:
            indSkinCluster = mel.eval ("findRelatedSkinCluster " + geo) #Finds the skinCluster attached to the GEO
            attachedJoints = cmds.skinCluster (indSkinCluster, q = 1, inf = 1) #Finds the joints attached to the skinCluster
            allSkinnedJoints = allSkinnedJoints + attachedJoints
            
        allSkinnedJoints = list(dict.fromkeys(allSkinnedJoints)) #Removes the duplicates from the list

        cmds.select (allSkinnedJoints, r = 1)
'''
####################################################################################################
SELECT SKINNED JOINTS IN A MESH
END
####################################################################################################
'''

'''
####################################################################################################
COMBINE SHAPE FOR SELECTED TRANSFORM NODES
START
####################################################################################################
'''
def combineShape ():
    with UndoContext(): #Using the 'UndoContext' class to create a block, that Undos at the same time, instead of undoing every line individually (which PySide tend to do)   
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        selected = cmds.ls(selection = True)
        allSelectedShapes = []

        if (len(selected) == 0 or len(selected) == 1):
            om.MGlobal.displayError("SELECT 2 OR MORE TRANSFORM NODES")
            return

        for item in selected:
            if (item != selected[0]):
                shapes = cmds.listRelatives(item, shapes = True)
                if (shapes != []):
                    allSelectedShapes.extend(shapes)

        cmds.select(allSelectedShapes, selected[0], r = True)
        cmds.parent (r = True, s= True)
'''
####################################################################################################
COMBINE SHAPE FOR SELECTED TRANSFORM NODES
END
####################################################################################################
'''

'''
####################################################################################################
BIPED CONTROL RIG SETUP
START
####################################################################################################
'''
def createBipedControlRig (leftIndicator, rightIndicator, pelvis, spine1, chest, neck, head, l_clavicle, l_shoulder, l_elbow, l_wrist, l_thigh, l_knee, l_ankle, l_ball, armFK, armIK, legFK, legIK, controllerSize, footRollControl):   
    
    #Chekcing if there are any empty arguments and displaying an error if there is   
    argumentsDict = locals() #Storing the values of the arguments in a dict()
    argumentKeys = argumentsDict.keys()
    
    #Checking if any of the argument is empty and displaying error if it is
    for args in argumentKeys:
        if argumentsDict[args] is None or argumentsDict[args] == "":
            om.MGlobal.displayError("EMPTY FIELDS DETECTED. FILL OUT ALL THE FILEDS")
            return
    
    #Checking if the foot roll control is enabled
    if not footRollControl:        
        om.MGlobal.displayError("FOOT ROLL CONTROL IS DISABLED. ENABLE THE FOOT ROLL CONTROL TO PROCEED")
        return
        
    if (not armFK and not armIK) or (not legFK and not legIK):
        om.MGlobal.displayError("SELECT EITHER FK,IK OR BOTH FOR THE ARM AND THE LEG SETUP")
        return
    
    #Getting the joint names from the right side from the left side inputs
    r_clavicle = l_clavicle.replace(leftIndicator, rightIndicator)
    r_shoulder = l_shoulder.replace(leftIndicator, rightIndicator)
    r_elbow = l_elbow.replace(leftIndicator, rightIndicator)
    r_wrist = l_wrist.replace(leftIndicator, rightIndicator)
    r_thigh = l_thigh.replace(leftIndicator, rightIndicator)
    r_knee = l_knee.replace(leftIndicator, rightIndicator)
    r_ankle = l_ankle.replace(leftIndicator, rightIndicator)
    r_ball = l_ball.replace(leftIndicator, rightIndicator)
        
    with UndoContext():
        bipedSpineBuild(pelvis, spine1, chest, neck, head, controllerSize)
        bipedArmBuild("L", l_clavicle, l_shoulder, l_elbow, l_wrist, armFK, armIK, controllerSize)
        bipedArmBuild("R", r_clavicle, r_shoulder, r_elbow, r_wrist, armFK, armIK, controllerSize)
        bipedLegBuild("L", l_thigh, l_knee, l_ankle, l_ball, legFK, legIK, footRollControl, pelvis, controllerSize)
        bipedLegBuild("R", r_thigh, r_knee, r_ankle, r_ball, legFK, legIK, footRollControl, pelvis, controllerSize)
        finalConnections (armFK, legFK, controllerSize)

def bipedSpineBuild(pelvisJNT, spineBaseJNT, chestJNT, neckJNT, headJNT, controllerScale):         
    with UndoContext():   
        spineBaseIKJNT = spineBaseJNT + "_ik"
        cmds.duplicate(spineBaseJNT, rr = True, name = spineBaseIKJNT)
        cmds.select (spineBaseIKJNT, r = True)
        cmds.parent (world = True)
        
        # To check the number of spine joints present between Base Spine and Chest joint
        chestIKFound = False
        newSpineJnt = [spineBaseIKJNT]
        spineJointNumber = 0
        midSpineJNT = []
        midSpineIKJNT = []
        midSpineFKJNT = []
        
        while chestIKFound == False:        
            children = cmds.listRelatives(newSpineJnt[spineJointNumber], c = True)
            
            if (children[0] == chestJNT):
                chestIKFound = True
                chestIKJNT = cmds.rename ((newSpineJnt[spineJointNumber] + "|" + children[0]), chestJNT + "_ik")
                
                jointsToDelete = cmds.listRelatives (chestIKJNT, c = True, f = True)
                cmds.delete (jointsToDelete)
            else:
                midSpineJNT.append(children[0])
                addJoint = newSpineJnt[spineJointNumber] + "|" + children[0]
                newSpineJnt.append(addJoint)
                spineJointNumber = spineJointNumber + 1
        
        #Rename the middle spine joints
        newSpineJnt.remove (spineBaseIKJNT)
        midSpineCount = len (newSpineJnt)
        
        if midSpineCount > 0:
            jointCount = 1
            for joint in newSpineJnt:
                newName = cmds.rename ((newSpineJnt[midSpineCount-jointCount]), (midSpineJNT[midSpineCount-jointCount]) + '_ik') #Renaming the middle spine joints
                midSpineIKJNT.insert(0, newName) #Addind the middle spine joints to an array
                jointCount = jointCount + 1
        
        #Creating the FK joint chain
        spineBaseFKJNT = spineBaseJNT + "_fk"
        cmds.duplicate(spineBaseIKJNT, rr = True, n = spineBaseFKJNT)
        
        mel.eval ("searchReplaceNames {0} {1} {2};".format("_ik", "_fk", "hierarchy"))
        
        chestFKJNT = "{0}_fk".format(chestJNT)
        
        cmds.select (spineBaseFKJNT, hi = True)
        
        midSpineFKJNT = cmds.ls(selection = True)
        midSpineFKJNT.remove(spineBaseFKJNT)
        midSpineFKJNT.remove(chestFKJNT)
        
        #Contraining the IK Joints to the Bind Joints
        cmds.select(spineBaseIKJNT, spineBaseJNT, r = True)
        cmds.parentConstraint (weight = 1)
        
        cmds.select(chestIKJNT, chestJNT, r = True)
        cmds.parentConstraint (weight = 1)
        
        for i in range (len(midSpineIKJNT)):
            cmds.select(midSpineIKJNT[i], midSpineJNT[i], r = True)
            cmds.parentConstraint(weight = 1)
            
        #Creating Spine Base and Tip Joint to control the Spline IK Curve
        splineBaseJNT = cmds.duplicate (spineBaseIKJNT, rr = True, n = "spineBase_JNT")
        cmds.delete(cmds.listRelatives(splineBaseJNT, c = True, f = True))
        splineTipJNT = cmds.duplicate (chestIKJNT, rr = True, n = "spineTip_JNT")
        cmds.select(splineTipJNT, r = True)
        cmds.parent (world = True)
        
        
        #Adding in Spline IK from the base spine joint to the chest joint
        splineIkSolver = cmds.ikHandle (name = "spine_IKH", sj = spineBaseIKJNT, ee = chestIKJNT, sol = "ikSplineSolver", scv = False)
        
        splineCurve = splineIkSolver[2]
        splineCurve = cmds.rename(splineCurve, "spline_CUR")
        cmds.rename(splineIkSolver[1], "spline_EFF")
        
        splineIkSolver = splineIkSolver[0]
        
        #Skinning the Spline Base and the Tip joints to the spline curve
        cmds.skinCluster (splineBaseJNT, splineTipJNT, splineCurve, tsb = True, n = "splineIK_skinCluster")
        
        cmds.setAttr("{0}.inheritsTransform".format(splineCurve), 0)

        #Creating controllers for the spline Ik and pelvis joints
        splineBaseJNT_ctrl =  cmds.circle (c = (0,0,0), nr = (0,1,0), sw = 360, r = 1, d = 3, ut = 0, tol = 0.01, s = 8, ch = 1, n = "splineBase_CTRL")
        splineBaseJNT_ctrl = splineBaseJNT_ctrl[0]
        cmds.rotate (0,0,90, splineBaseJNT_ctrl)
        cmds.scale(controllerScale * 3, controllerScale * 3, controllerScale * 3, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
        
        splineBaseJNT_con = cmds.group(n = "splineBase_CTRL_CON")
        splineBaseJNT_offset = cmds.group(n = "splineBase_CTRL_0")
        
        splineTipJNT_ctrl =  cmds.circle (c = (0,0,0), nr = (0,1,0), sw = 360, r = 1, d = 3, ut = 0, tol = 0.01, s = 8, ch = 1, n = "splineTip_CTRL")
        splineTipJNT_ctrl = splineTipJNT_ctrl[0]
        cmds.rotate (0,0,90, splineTipJNT_ctrl)
        cmds.scale(controllerScale * 3, controllerScale * 3, controllerScale * 3, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
        
        splineTipJNT_con = cmds.group(n = "splineTip_CTRL_CON")
        splineTipJNT_offset = cmds.group(n = "splineTip_CTRL_0")
        
        pelvisJNT_ctrl = mel.eval ("curve -d 1 -p -1 0 1 -p -1 0 -1 -p 1 0 -1 -p 1 0 1 -p -1 0 1 -k 0 -k 1 -k 2 -k 3 -k 4 ;")
        pelvisJNT_ctrl = cmds.rename (pelvisJNT_ctrl, "pelvis_CTRL")
        cmds.scale(controllerScale * 3, controllerScale * 3, controllerScale * 3, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
        
        pelvisJNT_con = cmds.group(n = "pelvis_CTRL_CON")
        pelvisJNT_offset = cmds.group(n = "pelvis_CTRL_0")
        
        #Placing the controllers to their respective places
        cmds.select (splineBaseJNT, splineBaseJNT_offset, r = True)
        cmds.delete (cmds.parentConstraint (weight = 1))
        
        cmds.select (splineTipJNT, splineTipJNT_offset, r = True)
        cmds.delete (cmds.parentConstraint (weight = 1))
        
        cmds.select (pelvisJNT, pelvisJNT_offset, r = True)
        cmds.delete (cmds.pointConstraint (offset = (0,0,0), weight = 1))
        
        #Establishing the connections between the controllers and their respective joints
        cmds.select (splineBaseJNT_ctrl, splineBaseJNT, r = True)
        cmds.parentConstraint (weight = 1)
        
        cmds.select (splineTipJNT_ctrl, splineTipJNT, r = True)
        cmds.parentConstraint (weight = 1)
        
        cmds.select (splineBaseJNT_offset, splineTipJNT_offset, pelvisJNT_ctrl, r = True)
        cmds.parent()
        
        cmds.select (splineBaseJNT_ctrl, pelvisJNT, r = True)
        cmds.parentConstraint(mo = True, weight = 1)
        
        cmds.select (splineTipJNT_ctrl, chestIKJNT, r = True)
        cmds.orientConstraint(offset = (0,0,0), weight = 1)
        
        cmds.select(chestFKJNT, splineTipJNT_offset, r = True)
        cmds.parentConstraint (weight = 1)
        
        cmds.select(pelvisJNT_ctrl, spineBaseFKJNT, r = True)
        cmds.parentConstraint (mo = True, weight = 1)
        
        #Creating FK controllers for all the mid spine joints and aligning them to their respective joints
        midSpineFK_ctrl = []
        midSpineFK_off = []
        
        for i in range (len(midSpineFKJNT)):
            newCTRL =  cmds.circle (c = (0,0,0), nr = (0,1,0), sw = 360, r = 1, d = 3, ut = 0, tol = 0.01, s = 8, ch = 1, n = midSpineFKJNT[i].replace ('JNT', 'CTRL'))
            cmds.rotate (0,0,90, newCTRL)
            cmds.scale(controllerScale * 3, controllerScale * 3, controllerScale * 3, r = True)
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            
            midSpineFK_ctrl.append(newCTRL[0])             
        
            cmds.group(n = newCTRL[0] + "_CON")
            newGRP = cmds.group(n = newCTRL[0] + "_0")
            
            midSpineFK_off.append(newGRP)
            
            cmds.select (midSpineFKJNT[i], newGRP, r = True)
            cmds.delete (cmds.parentConstraint(weight = 1))
            
            #Constrainting the mid spine FK joints to the controllers
            cmds.select (midSpineFK_ctrl[i], midSpineFKJNT[i], r = True)
            cmds.parentConstraint(weight = 1)
        
        #Grouping the mid spine controllers to each other
        if midSpineCount > 1:
            for i in range (midSpineCount-1):
                cmds.select(midSpineFK_off[(midSpineCount - (i+1))], midSpineFK_ctrl[(midSpineCount - (i+2))], r = True)
                cmds.parent()
            
        cmds.select(midSpineFK_off[0], pelvisJNT_ctrl, r= True)
        cmds.parent()        
        
        #Setting up the Advanced Twist Controls (from the spline IKH attributes)
        cmds.setAttr("{0}.dTwistControlEnable".format(splineIkSolver), 1)    
        cmds.setAttr("{0}.dWorldUpType".format(splineIkSolver), 4)     
        cmds.connectAttr("{0}.worldMatrix".format(splineBaseJNT_ctrl), "{0}.dWorldUpMatrix".format(splineIkSolver))
        cmds.connectAttr("{0}.worldMatrix".format(splineTipJNT_ctrl), "{0}.dWorldUpMatrixEnd".format(splineIkSolver)) 
        
        #Organizing the joints and the controllers
        cmds.select (spineBaseFKJNT, spineBaseIKJNT, splineBaseJNT, splineTipJNT, r = True)
        spineJNT_grp = cmds.group(n = "spine_JNT_GRP")
        
        cmds.select (pelvisJNT_offset, r = True)
        spineCTRL_grp = cmds.group (n = "spine_CTRL_GRP")
        
        cmds.select (splineIkSolver, splineCurve, r = True)
        spineMISC_grp = cmds.group (n = "spine_MISC_GRP")
        
        #Neck and Head Build
        neckBaseFKJNT = neckJNT + "_fk"
        cmds.duplicate(neckJNT, rr = True, name = neckBaseFKJNT)
        cmds.select (neckBaseFKJNT, r = True)
        cmds.parent (world = True)
        
        # To check the number of neck joints present between Base Neck and Head joint
        headFound = False
        newNeckJnt = [neckBaseFKJNT]
        neckJointNumber = 0
        midNeckJNT = []
        midNeckFKJNT = []
        
        neckHeadJointsList = [neckJNT]
        neckHeadFKJointsList = [neckBaseFKJNT]
        
        while headFound == False:        
            children = cmds.listRelatives(newNeckJnt[neckJointNumber], c = True)
            
            if (children[0] == headJNT):
                headFound = True
                headFKJNT = cmds.rename ((newNeckJnt[neckJointNumber] + "|" + children[0]), headJNT + "_fk")
                
                jointsToDelete = cmds.listRelatives (headFKJNT, c = True, f = True)
                cmds.delete (jointsToDelete)
            else:
                midNeckJNT.append(children[0])
                addJoint = newNeckJnt[neckJointNumber] + "|" + children[0]
                newNeckJnt.append(addJoint)
                neckJointNumber = neckJointNumber + 1
        
            
        #Rename the middle neck joints
        newNeckJnt.remove (neckBaseFKJNT)
        midNeckCount = len (newNeckJnt)
        
        if midNeckCount > 0:
            jointCount = 1
            for joint in newNeckJnt:
                newName = cmds.rename((newNeckJnt[midNeckCount-jointCount]), (midNeckJNT[midNeckCount-jointCount] + '_fk'))
                midNeckFKJNT.insert(0, newName) #Addind the middle neck joints to an array
                jointCount = jointCount + 1
        
        #Adding all the neck and head joints to one list
        for fkneck, neckjnt in zip (midNeckFKJNT, midNeckJNT):
            neckHeadJointsList.append (neckjnt)
            neckHeadFKJointsList.append (fkneck)
        
        #Lists with the complete head and the neck joints
        neckHeadJointsList.append(headJNT)
        neckHeadFKJointsList.append(headFKJNT)
        
        #Constraining the fk joints to the bind joints
        for bindJoint, fkJoint in zip (neckHeadJointsList, neckHeadFKJointsList):
            cmds.parentConstraint (fkJoint, bindJoint, weight = 1)
            
        #Creating FK controllers for the neck and head joints
        neckFK_ctrl = []
        neckFK_off = []
        
        for i, neckFKJNT in enumerate(neckHeadFKJointsList):
            newCTRL = cmds.circle (c = (0,0,0), nr = (0,1,0), sw = 360, r = 1, d = 3, ut = 0, tol = 0.01, s = 8, ch = 1, n = neckFKJNT.replace('JNT', 'CTRL'))
            cmds.rotate (0,0,90, newCTRL)
            cmds.scale(controllerScale * 2, controllerScale * 2, controllerScale * 2, r = True)
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            
            neckFK_ctrl.append(newCTRL[0])
            
            cmds.group (n = newCTRL[0] + '_CON')
            newGRP = cmds.group(n = newCTRL[0] + "_0")
            
            neckFK_off.append(newGRP)
            
            cmds.select (neckFKJNT, newGRP, r = True)
            cmds.delete (cmds.parentConstraint(weight = 1))
            
            #Constrainting the mid spine FK joints to the controllers
            cmds.select (neckFK_ctrl[i], neckFKJNT, r = True)
            cmds.parentConstraint(weight = 1)
        
        neckJNTCount = len (neckHeadFKJointsList)
        #Grouping the neck and the head controllers to each other
        if neckJNTCount > 1:
            for i in range (neckJNTCount - 1):
                cmds.select(neckFK_off[(neckJNTCount - (i + 1))], neckFK_ctrl[(neckJNTCount - (i + 2))], r = True)
                cmds.parent()  
        
        #Organizing the neck and the head controllers
        cmds.select (neckHeadFKJointsList[0], r = True)
        neckJNT_grp = cmds.group (n = "neck_JNT_GRP")
        
        cmds.select (neckFK_off[0], r = True)
        neckCTRL_grp = cmds.group (n = "neck_CTRL_GRP")
        
        #Connecting the spine with the neck controls
        cmds.select (chestJNT, neckFK_off[0], r = True)
        cmds.parentConstraint (mo = True, weight = 1)
        
        #Adding in Color to the New Controllers
        cmds.select (splineBaseJNT_ctrl, splineTipJNT_ctrl, neckFK_ctrl, midSpineFK_ctrl, pelvisJNT_ctrl, r = True)
        shapesSelect = cmds.ls (selection = 1, shapes = True, dag = True) #Selecting all the shapes from the newly created controller
        
        #Going through all the shapes and changing the RGB color through the 'Drawing Overrides'
        for shape in shapesSelect:
            cmds.setAttr(shape + ".overrideEnabled", 1)
            cmds.setAttr(shape + ".overrideRGBColors", 1)
            cmds.setAttr(shape + ".overrideColorRGB", 255, 255, 0)
    
#Arm Setup
def bipedArmBuild(side, clavicleJNT, shoulderJNT, elbowJNT, wristJNT, armfkSetup, armikSetup, controllerScale):        
    with UndoContext():
        #Creating clavicle FK Joint
        clavicleFKJNT = clavicleJNT + "_fk"
        cmds.duplicate (clavicleJNT, rr = True, name = clavicleFKJNT)
        cmds.select (clavicleFKJNT, r = True)
        cmds.parent (world = True)
        
        #Deleting everything in the hierarchy for the clavicle joint
        clavicleChild = cmds.listRelatives (clavicleFKJNT, c = True, f = True)
        cmds.delete (clavicleChild)
        
        #Parent constrainting clavicle fk joint to the bind joint
        cmds.parentConstraint (clavicleFKJNT, clavicleJNT, weight = 1)
        
        #Creating the clavicle controller
        clavicleCTRL = cmds.circle (c = (0,0,0), nr = (0,1,0), sw = 360, r = 1, d = 3, ut = 0, tol = 0.01, s = 8, ch = 1 , n = (side + "_clavicle_CTRL"))[0]
        cmds.scale(controllerScale, controllerScale, controllerScale, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
        clavicleCON = cmds.group(n = side + "_clavicle_CTRL_CON")
        clavicleOFF = cmds.group(n = side + "_clavicle_CTRL_0")
        
        #Snapping the clavicle controller to the joint
        cmds.select (clavicleFKJNT, clavicleOFF, r = True)
        cmds.delete (cmds.parentConstraint (weight = 1))
        cmds.select (clavicleCTRL+".cv[0:7]", r = True)
        cmds.rotate (0, 0, -90, r = True, os = True, fo = True)
        
        #Connecting the clavicle controller to the joint
        cmds.parentConstraint (clavicleCTRL, clavicleFKJNT, weight = 1, mo = False)
        
        #Grouping the Clavicle joints and controllers to their respective places
        cmds.group (em = True, n = side + "_clavicle_CTRL_GRP")
        cmds.parent (clavicleOFF, side + "_clavicle_CTRL_GRP", r = False)
        
        cmds.group (em = True, n = side + "_clavicle_JNT_GRP")
        cmds.parent (clavicleFKJNT, side + "_clavicle_JNT_GRP", r = False)
        
        shoulderTwistFKJNT = []
        elbowTwistFKJNT = []
        shoulderTwistIKJNT = []
        elbowTwistIKJNT = []
        
        
        if armfkSetup:
            #FK Setup
            #Joints
            shoulderFKJNT = shoulderJNT + "_fk"
            elbowFKJNT = elbowJNT + "_fk"
            wristFKJNT = wristJNT + "_fk"
            
            #Duplicating the bind joint to create a fk joint
            for jnts in [shoulderJNT, elbowJNT, wristJNT]:
                duplicateJnt = cmds.duplicate (jnts, rr = True, name = jnts + '_fk')
                cmds.select (duplicateJnt, r = True)
                cmds.parent (world = True)
                
                cmds.delete (cmds.listRelatives(duplicateJnt, c = True, f = True))
            
            #Parenting the FK joints to one another
            cmds.parent (wristFKJNT, elbowFKJNT)
            cmds.parent (elbowFKJNT, shoulderFKJNT)
            
                        
            #Controllers
            #Shoulder FK Controller
            shoulderFKCTRL = cmds.circle (c = (0,0,0), nr = (0,1,0), sw = 360, r = 1, d = 3, ut = 0, tol = 0.01, s = 8, ch = 1 , n = (side + "_shoulderFK_CTRL"))[0]
            cmds.scale(controllerScale, controllerScale, controllerScale, r = True)
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            shoulderFKCON = cmds.group(n = side + "_shoulderFK_CTRL_CON")
            shoulderFKOFF = cmds.group(n = side + "_shoulderFK_CTRL_0")
            
            #Elbow FK Controller
            elbowFKCTRL = cmds.circle (c = (0,0,0), nr = (0,1,0), sw = 360, r = 1, d = 3, ut = 0, tol = 0.01, s = 8, ch = 1 , n = (side + "_elbowFK_CTRL"))[0]
            cmds.scale(controllerScale, controllerScale, controllerScale, r = True)
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            elbowFKCON = cmds.group(n = side + "_elbowFK_CTRL_CON")
            elbowFKOFF = cmds.group(n = side + "_elbowFK_CTRL_0")
        
            #Wrist FK Controller
            wristFKCTRL = cmds.circle (c = (0,0,0), nr = (0,1,0), sw = 360, r = 1, d = 3, ut = 0, tol = 0.01, s = 8, ch = 1 , n = (side + "_wristFK_CTRL"))[0]
            cmds.scale(controllerScale, controllerScale, controllerScale, r = True)
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            wristFKCON = cmds.group(n = side + "_wristFK_CTRL_CON")
            wristFKOFF = cmds.group(n = side + "_wristFK_CTRL_0")
        
            #Snapping the fk controller to their respective joints
            cmds.select (shoulderFKJNT, shoulderFKOFF, r = True)
            cmds.delete (cmds.parentConstraint (weight = 1))
            cmds.select (shoulderFKCTRL+".cv[0:7]", r = True)
            cmds.rotate (0, 0, -90, r = True, os = True, fo = True)
            
            cmds.select (elbowFKJNT, elbowFKOFF, r = True)
            cmds.delete (cmds.parentConstraint (weight = 1))
            cmds.select (elbowFKCTRL+".cv[0:7]", r = True)
            cmds.rotate (0, 0, -90, r = True, os = True, fo = True)
            
            cmds.select (wristFKJNT, wristFKOFF, r = True)
            cmds.delete (cmds.parentConstraint (weight = 1))
            cmds.select (wristFKCTRL+".cv[0:7]", r = True)
            cmds.rotate (0, 0, -90, r = True, os = True, fo = True)
            
            #Setting up the controllers in their hierachy
            cmds.parent(wristFKOFF, elbowFKCTRL, r = False)
            cmds.parent(elbowFKOFF, shoulderFKCTRL, r = False)
            
            cmds.group (em = True, n = side + "_armFK_CTRL_GRP")
            cmds.parent(shoulderFKOFF, side + "_armFK_CTRL_GRP", r = False)
            
            #Connecting the controllers to their respective joints
            cmds.parentConstraint (shoulderFKCTRL, shoulderFKJNT, weight = 1, mo = False)
            cmds.parentConstraint (elbowFKCTRL, elbowFKJNT, weight = 1, mo = False)
            cmds.parentConstraint (wristFKCTRL, wristFKJNT, weight = 1, mo = False)
            
            #Creating a connection between the clavicle and the fk shoulder using 'const_loc' method
            #Getting the position of the shoulder fk joint
            shoulderFKPOS = cmds.xform (shoulderFKJNT, q = True, ws = True, t = True)
            shoulderLoc = cmds.spaceLocator (p = (0,0,0), n = side + "_shoulderFK_CTRL_CONST_LOC")
            cmds.move (shoulderFKPOS[0], shoulderFKPOS[1], shoulderFKPOS[2])
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            
            shoulderGRP = cmds.group (em = True, n = side + "_shoulder_FK_CTRL_GRP")
            cmds.move (shoulderFKPOS[0], shoulderFKPOS[1], shoulderFKPOS[2])
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            cmds.select (side + "_armFK_CTRL_GRP", add = True)
            cmds.parent()
            cmds.parent (shoulderFKOFF, side + "_shoulder_FK_CTRL_GRP", r = False)
            
            cmds.parentConstraint(clavicleCTRL, shoulderLoc[0], mo = True, weight = 1)
            cmds.pointConstraint (shoulderLoc[0], shoulderGRP, offset = (0,0,0), weight = 1)
            
            armMISC_grp = cmds.group (em = True, n = side + "_arm_MISC_GRP")
            cmds.parent (shoulderLoc[0], side + "_arm_MISC_GRP", r = False)
            
            #Checking if there are twist joints parented to the shoulder
            shoulderChildJoint = cmds.listRelatives (shoulderJNT, c = True)
                        
            #If there are more than 1 children for the shoulder joint [the one being the elbow joint]
            if len(shoulderChildJoint) > 1:
                for jnt in shoulderChildJoint:
                    if 'twist' in jnt:
                        twistDuplicate = cmds.duplicate(jnt, rr = True, n = jnt + '_fk')[0]
                        cmds.parent (twistDuplicate, w = True)
                        shoulderTwistFKJNT.append(twistDuplicate)
                
                shoulderTwistFKJNT.sort()
                
                #Breaking the connection between the shoulderFK controller and the shoulderFk joint rotate X
                connectRotateX = cmds.listConnections (shoulderFKJNT + '.rotateX', s = 1, p = 1)[0]
                cmds.disconnectAttr(connectRotateX, shoulderFKJNT + '.rotateX')
                
                #Creating a multDoubleLinear node to divide the value of rotate X to the respective twist joints
                for i, jnt in enumerate(shoulderTwistFKJNT):
                    multDblNode = cmds.createNode('multDoubleLinear', n = jnt + '_mdl')
                    
                    input2Numo = i + 1.0
                    input2Deno = len(shoulderTwistFKJNT) + 1.0
                    
                    input2Value = input2Numo/input2Deno
                    
                    cmds.setAttr(multDblNode + '.input2', input2Value)
                    
                    cmds.connectAttr(shoulderFKCTRL + '.rotateX', multDblNode + '.input1')
                    
                    cmds.connectAttr (multDblNode + '.output', jnt + '.rotateX')  
            
            
            #Checking if there are twist joints parented to the elbow
            elbowChildJoint = cmds.listRelatives (elbowJNT, c = True)
            
            #If there are more than 1 children for the elbow joint [the one being the wrist jnt]
            if len(elbowChildJoint) > 1:
                for jnt in elbowChildJoint:
                    if 'twist' in jnt:
                        twistDuplicate = cmds.duplicate(jnt, rr = True, n = jnt + '_fk')[0]
                        cmds.parent (twistDuplicate, w = True)
                        elbowTwistFKJNT.append(twistDuplicate)
                
                elbowTwistFKJNT.sort()
                
                #Creating a multDoubleLinear node to divide the value of rotate X to the respective twist joints
                for i, jnt in enumerate(elbowTwistFKJNT):
                    multDblNode = cmds.createNode('multDoubleLinear', n = jnt + '_mdl')
                    
                    input2Numo = i + 1.0
                    input2Deno = len(elbowTwistFKJNT) + 1.0
                    
                    input2Value = input2Numo/input2Deno
                    
                    cmds.setAttr(multDblNode + '.input2', input2Value)
                    
                    cmds.connectAttr(wristFKCTRL + '.rotateX', multDblNode + '.input1')
                    
                    cmds.connectAttr (multDblNode + '.output', jnt + '.rotateX') 
            
            cmds.select (shoulderTwistFKJNT, shoulderFKJNT, r = True)
            cmds.parent()
            cmds.select (elbowTwistFKJNT, elbowFKJNT, r = True)
            cmds.parent()
            
                        
        if armikSetup:
            #IK Setup
            #Joints
            shoulderIKJNT = shoulderJNT + "_ik"
            elbowIKJNT = elbowJNT + "_ik"
            wristIKJNT = wristJNT + "_ik"
            
            #Duplicating the bind joint to create a fk joint
            for jnts in [shoulderJNT, elbowJNT, wristJNT]:
                duplicateJnt = cmds.duplicate (jnts, rr = True, name = jnts + '_ik')
                cmds.select (duplicateJnt, r = True)
                cmds.parent (world = True)
                
                cmds.delete (cmds.listRelatives(duplicateJnt, c = True, f = True))
            
            #Parenting the FK joints to one another
            cmds.parent (wristIKJNT, elbowIKJNT)
            cmds.parent (elbowIKJNT, shoulderIKJNT)
            
            #Controllers
            #Pole Vector Controller
            elbowIKCTRL = mel.eval ("curve -d 1 -p 0 0 0 -p 0 0.4 -0.4 -p 0 0.2 -0.4 -p 0 0.2 -1 -p 0 -0.2 -1 -p 0 -0.2 -0.4 -p 0 -0.4 -0.4 -p 0 0 0 -p -0.4 0 -0.4 -p -0.2 0 -0.4 -p -0.2 0 -1 -p 0.2 0 -1 -p 0.2 0 -0.4 -p 0.4 0 -0.4 -p 0 0 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 ;")    
            elbowIKCTRL = cmds.rename (elbowIKCTRL, side + "_elbowIK_CTRL")
            cmds.scale(controllerScale, controllerScale, controllerScale, r = True)
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            
            elbowIKCON = cmds.group (n = side + "_elbowIK_CTRL_CON")
            cmds.xform (elbowIKCON, ws = True, pivots = (0,0,0))
            elbowIKOFF = cmds.group (n = side + "_elbowIK_CTRL_0")
            cmds.xform (elbowIKOFF, ws = True, pivots = (0,0,0))
            
            #Creating Arrow connecting pole vector controller and elbow joint
            annoteLoc = cmds.spaceLocator (n = elbowIKJNT + '_annotation_LOC')
            cmds.delete (cmds.parentConstraint (elbowIKJNT, annoteLoc, weight = 1))
            
            cmds.parent (annoteLoc, elbowIKJNT)
            
            annotationShape = cmds.annotate(annoteLoc)
            annote = cmds.group (annotationShape, n = elbowIKJNT + '_annotation')
            
            cmds.setAttr (annotationShape + '.overrideEnabled', 1)
            cmds.setAttr (annotationShape + '.overrideDisplayType', 1)
            
            cmds.parent (annote, elbowIKCTRL)
            cmds.ResetTransformations(annote)

            #Main Controller
            armIKCTRL = cmds.curve (d = 1, n = side + "_armIK_CTRL", p = [(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1), (-1, 0, -1)], k = [0, 1, 2, 3, 4])
            cmds.scale(controllerScale, controllerScale, controllerScale, r = True)   
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory() 
            
            armIKCON = cmds.group (n = side + "_armIK_CTRL_CON")
            armIKOFF = cmds.group (n = side + "_armIK_CTRL_0")
        
            #Snapping the fk controller to their respective joints
            cmds.select (wristIKJNT, armIKOFF, r= True)
            cmds.delete (cmds.parentConstraint (weight = 1))
            cmds.select (armIKCTRL+".cv[0:4]", r = True)
            cmds.rotate (0, 0, -90, r = True, os = True, fo = True)
            
            #Setting up the Pole-Vector position
            tempPlane = cmds.polyPlane(subdivisionsHeight = 1, subdivisionsWidth = 1)[0]
            cmds.delete(tempPlane + '.vtx[3]')

            shoulderPos = cmds.xform (shoulderIKJNT, q = True, ws = True, translation = True)
            cmds.xform (tempPlane + '.vtx[0]', ws = True, translation = shoulderPos)

            elbowPos = cmds.xform (elbowIKJNT, q = True, ws = True, translation = True)
            cmds.xform (tempPlane + '.vtx[1]', ws = True, translation = elbowPos)

            wristPos = cmds.xform (wristIKJNT, q = True, ws = True, translation = True)
            cmds.xform (tempPlane + '.vtx[2]', ws = True, translation = wristPos)
            
            if (elbowPos[0] < 0):
                uValue = -5 * controllerScale
            else:
                uValue = 5 * controllerScale
            
            cmds.moveVertexAlongDirection (tempPlane + '.vtx[1]', u = uValue) #Moving the elbow vertex of the plane along the V-normal axis

            poleVectorPos = cmds.xform (tempPlane + '.vtx[1]', q = True, ws = True, translation = True)
            cmds.xform (elbowIKOFF, ws = True, translation = poleVectorPos)

            cmds.delete(tempPlane)
            
            #Setting up the controllers in their hierachy
            cmds.group (em = True, n = side + "_armIK_CTRL_GRP")
            cmds.parent(armIKOFF, elbowIKOFF, side + "_armIK_CTRL_GRP", r = False)
            
            #Creating the connection from the controller to the joints
            #Creating the IK Handles
            ArmIKHandle = cmds.ikHandle (n = wristIKJNT + "_IKH", shf = False, s = "sticky", fs = True, sj = shoulderIKJNT, ee = wristIKJNT)
            cmds.rename(ArmIKHandle[1], wristIKJNT + "_EFF")
            
            #Parenting the IKH to the main controller and creating a pole vector constraint
            cmds.select(ArmIKHandle[0], armIKCTRL, r = True)
            cmds.parent()
            cmds.select(elbowIKCTRL, ArmIKHandle[0], r = True)
            poleVector = cmds.poleVectorConstraint (weight = 1)
            
            #Hide the IK Handle
            cmds.setAttr(ArmIKHandle[0] + ".v", 0)
            
            cmds.select(armIKCTRL, wristIKJNT, r = True)
            cmds.orientConstraint (offset = (0,0,0), weight = 1)
            
            #Adding a follow attribute to the pole vector controller
            cmds.select(elbowIKCTRL, r = True)
            cmds.addAttr (ln = "follow", at = "enum", en = "<none>:Wrist:", k = True)
            
            cmds.select(armIKCTRL, elbowIKOFF, r = True)
            secondGrpCONST = cmds.parentConstraint (maintainOffset = True, weight = 1)
            
            #Creating connection for the above created attributes using SDK
            cmds.setDrivenKeyframe (secondGrpCONST[0] + "." + armIKCTRL + "W0", dv = 0, v = 0, cd = elbowIKCTRL + '.follow')
            cmds.setDrivenKeyframe (secondGrpCONST[0] + "." + armIKCTRL + "W0", dv = 1, v = 1, cd = elbowIKCTRL + '.follow')
            
            #Creating a constraint between the clavicle controller and the shoulder ik joint.
            cmds.parentConstraint (clavicleCTRL, shoulderIKJNT, weight = 1, mo = True)
            
            
            #Checking if there are twist joints parented to the shoulder
            shoulderChildJoint = cmds.listRelatives (shoulderJNT, c = True)
                        
            #If there are more than 1 children for the shoulder joint [the one being the elbow joint]
            if len(shoulderChildJoint) > 1:
                for jnt in shoulderChildJoint:
                    if 'twist' in jnt:
                        twistDuplicate = cmds.duplicate(jnt, rr = True, n = jnt + '_ik')[0]
                        cmds.parent (twistDuplicate, w = True)
                        shoulderTwistIKJNT.append(twistDuplicate)
                
                shoulderTwistIKJNT.sort()
            
            #Checking if there are twist joints parented to the elbow
            elbowChildJoint = cmds.listRelatives (elbowJNT, c = True)
            
            #If there are more than 1 children for the elbow joint [the one being the wrist jnt]
            if len(elbowChildJoint) > 1:
                for jnt in elbowChildJoint:
                    if 'twist' in jnt:
                        twistDuplicate = cmds.duplicate(jnt, rr = True, n = jnt + '_ik')[0]
                        cmds.parent (twistDuplicate, w = True)
                        elbowTwistIKJNT.append(twistDuplicate)
                
                elbowTwistIKJNT.sort()
                
                #Creating a multDoubleLinear node to divide the value of rotate X to the respective twist joints
                for i, jnt in enumerate(elbowTwistIKJNT):
                    multDblNode = cmds.createNode('multDoubleLinear', n = jnt + '_mdl')
                    
                    input2Numo = i + 1.0
                    input2Deno = len(elbowTwistIKJNT) + 1.0
                    
                    input2Value = input2Numo/input2Deno
                    
                    cmds.setAttr(multDblNode + '.input2', input2Value)
                    
                    cmds.connectAttr(armIKCTRL + '.rotateX', multDblNode + '.input1')
                    
                    cmds.connectAttr (multDblNode + '.output', jnt + '.rotateX')  
            
            cmds.select (shoulderTwistIKJNT, shoulderIKJNT, r = True)
            cmds.parent()
            cmds.select (elbowTwistIKJNT, elbowIKJNT, r = True)
            cmds.parent()
            
            
        if (armfkSetup and armikSetup):            
            # IK-FK Switch
            ikFkControl = mel.eval ("curve -d 1 -p -1.541097 0 -0.407608 -p -1.997943 0 -0.287409 -p -1.996633 0 0.292773 -p -1.540642 0 0.404437 -p -1.376247 0 0.800967 -p -1.614601 0 1.209387 -p -1.206218 0 1.618289 -p -0.802518 0 1.37467 -p -0.406558 0 1.538403 -p -0.285068 0 1.998563 -p 0.293543 0 1.996772 -p 0.405503 0 1.538183 -p 0.800499 0 1.376064 -p 1.209852 0 1.613362 -p 1.618868 0 1.206081 -p 1.37717 0 0.803675 -p 1.540102 0 0.406725 -p 1.997785 0 0.285372 -p 1.997147 0 -0.294228 -p 1.540467 0 -0.405926 -p 1.377365 0 -0.800905 -p 1.615038 0 -1.210376 -p 1.206209 0 -1.619887 -p 0.802833 0 -1.375844 -p 0.40785 0 -1.540751 -p 0.28608 0 -1.998594 -p -0.29285 0 -1.997769 -p -0.405278 0 -1.539256 -p -0.801016 0 -1.37748 -p -1.208227 0 -1.614979 -p -1.619464 0 -1.206488 -p -1.37182 0 -0.798064 -p -1.541097 0 -0.407608 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 -k 17 -k 18 -k 19 -k 20 -k 21 -k 22 -k 23 -k 24 -k 25 -k 26 -k 27 -k 28 -k 29 -k 30 -k 31 -k 32;")
            delController = mel.eval ("circle -c 0 0 0 -r 0.8 -nr 0 1 0")
            delControllerShapes = cmds.listRelatives(delController, shapes = True)
            cmds.select (delControllerShapes, r = True)
            cmds.select (ikFkControl, add = True)
            cmds.parent (r = True, s = True)
            cmds.delete (delController)
            ikFkControl = cmds.rename (ikFkControl, side + '_armSwitch_CTRL')
            
            ikFkControl = side + '_armSwitch_CTRL'
            cmds.select (ikFkControl)
            cmds.rotate (90, 0, 0)
            cmds.scale (controllerScale/4, controllerScale/4, controllerScale/4)
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()

            cmds.group (n = side + '_armSwitch_CTRL_GRP', empty = True)

            cmds.parent (ikFkControl, side + '_armSwitch_CTRL_GRP')

            cmds.select (wristJNT, side + '_armSwitch_CTRL_GRP', r = True)
            cmds.pointConstraint(weight = 1)
            cmds.orientConstraint(weight = 1, maintainOffset = 1)

            cmds.select (ikFkControl + '.cv[0:32]', r = True)
            cmds.move (0, 0, (-3 * controllerScale), os = True, wd = True, r = True)
            cmds.select (cl = True)

            cmds.select (ikFkControl, r = True)
            cmds.addAttr (ln = "FKIK", at = "float", min = 0, max = 1, dv = 0, k = True)
            
            #Getting the twist bind joints and creating alist
            #Shoulder
            shoulderTwistBindJntsTemp = cmds.listRelatives (shoulderJNT, c = True)
            shoulderTwistBindJnts = []
            
            #If there are more than 1 children for the shoulder joint [the one being the elbow jnt]
            if len(shoulderTwistBindJntsTemp) > 1:
                for jnt in shoulderTwistBindJntsTemp:
                    if 'twist' in jnt:
                        shoulderTwistBindJnts.append(jnt)
                    
                shoulderTwistBindJnts.sort()
            
            #Elbow
            elbowTwistBindJntsTemp = cmds.listRelatives (elbowJNT, c = True)
            elbowTwistBindJnts = []
            
            #If there are more than 1 children for the elbow joint [the one being the wrist jnt]
            if len(elbowTwistBindJntsTemp) > 1:
                for jnt in elbowTwistBindJntsTemp:
                    if 'twist' in jnt:
                        elbowTwistBindJnts.append(jnt)
                    
                elbowTwistBindJnts.sort()      
            
                        
            bindJnts = [shoulderJNT, elbowJNT, wristJNT] + shoulderTwistBindJnts + elbowTwistBindJnts
            fkJnts = [shoulderFKJNT, elbowFKJNT, wristFKJNT] + shoulderTwistFKJNT + elbowTwistFKJNT
            ikJnts = [shoulderIKJNT, elbowIKJNT, wristIKJNT] + shoulderTwistIKJNT + elbowTwistIKJNT
            
            #Connecting the FK-IK joints with the bind joints using blendColors node
            for bind, fk, ik in zip (bindJnts, fkJnts, ikJnts):
                for i in ['translate', 'rotate', 'scale']:
                    blendColor = cmds.createNode('blendColors', n = bind.replace('JNT', 'blendColors_{}'.format(i))) #Creating a blendnode to blend the bind joint between fk and ik joints
                    cmds.connectAttr('{0}.{1}'.format(fk, i), blendColor + '.color2')
                    cmds.connectAttr('{0}.{1}'.format(ik, i), blendColor + '.color1')
                    
                    #Only when dealing with the shoulder joint, since the local values for the shoulder bind joint and fk & ik joints are different, due to the bind shoulder joint being parented to the clavicle joint
                    #That is why we need to convert the world translate values to local translate values for the shoulder bind joint
                    if bind == bindJnts[0] and i == 'translate':
                        pointMatMult = cmds.createNode('pointMatrixMult', n = bind.replace('JNT', 'pointMatMult_{}'.format(i))) #Using 'pointMatrixMult' to get the local translate, rotate and scale values for the shoulder bind joint
                        cmds.connectAttr(clavicleJNT + '.worldInverseMatrix', pointMatMult + '.inMatrix')
                        cmds.connectAttr(blendColor + '.output', pointMatMult + '.inPoint')
                        cmds.connectAttr(pointMatMult + '.output', '{0}.{1}'.format(bind, i))
                    else:
                        cmds.connectAttr(blendColor + '.output', '{0}.{1}'.format(bind, i))
                    
                    cmds.connectAttr (ikFkControl + '.FKIK', blendColor + '.blender')            
                           
            #Locking the unwanted attributes for the switch controller
            cmds.setAttr(ikFkControl + ".tx", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".ty", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".tz", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".rx", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".ry", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".rz", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".sx", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".sy", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".sz", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".v", lock = True, keyable = False, channelBox = False)
            
            #Setting up the controllers in their hierachy
            cmds.group (em = True, n = side + "_armMain_CTRL_GRP")
            cmds.parent (side + "_armSwitch_CTRL_GRP", side + "_armMain_CTRL_GRP", r = False)
            
            armCTRL_grp = cmds.group (em = True, n = side + "_arm_CTRL_GRP")
            cmds.parent (side + "_armFK_CTRL_GRP", side + "_armIK_CTRL_GRP", side + "_armMain_CTRL_GRP", side + "_arm_CTRL_GRP", r = False)
            
            armJNT_grp = cmds.group(em = True, n = side + "_arm_JNT_GRP")
            cmds.parent (shoulderFKJNT, shoulderIKJNT, side + "_arm_JNT_GRP", r = False)
            
            #Connecting the visibility of the controllers to the switch using nodes
            cmds.connectAttr (ikFkControl + '.FKIK', side + "_armIK_CTRL_GRP.visibility")
            reverseNode = cmds.createNode('reverse', n = side + '_armControlVis_rev')
            cmds.connectAttr(ikFkControl + '.FKIK', reverseNode +'.inputX')
            cmds.connectAttr(reverseNode + '.outputX', side + "_armFK_CTRL_GRP.visibility")                    
                
            if (cmds.xform (shoulderJNT, q = True, ws = True, translation = True)[0] > 0): #Checking the side of the controllers usinmg the X position of the shoulder joint 
                controllerColorAssign(255, 0, 0, clavicleCTRL, shoulderFKCTRL, elbowFKCTRL, wristFKCTRL, armIKCTRL, elbowIKCTRL, ikFkControl)
            else:                    
                controllerColorAssign(0, 0, 255, clavicleCTRL, shoulderFKCTRL, elbowFKCTRL, wristFKCTRL, armIKCTRL, elbowIKCTRL, ikFkControl)
            
       
        elif (armfkSetup and not armikSetup):
            armCTRL_grp = cmds.group (em = True, n = side + "_arm_CTRL_GRP")
            cmds.parent (side + "_armFK_CTRL_GRP", side + "_arm_CTRL_GRP", r = False)
            
            armJNT_grp = cmds.group(em = True, n = side + "_arm_JNT_GRP")
            cmds.parent (shoulderFKJNT, side + "_arm_JNT_GRP", r = False)
                
            if (cmds.xform (shoulderJNT, q = True, ws = True, translation = True)[0] > 0): #Checking the side of the controllers usinmg the X position of the shoulder joint 
                controllerColorAssign(255, 0, 0, clavicleCTRL, shoulderFKCTRL, elbowFKCTRL, wristFKCTRL)
            else:                    
                controllerColorAssign(0, 0, 255, clavicleCTRL, shoulderFKCTRL, elbowFKCTRL, wristFKCTRL)
            
        elif (armikSetup and not armfkSetup):
            armCTRL_grp = cmds.group (em = True, n = side + "_arm_CTRL_GRP")
            cmds.parent (side + "_armIK_CTRL_GRP", side + "_arm_CTRL_GRP", r = False)
            
            armJNT_grp = cmds.group(em = True, n = side + "_arm_JNT_GRP")
            cmds.parent (shoulderIKJNT, side + "_arm_JNT_GRP", r = False)
                
            if (cmds.xform (shoulderJNT, q = True, ws = True, translation = True)[0] > 0): #Checking the side of the controllers usinmg the X position of the shoulder joint 
                controllerColorAssign(255, 0, 0, armIKCTRL, elbowIKCTRL)
            else:                    
                controllerColorAssign(0, 0, 255, armIKCTRL, elbowIKCTRL)
            
        else:
            #Give out an error message
            om.MGlobal.displayError("SELECT EITHER FK,IK OR BOTH FOR THE ARM SETUP")
            return
        
#Leg Setup
def bipedLegBuild(side, thighJNT, kneeJNT, ankleJNT, ballJNT, legfkSetup, legikSetup, footRollSetup, pelvisJNT, controllerScale):         
    with UndoContext():          
        #Heel Roll Locator's Name
        heelLoc = "L_heelPos_LOC"
        ankleRollInLoc = "L_ankleRollInPos_LOC"
        ankleRollOutLoc = "L_ankleRollOutPos_LOC"
        toeTipLoc = "L_toeTipPos_LOC"
                       
        thighTwistFKJNT = []
        kneeTwistFKJNT = []
        thighTwistIKJNT = []
        kneeTwistIKJNT = []
        
        if legfkSetup:
            #FK Setup
            #Joints
            thighFKJNT = thighJNT + "_fk"
            kneeFKJNT = kneeJNT + "_fk"
            ankleFKJNT = ankleJNT + "_fk"
            ballFKJNT = ballJNT + "_fk"
            
            #Duplicating the bind joints to create the fk joints
            for jnts in [thighJNT, kneeJNT, ankleJNT, ballJNT]:
                duplicateJnt = cmds.duplicate (jnts, rr = True, name = jnts + '_fk')
                cmds.select (duplicateJnt, r = True)
                cmds.parent (world = True)
                
                cmds.delete (cmds.listRelatives(duplicateJnt, c = True, f = True))
            
            #Parenting the FK Joints to one another
            cmds.parent (ballFKJNT, ankleFKJNT)
            cmds.parent (ankleFKJNT, kneeFKJNT)
            cmds.parent (kneeFKJNT, thighFKJNT)
            
            #Controllers
            #Thigh FK Controller
            thighFKCTRL = cmds.circle (c = (0,0,0), nr = (0,1,0), sw = 360, r = 1, d = 3, ut = 0, tol = 0.01, s = 8, ch = 1 , n = (side + "_thighFK_CTRL"))[0]
            cmds.scale(controllerScale, controllerScale, controllerScale, r = True)
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            thighFKCON = cmds.group(n = side + "_thighFK_CTRL_CON")
            thighFKOFF = cmds.group(n = side + "_thighFK_CTRL_0")
            
            #Knee FK Controller
            kneeFKCTRL = cmds.circle (c = (0,0,0), nr = (0,1,0), sw = 360, r = 1, d = 3, ut = 0, tol = 0.01, s = 8, ch = 1 , n = (side + "_kneeFK_CTRL"))[0]
            cmds.scale(controllerScale, controllerScale, controllerScale, r = True)
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            kneeFKCON = cmds.group(n = side + "_kneeFK_CTRL_CON")
            kneeFKOFF = cmds.group(n = side + "_kneeFK_CTRL_0")
        
            #Ankle FK Controller
            ankleFKCTRL = cmds.circle (c = (0,0,0), nr = (0,1,0), sw = 360, r = 1, d = 3, ut = 0, tol = 0.01, s = 8, ch = 1 , n = (side + "_ankleFK_CTRL"))[0]
            cmds.scale(controllerScale, controllerScale, controllerScale, r = True)
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            ankleFKCON = cmds.group(n = side + "_ankleFK_CTRL_CON")
            ankleFKOFF = cmds.group(n = side + "_ankleFK_CTRL_0")
            
            #Ball FK Controller
            ballFKCTRL = cmds.circle (c = (0,0,0), nr = (0,1,0), sw = 360, r = 1, d = 3, ut = 0, tol = 0.01, s = 8, ch = 1 , n = (side + "_ballFK_CTRL"))[0]
            cmds.rotate (0,0,90, ballFKCTRL)
            cmds.scale(controllerScale, controllerScale, controllerScale, r = True)
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()        
            ballFKCON = cmds.group(n = side + "_ballFK_CTRL_CON")
            ballFKOFF = cmds.group(n = side + "_ballFK_CTRL_0")
        
            #Snapping the fk controller to their respective joints
            cmds.select (thighFKJNT, thighFKOFF, r = True)
            cmds.delete (cmds.parentConstraint (weight = 1))
            cmds.select (thighFKCTRL+".cv[0:7]", r = True)
            cmds.rotate (0, 0, -90, r = True, os = True, fo = True)
            
            cmds.select (kneeFKJNT, kneeFKOFF, r = True)
            cmds.delete (cmds.parentConstraint (weight = 1))
            cmds.select (kneeFKCTRL+".cv[0:7]", r = True)
            cmds.rotate (0, 0, -90, r = True, os = True, fo = True)
            
            cmds.select (ankleFKJNT, ankleFKOFF, r = True)
            cmds.delete (cmds.parentConstraint (weight = 1))
            cmds.select (ankleFKCTRL+".cv[0:7]", r = True)
            cmds.rotate (0, 0, -90, r = True, os = True, fo = True)
            
            cmds.select (ballFKJNT, ballFKOFF, r = True)
            cmds.delete (cmds.parentConstraint (weight = 1))
            
            #Setting up the controllers in their hierachy
            cmds.parent(ballFKOFF, ankleFKCTRL, r = False)
            cmds.parent(ankleFKOFF, kneeFKCTRL, r = False)
            cmds.parent(kneeFKOFF, thighFKCTRL, r = False)
            
            cmds.group (em = True, n = side + "_legFK_CTRL_GRP")
            cmds.parent(thighFKOFF, side + "_legFK_CTRL_GRP", r = False)
            
            #Connecting the controllers to their respective joints
            cmds.parentConstraint (thighFKCTRL, thighFKJNT, weight = 1, mo = False)
            cmds.parentConstraint (kneeFKCTRL, kneeFKJNT, weight = 1, mo = False)
            cmds.parentConstraint (ankleFKCTRL, ankleFKJNT, weight = 1, mo = False)
            cmds.parentConstraint (ballFKCTRL, ballFKJNT, weight = 1, mo = False)
            
            
            #Creating a connection between the pelvis and the fk thigh using 'const_loc' method
            #Getting the position of the thigh fk joint
            thighFKPOS = cmds.xform (thighFKJNT, q = True, ws = True, t = True)
            thighLoc = cmds.spaceLocator (p = (0,0,0), n = side + "_thighFK_CTRL_CONST_LOC")
            cmds.move (thighFKPOS[0], thighFKPOS[1], thighFKPOS[2])
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            
            thighGRP = cmds.group (em = True, n = side + "_thigh_FK_CTRL_GRP")
            cmds.move (thighFKPOS[0], thighFKPOS[1], thighFKPOS[2])
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            cmds.select (side + "_legFK_CTRL_GRP", add = True)
            cmds.parent()
            cmds.parent (thighFKOFF, side + "_thigh_FK_CTRL_GRP", r = False)
            
            cmds.parentConstraint("splineBase_CTRL", thighLoc[0], mo = True, weight = 1)
            cmds.pointConstraint (thighLoc[0], thighGRP, offset = (0,0,0), weight = 1)
            
            legMISC_grp = cmds.group (em = True, n = side + "_leg_MISC_GRP")
            cmds.parent (thighLoc[0], side + "_leg_MISC_GRP", r = False)
            
                        
            #Checking if there are twist joints parented to the thigh
            thighChildJoint = cmds.listRelatives (thighJNT, c = True)
                        
            #If there are more than 1 children for the thigh joint [the one being the knee joint]
            if len(thighChildJoint) > 1:
                for jnt in thighChildJoint:
                    if 'twist' in jnt:
                        twistDuplicate = cmds.duplicate(jnt, rr = True, n = jnt + '_fk')[0]
                        cmds.parent (twistDuplicate, w = True)
                        thighTwistFKJNT.append(twistDuplicate)
                
                thighTwistFKJNT.sort()
                
                #Breaking the connection between the thighFK controller and the thighFk joint rotate X
                connectRotateX = cmds.listConnections (thighFKJNT + '.rotateX', s = 1, p = 1)[0]
                cmds.disconnectAttr(connectRotateX, thighFKJNT + '.rotateX')
                
                #Creating a multDoubleLinear node to divide the value of rotate X to the respective twist joints
                for i, jnt in enumerate(thighTwistFKJNT):
                    multDblNode = cmds.createNode('multDoubleLinear', n = jnt + '_mdl')
                    
                    input2Numo = i + 1.0
                    input2Deno = len(thighTwistFKJNT) + 1.0
                    
                    input2Value = input2Numo/input2Deno
                    
                    cmds.setAttr(multDblNode + '.input2', input2Value)
                    
                    cmds.connectAttr(thighFKCTRL + '.rotateX', multDblNode + '.input1')
                    
                    cmds.connectAttr (multDblNode + '.output', jnt + '.rotateX')  
            
            
            #Checking if there are twist joints parented to the knee
            kneeChildJoint = cmds.listRelatives (kneeJNT, c = True)
            
            #If there are more than 1 children for the knee joint [the one being the ankle jnt]
            if len(kneeChildJoint) > 1:
                for jnt in kneeChildJoint:
                    if 'twist' in jnt:
                        twistDuplicate = cmds.duplicate(jnt, rr = True, n = jnt + '_fk')[0]
                        cmds.parent (twistDuplicate, w = True)
                        kneeTwistFKJNT.append(twistDuplicate)
                
                kneeTwistFKJNT.sort()
                
                #Creating a multDoubleLinear node to divide the value of rotate X to the respective twist joints
                for i, jnt in enumerate(kneeTwistFKJNT):
                    multDblNode = cmds.createNode('multDoubleLinear', n = jnt + '_mdl')
                    
                    input2Numo = i + 1.0
                    input2Deno = len(kneeTwistFKJNT) + 1.0
                    
                    input2Value = input2Numo/input2Deno
                    
                    cmds.setAttr(multDblNode + '.input2', input2Value)
                    
                    cmds.connectAttr(ankleFKCTRL + '.rotateX', multDblNode + '.input1')
                    
                    cmds.connectAttr (multDblNode + '.output', jnt + '.rotateX') 
            
            cmds.select (thighTwistFKJNT, thighFKJNT, r = True)
            cmds.parent()
            cmds.select (kneeTwistFKJNT, kneeFKJNT, r = True)
            cmds.parent()
        
        if legikSetup:
            #IK Setup
            #Joints
            thighIKJNT = thighJNT + "_ik"
            kneeIKJNT = kneeJNT + "_ik"
            ankleIKJNT = ankleJNT + "_ik"
            ballIKJNT = ballJNT + "_ik"
            toeIKJNT = side + "_toeTip_ik"
            
            #Duplicating the bind joints to create the fk joints
            for jnts in [thighJNT, kneeJNT, ankleJNT, ballJNT]:
                duplicateJnt = cmds.duplicate (jnts, rr = True, name = jnts + '_ik')
                cmds.select (duplicateJnt, r = True)
                cmds.parent (world = True)
                
                cmds.delete (cmds.listRelatives(duplicateJnt, c = True, f = True))
            
            #Parenting the FK Joints to one another
            cmds.parent (ballIKJNT, ankleIKJNT)
            cmds.parent (ankleIKJNT, kneeIKJNT)
            cmds.parent (kneeIKJNT, thighIKJNT)
            
            #Creating a top-tip joint from the toeTipLoc postion and parenting it to the ball_ik joint
            if footRollSetup:
                if (cmds.xform (ankleIKJNT, q = True, ws = True, translation = True)[0] > 0): #Checking which side of the leg it is, through the X-position of the ankle joint
                    cmds.select("L_footRollInfo_doNotDelete", r = True)
                    cmds.scale(-1,1,1, r = True)
                
                cmds.select (cl = True)
                toeTipPos = cmds.xform (toeTipLoc, q = True, ws = True, t = True)
                cmds.joint (n = toeIKJNT, p = (toeTipPos[0], toeTipPos[1], toeTipPos[2]))
                
                cmds.parent(toeIKJNT, ballIKJNT, r = False)
            
            #Controllers
            #Pole Vector Controller
            kneeIKCTRL = mel.eval ("curve -d 1 -p 0 0 0 -p 0 0.4 -0.4 -p 0 0.2 -0.4 -p 0 0.2 -1 -p 0 -0.2 -1 -p 0 -0.2 -0.4 -p 0 -0.4 -0.4 -p 0 0 0 -p -0.4 0 -0.4 -p -0.2 0 -0.4 -p -0.2 0 -1 -p 0.2 0 -1 -p 0.2 0 -0.4 -p 0.4 0 -0.4 -p 0 0 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 ;")
            kneeIKCTRL = cmds.rename (kneeIKCTRL, side + "_kneeIK_CTRL")
            cmds.scale(controllerScale, controllerScale, controllerScale, r = True)
            cmds.rotate (0, 180, 0)
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()
            
            kneeIKCON = cmds.group (n = side + "_kneeIK_CTRL_CON")
            cmds.xform (kneeIKCON, ws = True, pivots = (0,0,0))
            kneeIKOFF = cmds.group (n = side + "_kneeIK_CTRL_0")
            cmds.xform (kneeIKOFF, ws = True, pivots = (0,0,0))
            
            #Creating Arrow connecting pole vector controller and knee joint
            annoteLoc = cmds.spaceLocator (n = kneeIKJNT + '_annotation_LOC')
            cmds.delete (cmds.parentConstraint (kneeIKJNT, annoteLoc, weight = 1))
            
            cmds.parent (annoteLoc, kneeIKJNT)
            
            annotationShape = cmds.annotate(annoteLoc)
            annote = cmds.group (annotationShape, n = kneeIKJNT + '_annotation')
            
            cmds.setAttr (annotationShape + '.overrideEnabled', 1)
            cmds.setAttr (annotationShape + '.overrideDisplayType', 1)
            
            cmds.parent (annote, kneeIKCTRL)
            cmds.ResetTransformations(annote)
            
            #Main Controller
            legIKCTRL =  mel.eval ("curve -d 1 -p -1 0 1 -p -1 0 -1 -p 1 0 -1 -p 1 0 1 -p -1 0 1 -k 0 -k 1 -k 2 -k 3 -k 4 ;")
            legIKCTRL = cmds.rename(legIKCTRL, side + "_legIK_CTRL")
            cmds.scale(controllerScale, controllerScale, controllerScale, r = True)   
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory() 
            
            legIKCON = cmds.group (n = side + "_legIK_CTRL_CON")
            legIKOFF = cmds.group (n = side + "_legIK_CTRL_0")
        
            #Snapping the ik controller to their respective joints
            cmds.select (ankleIKJNT, legIKOFF, r= True)
            cmds.delete (cmds.pointConstraint (offset = (0,0,0), weight = 1))
            
            
            #Setting up the size of the leg controller
            cmds.select(legIKCTRL + '.cv[3:4]', legIKCTRL + '.cv[0]', r = True)
            toeTipPos = cmds.xform (toeTipLoc, q = True, ws = True, t = True)
            cmds.move (toeTipPos[2], a = True, z = True)
            
            cmds.select(legIKCTRL + '.cv[1:2]', r = True)
            heelTipPos = cmds.xform (heelLoc, q = True, ws = True, t = True)
            cmds.move (heelTipPos[2], a = True, z = True)
            
            cmds.select(legIKCTRL + '.cv[0:4]', r = True)
            cmds.move (0, a = True, y = True)
            
            #Setting up the Pole-Vector position
            tempPlane = cmds.polyPlane(subdivisionsHeight = 1, subdivisionsWidth = 1)[0]
            cmds.delete(tempPlane + '.vtx[3]')

            thighPos = cmds.xform (thighIKJNT, q = True, ws = True, translation = True)
            cmds.xform (tempPlane + '.vtx[0]', ws = True, translation = thighPos)

            kneePos = cmds.xform (kneeIKJNT, q = True, ws = True, translation = True)
            cmds.xform (tempPlane + '.vtx[1]', ws = True, translation = kneePos)

            anklePos = cmds.xform (ankleIKJNT, q = True, ws = True, translation = True)
            cmds.xform (tempPlane + '.vtx[2]', ws = True, translation = anklePos)

            cmds.moveVertexAlongDirection (tempPlane + '.vtx[1]', v = 5 * controllerScale) #Moving the knee vertex of the plane along the V-normal axis

            poleVectorPos = cmds.xform (tempPlane + '.vtx[1]', q = True, ws = True, translation = True)
            cmds.xform (kneeIKOFF, ws = True, translation = poleVectorPos)

            cmds.delete(tempPlane)
            
            #Setting up the controllers in their hierachy
            cmds.group (em = True, n = side + "_legIK_CTRL_GRP")
            cmds.parent(legIKOFF, kneeIKOFF, side + "_legIK_CTRL_GRP", r = False)
            
            #Creating the connection from the controller to the joints
            #Creating the IK Handles
            LegIKHandle = cmds.ikHandle (n = ankleIKJNT + "_IKH", shf = False, s = "sticky", fs = True, sj = thighIKJNT, ee = ankleIKJNT)
            cmds.rename(LegIKHandle[1], ankleIKJNT + "_EFF")
            
            BallIKHandle = cmds.ikHandle (n = ballIKJNT + "_IKH", shf = False, s = "sticky", fs = True, sol = "ikSCsolver", sj = ankleIKJNT, ee = ballIKJNT)
            cmds.rename(BallIKHandle[1], ballIKJNT + "_EFF")
            
            ToeIKHandle = cmds.ikHandle (n = toeIKJNT + "_IKH", shf = False, s = "sticky", fs = True, sol = "ikSCsolver", sj = ballIKJNT, ee = toeIKJNT)
            cmds.rename(ToeIKHandle[1], toeIKJNT + "_EFF")
            
            #Parenting the IKH to the main controller and creating a pole vector constraint
            cmds.select(LegIKHandle[0], BallIKHandle[0], ToeIKHandle[0], legIKCTRL, r = True)
            cmds.parent()
            cmds.select(kneeIKCTRL, LegIKHandle[0], r = True)
            poleVector = cmds.poleVectorConstraint (weight = 1)
            
            #Hide the IK Handle
            cmds.setAttr(LegIKHandle[0] + ".v", 0)
            cmds.setAttr(BallIKHandle[0] + ".v", 0)
            cmds.setAttr(ToeIKHandle[0] + ".v", 0)
            
            cmds.select(legIKCTRL, ankleIKJNT, r = True)
            cmds.orientConstraint (mo = True, weight = 1)
            
            #Adding a follow attribute to the pole vector controller
            cmds.select(kneeIKCTRL, r = True)
            cmds.addAttr (ln = "follow", at = "enum", en = "<none>:Ankle:", k = True)
            
            cmds.select(legIKCTRL, kneeIKOFF, r = True)
            secondGrpCONST = cmds.parentConstraint (maintainOffset = True, weight = 1)
            
            #Creating connection for the above created attributes using SDK
            cmds.setDrivenKeyframe (secondGrpCONST[0] + "." + legIKCTRL + "W0", dv = 0, v = 0, cd = kneeIKCTRL + '.follow')
            cmds.setDrivenKeyframe (secondGrpCONST[0] + "." + legIKCTRL + "W0", dv = 1, v = 1, cd = kneeIKCTRL + '.follow')
            
            cmds.select (legIKCTRL, r = True)
            cmds.addAttr (ln = "follow", at = "enum", en = "<none>:Hip:", k = True)
            
            #Adding attributes to the legIKCtrl for foot roll
            if footRollSetup:
                cmds.select (legIKCTRL, r = True)
                cmds.addAttr(ln = "footRoll", at = "float", dv = 0, k = True)
                cmds.addAttr(ln = "ankleRoll", at = "float", dv = 0, k = True)
                cmds.addAttr(ln = "toeRoll", at = "float", dv = 0, k = True)
                cmds.addAttr(ln = "heelPivot", at = "float", dv = 0, k = True)
                cmds.addAttr(ln = "ballPivot", at = "float", dv = 0, k = True)
                cmds.addAttr(ln = "toePivot", at = "float", dv = 0, k = True)
                cmds.addAttr(ln = "toeWiggle", at = "float", dv = 0, k = True)
                
                #Getting the position of the foot locators
                heelLOCPos = cmds.xform (heelLoc, q = True, ws = True, t = True)
                ankleInLOCPos = cmds.xform (ankleRollInLoc, q = True, ws = True, t = True)
                ankleOutLOCPos = cmds.xform (ankleRollOutLoc, q = True, ws = True, t = True)
                            
                #Creating foot roll locators and placing them in the correct postion
                #Heel Loc
                heel_loc = cmds.spaceLocator (p = (0,0,0), n = side + "_heel_LOC")
                cmds.move (heelLOCPos[0], heelLOCPos[1], heelLOCPos[2], r = True)
                #Ball Pivot Loc
                ballPivot_loc = cmds.spaceLocator (p = (0,0,0), n = side + "_ballPivot_LOC")
                cmds.select (ballIKJNT, ballPivot_loc[0], r = True)
                cmds.delete(cmds.pointConstraint(offset = (0,0,0), weight = 1))
                cmds.setAttr (ballPivot_loc[0]+ ".ty", 0)
                #Toe Pivot Loc
                toePivot_loc = cmds.spaceLocator (p = (0,0,0), n = side + "_toePivot_LOC")
                cmds.select (toeIKJNT, toePivot_loc[0], r = True)
                cmds.delete(cmds.pointConstraint(offset = (0,0,0), weight = 1))
                cmds.setAttr(toePivot_loc[0]+ ".ty", 0)
                #Ankle Roll In Loc
                ankleRollIn_loc = cmds.spaceLocator (p = (0,0,0), n = side + "_ankleRollIn_LOC")
                cmds.move (ankleInLOCPos[0], ankleInLOCPos[1], ankleInLOCPos[2], r = True)
                #Ankle Roll Out Loc
                ankleRollOut_loc = cmds.spaceLocator (p = (0,0,0), n = side + "_ankleRollOut_LOC")
                cmds.move (ankleOutLOCPos[0], ankleOutLOCPos[1], ankleOutLOCPos[2], r = True)
                #Toe Wiggle Loc
                toeWiggle_loc = cmds.spaceLocator (p = (0,0,0), n = side + "_toeWiggle_LOC")
                cmds.select (ballIKJNT, toeWiggle_loc[0], r = True)
                cmds.delete(cmds.pointConstraint(offset = (0,0,0), weight = 1))
                #Roll Loc
                roll_loc = cmds.spaceLocator (p = (0,0,0), n = side + "_roll_LOC")
                cmds.select (ballIKJNT, roll_loc[0], r = True)
                cmds.delete(cmds.pointConstraint(offset = (0,0,0), weight = 1))
                
                #Arranging the locators in the right hierarchy
                cmds.parent(roll_loc[0], toeWiggle_loc[0], ankleRollIn_loc[0], r = False)
                cmds.parent (ankleRollIn_loc[0], ankleRollOut_loc[0], r = False)
                cmds.parent (ankleRollOut_loc[0], toePivot_loc[0], r = False)
                cmds.parent (toePivot_loc[0], ballPivot_loc[0], r = False)
                cmds.parent (ballPivot_loc[0], heel_loc[0], r = False)
                cmds.select (heel_loc[0], r = True)   
                cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
                cmds.DeleteHistory() 
                
                cmds.parent (heel_loc[0], legIKCTRL, r = False)
                
                #Re-parenting the leg IKH to their respective locators
                cmds.parent (ToeIKHandle[0], toeWiggle_loc[0], r = False)
                cmds.parent (BallIKHandle[0], ankleRollIn_loc[0], r = False)
                cmds.parent (LegIKHandle[0], roll_loc[0], r = False)
                                
                #Creating Set Driven Keys for the foot rolls
                if (anklePos[0] > 0):
                    #Toe Wiggle
                    cmds.setDrivenKeyframe (toeWiggle_loc[0] + ".rx", dv = 0, v = 0, cd = legIKCTRL + '.toeWiggle')
                    cmds.setDrivenKeyframe (toeWiggle_loc[0] + ".rx", dv = 10, v = 45, cd = legIKCTRL + '.toeWiggle')
                    cmds.setDrivenKeyframe (toeWiggle_loc[0] + ".rx", dv = -10, v = -45, cd = legIKCTRL + '.toeWiggle')
                    #Toe Pivot
                    cmds.setDrivenKeyframe (toePivot_loc[0] + ".ry", dv = 0, v = 0, cd = legIKCTRL + '.toePivot')
                    cmds.setDrivenKeyframe (toePivot_loc[0] + ".ry", dv = 10, v = -45, cd = legIKCTRL + '.toePivot')
                    cmds.setDrivenKeyframe (toePivot_loc[0] + ".ry", dv = -10, v = 45, cd = legIKCTRL + '.toePivot')
                    #Ball Pivot
                    cmds.setDrivenKeyframe (ballPivot_loc[0] + ".ry", dv = 0, v = 0, cd = legIKCTRL + '.ballPivot')
                    cmds.setDrivenKeyframe (ballPivot_loc[0] + ".ry", dv = 10, v = -45, cd = legIKCTRL + '.ballPivot')
                    cmds.setDrivenKeyframe (ballPivot_loc[0] + ".ry", dv = -10, v = 45, cd = legIKCTRL + '.ballPivot')
                    #Heel Pivot
                    cmds.setDrivenKeyframe (heel_loc[0] + ".ry", dv = 0, v = 0, cd = legIKCTRL + '.heelPivot')
                    cmds.setDrivenKeyframe (heel_loc[0] + ".ry", dv = 10, v = -45, cd = legIKCTRL + '.heelPivot')
                    cmds.setDrivenKeyframe (heel_loc[0] + ".ry", dv = -10, v = 45, cd = legIKCTRL + '.heelPivot')
                    #Toe Roll
                    cmds.setDrivenKeyframe (toePivot_loc[0] + ".rx", dv = 0, v = 0, cd = legIKCTRL + '.toeRoll')
                    cmds.setDrivenKeyframe (toePivot_loc[0] + ".rx", dv = 10, v = 45, cd = legIKCTRL + '.toeRoll')
                    #cmds.setDrivenKeyframe (toePivot_loc[0] + ".rx", dv = -10, v = -45, cd = legIKCTRL + '.toeRoll')
                    #Ankle Roll
                    cmds.setDrivenKeyframe (ankleRollOut_loc[0] + ".rz", dv = 0, v = 0, cd = legIKCTRL + '.ankleRoll')
                    cmds.setDrivenKeyframe (ankleRollOut_loc[0] + ".rz", dv = 10, v = -45, cd = legIKCTRL + '.ankleRoll')
                    cmds.setDrivenKeyframe (ankleRollIn_loc[0] + ".rz", dv = 0, v = 0, cd = legIKCTRL + '.ankleRoll')
                    cmds.setDrivenKeyframe (ankleRollIn_loc[0] + ".rz", dv = -10, v = 45, cd = legIKCTRL + '.ankleRoll')
                    #Foot Roll
                    cmds.setDrivenKeyframe (roll_loc[0] + ".rx", dv = 0, v = 0, cd = legIKCTRL + '.footRoll')
                    cmds.setDrivenKeyframe (roll_loc[0] + ".rx", dv = 10, v = 45, cd = legIKCTRL + '.footRoll')
                    cmds.setDrivenKeyframe (heel_loc[0] + ".rx", dv = 0, v = 0, cd = legIKCTRL + '.footRoll')
                    cmds.setDrivenKeyframe (heel_loc[0] + ".rx", dv = -10, v = -45, cd = legIKCTRL + '.footRoll')
                
                elif (anklePos[0] < 0):
                    #Toe Wiggle
                    cmds.setDrivenKeyframe (toeWiggle_loc[0] + ".rx", dv = 0, v = 0, cd = legIKCTRL + '.toeWiggle')
                    cmds.setDrivenKeyframe (toeWiggle_loc[0] + ".rx", dv = 10, v = 45, cd = legIKCTRL + '.toeWiggle')
                    cmds.setDrivenKeyframe (toeWiggle_loc[0] + ".rx", dv = -10, v = -45, cd = legIKCTRL + '.toeWiggle')
                    #Toe Pivot
                    cmds.setDrivenKeyframe (toePivot_loc[0] + ".ry", dv = 0, v = 0, cd = legIKCTRL + '.toePivot')
                    cmds.setDrivenKeyframe (toePivot_loc[0] + ".ry", dv = 10, v = 45, cd = legIKCTRL + '.toePivot')
                    cmds.setDrivenKeyframe (toePivot_loc[0] + ".ry", dv = -10, v = -45, cd = legIKCTRL + '.toePivot')
                    #Ball Pivot
                    cmds.setDrivenKeyframe (ballPivot_loc[0] + ".ry", dv = 0, v = 0, cd = legIKCTRL + '.ballPivot')
                    cmds.setDrivenKeyframe (ballPivot_loc[0] + ".ry", dv = 10, v = 45, cd = legIKCTRL + '.ballPivot')
                    cmds.setDrivenKeyframe (ballPivot_loc[0] + ".ry", dv = -10, v = -45, cd = legIKCTRL + '.ballPivot')
                    #Heel Pivot
                    cmds.setDrivenKeyframe (heel_loc[0] + ".ry", dv = 0, v = 0, cd = legIKCTRL + '.heelPivot')
                    cmds.setDrivenKeyframe (heel_loc[0] + ".ry", dv = 10, v = 45, cd = legIKCTRL + '.heelPivot')
                    cmds.setDrivenKeyframe (heel_loc[0] + ".ry", dv = -10, v = -45, cd = legIKCTRL + '.heelPivot')
                    #Toe Roll
                    cmds.setDrivenKeyframe (toePivot_loc[0] + ".rx", dv = 0, v = 0, cd = legIKCTRL + '.toeRoll')
                    cmds.setDrivenKeyframe (toePivot_loc[0] + ".rx", dv = 10, v = 45, cd = legIKCTRL + '.toeRoll')
                    #cmds.setDrivenKeyframe (toePivot_loc[0] + ".rx", dv = -10, v = -45, cd = legIKCTRL + '.toeRoll')
                    #Ankle Roll
                    cmds.setDrivenKeyframe (ankleRollOut_loc[0] + ".rz", dv = 0, v = 0, cd = legIKCTRL + '.ankleRoll')
                    cmds.setDrivenKeyframe (ankleRollOut_loc[0] + ".rz", dv = 10, v = 45, cd = legIKCTRL + '.ankleRoll')
                    cmds.setDrivenKeyframe (ankleRollIn_loc[0] + ".rz", dv = 0, v = 0, cd = legIKCTRL + '.ankleRoll')
                    cmds.setDrivenKeyframe (ankleRollIn_loc[0] + ".rz", dv = -10, v = -45, cd = legIKCTRL + '.ankleRoll')
                    #Foot Roll
                    cmds.setDrivenKeyframe (roll_loc[0] + ".rx", dv = 0, v = 0, cd = legIKCTRL + '.footRoll')
                    cmds.setDrivenKeyframe (roll_loc[0] + ".rx", dv = 10, v = 45, cd = legIKCTRL + '.footRoll')
                    cmds.setDrivenKeyframe (heel_loc[0] + ".rx", dv = 0, v = 0, cd = legIKCTRL + '.footRoll')
                    cmds.setDrivenKeyframe (heel_loc[0] + ".rx", dv = -10, v = -45, cd = legIKCTRL + '.footRoll')
                
                #Enabling cycle with offset for the set driven keys on the foot locators
                #Changing every key to linear
                cmds.select(heel_loc[0], ballPivot_loc[0], toePivot_loc[0], ankleRollIn_loc[0], ankleRollOut_loc[0], roll_loc[0], toeWiggle_loc[0], r = True)
                cmds.selectKey (clear = True)
                cmds.selectKey (heel_loc[0] + "_rotateX", add = True, k = True, f = (-10,0))
                cmds.selectKey (toePivot_loc[0] + "_rotateX", add = True, k = True, f = (0,10))
                cmds.selectKey (ankleRollOut_loc[0] + "_rotateZ", add = True, k = True, f = (0,10))
                cmds.selectKey (ankleRollIn_loc[0] + "_rotateZ", add = True, k = True, f = (-10,0))
                cmds.selectKey (roll_loc[0] + "_rotateX", add = True, k = True, f = (0,10))
                cmds.selectKey ((heel_loc[0] + "_rotateY"), (ballPivot_loc[0] + "_rotateY"), (toePivot_loc[0] + "_rotateY"), (toeWiggle_loc[0] + "_rotateX"), add = True, k = True)
                cmds.keyTangent (itt = "linear", ott = "linear")
                
                #Enabling post and pre infinity to the keys
                cmds.selectKey (clear = True)
                cmds.selectKey ((heel_loc[0] + "_rotateY"), (ballPivot_loc[0] + "_rotateY"), (toePivot_loc[0] + "_rotateY"), (toeWiggle_loc[0] + "_rotateX"), add = True, k = True)
                cmds.setInfinity (pri = "cycleRelative")
                cmds.setInfinity (poi = "cycleRelative")
                
                cmds.selectKey (clear = True)
                cmds.selectKey (heel_loc[0] + "_rotateX", add = True, k = True, f = (-10,0))
                cmds.selectKey (ankleRollIn_loc[0] + "_rotateZ", add = True, k = True, f = (-10,0))
                cmds.setInfinity (pri = "cycleRelative")
                
                cmds.selectKey (clear = True)
                cmds.selectKey (ankleRollOut_loc[0] + "_rotateZ", add = True, k = True, f = (0,10))
                cmds.selectKey (roll_loc[0] + "_rotateX", add = True, k = True, f = (0,10))
                cmds.selectKey (toePivot_loc[0] + "_rotateX", add = True, k = True, f = (0,10))
                cmds.setInfinity (poi = "cycleRelative")
                
                #Hide the locators
                cmds.setAttr (heel_loc[0] + ".v", 0)
                
                #Connecting the leg IK joints to the spineBase controller
                cmds.select ("splineBase_CTRL", thighIKJNT, r = True)
                cmds.parentConstraint (mo = True, weight = 1)
                
            #Checking if there are twist joints parented to the thigh
            thighChildJoint = cmds.listRelatives (thighJNT, c = True)
                        
            #If there are more than 1 children for the thigh joint [the one being the knee joint]
            if len(thighChildJoint) > 1:
                for jnt in thighChildJoint:
                    if 'twist' in jnt:
                        twistDuplicate = cmds.duplicate(jnt, rr = True, n = jnt + '_ik')[0]
                        cmds.parent (twistDuplicate, w = True)
                        thighTwistIKJNT.append(twistDuplicate)
                
                thighTwistIKJNT.sort()
            
            #Checking if there are twist joints parented to the knee
            kneeChildJoint = cmds.listRelatives (kneeJNT, c = True)
            
            #If there are more than 1 children for the knee joint [the one being the ankle jnt]
            if len(kneeChildJoint) > 1:
                for jnt in kneeChildJoint:
                    if 'twist' in jnt:
                        twistDuplicate = cmds.duplicate(jnt, rr = True, n = jnt + '_ik')[0]
                        cmds.parent (twistDuplicate, w = True)
                        kneeTwistIKJNT.append(twistDuplicate)
                
                kneeTwistIKJNT.sort()
                
                #Creating a multDoubleLinear node to divide the value of rotate X to the respective twist joints
                for i, jnt in enumerate(kneeTwistIKJNT):
                    multDblNode = cmds.createNode('multDoubleLinear', n = jnt + '_mdl')
                    
                    input2Numo = i + 1.0
                    input2Deno = len(kneeTwistIKJNT) + 1.0
                    
                    input2Value = input2Numo/input2Deno
                    
                    cmds.setAttr(multDblNode + '.input2', input2Value)
                    
                    cmds.connectAttr(legIKCTRL + '.rotateY', multDblNode + '.input1')
                    
                    cmds.connectAttr (multDblNode + '.output', jnt + '.rotateX')  
            
            cmds.select (thighTwistIKJNT, thighIKJNT, r = True)
            cmds.parent()
            cmds.select (kneeTwistIKJNT, kneeIKJNT, r = True)
            cmds.parent()
            
        if (legfkSetup and legikSetup):
            
            # IK-FK Switch
            ikFkControl = mel.eval ("curve -d 1 -p -1.541097 0 -0.407608 -p -1.997943 0 -0.287409 -p -1.996633 0 0.292773 -p -1.540642 0 0.404437 -p -1.376247 0 0.800967 -p -1.614601 0 1.209387 -p -1.206218 0 1.618289 -p -0.802518 0 1.37467 -p -0.406558 0 1.538403 -p -0.285068 0 1.998563 -p 0.293543 0 1.996772 -p 0.405503 0 1.538183 -p 0.800499 0 1.376064 -p 1.209852 0 1.613362 -p 1.618868 0 1.206081 -p 1.37717 0 0.803675 -p 1.540102 0 0.406725 -p 1.997785 0 0.285372 -p 1.997147 0 -0.294228 -p 1.540467 0 -0.405926 -p 1.377365 0 -0.800905 -p 1.615038 0 -1.210376 -p 1.206209 0 -1.619887 -p 0.802833 0 -1.375844 -p 0.40785 0 -1.540751 -p 0.28608 0 -1.998594 -p -0.29285 0 -1.997769 -p -0.405278 0 -1.539256 -p -0.801016 0 -1.37748 -p -1.208227 0 -1.614979 -p -1.619464 0 -1.206488 -p -1.37182 0 -0.798064 -p -1.541097 0 -0.407608 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 -k 17 -k 18 -k 19 -k 20 -k 21 -k 22 -k 23 -k 24 -k 25 -k 26 -k 27 -k 28 -k 29 -k 30 -k 31 -k 32;")
            delController = mel.eval ("circle -c 0 0 0 -r 0.8 -nr 0 1 0")
            delControllerShapes = cmds.listRelatives(delController, shapes = True)
            cmds.select (delControllerShapes, r = True)
            cmds.select (ikFkControl, add = True)
            cmds.parent (r = True, s = True)
            cmds.delete (delController)
            ikFkControl = cmds.rename (ikFkControl, side + '_legSwitch_CTRL')
            
            ikFkControl = side + '_legSwitch_CTRL'
            cmds.select (ikFkControl)
            cmds.rotate (90, 0, 0)
            cmds.scale (controllerScale/4, controllerScale/4, controllerScale/4)
            cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
            cmds.DeleteHistory()

            cmds.group (n = side + '_legSwitch_CTRL_GRP', empty = True)

            cmds.parent (ikFkControl, side + '_legSwitch_CTRL_GRP')

            cmds.select (ankleJNT, side + '_legSwitch_CTRL_GRP', r = True)
            cmds.pointConstraint(weight = 1)
            cmds.orientConstraint(weight = 1, maintainOffset = 1)

            cmds.select (ikFkControl + '.cv[0:32]', r = True)
            checkSide = cmds.xform(ikFkControl, q = True, ws = True, translation = True)
            if (checkSide[0] > 0):
                cmds.move ((3 * controllerScale), 0, 0, os = True, wd = True, r = True)
            else:
                cmds.move ((-3 * controllerScale), 0, 0, os = True, wd = True, r = True)
            cmds.select (cl = True)

            cmds.select (ikFkControl, r = True)
            cmds.addAttr (ln = "FKIK", at = "float", min = 0, max = 1, dv = 0, k = True)
            
            #Getting the twist bind joints and creating alist
            #thigh
            thighTwistBindJntsTemp = cmds.listRelatives (thighJNT, c = True)
            thighTwistBindJnts = []
            
            #If there are more than 1 children for the thigh joint [the one being the knee jnt]
            if len(thighTwistBindJntsTemp) > 1:
                for jnt in thighTwistBindJntsTemp:
                    if 'twist' in jnt:
                        thighTwistBindJnts.append(jnt)
                    
                thighTwistBindJnts.sort()
            
            #knee
            kneeTwistBindJntsTemp = cmds.listRelatives (kneeJNT, c = True)
            kneeTwistBindJnts = []
            
            #If there are more than 1 children for the knee joint [the one being the ankle jnt]
            if len(kneeTwistBindJntsTemp) > 1:
                for jnt in kneeTwistBindJntsTemp:
                    if 'twist' in jnt:
                        kneeTwistBindJnts.append(jnt)
                    
                kneeTwistBindJnts.sort()      
            
                        
            bindJnts = [thighJNT, kneeJNT, ankleJNT, ballJNT] + thighTwistBindJnts + kneeTwistBindJnts
            fkJnts = [thighFKJNT, kneeFKJNT, ankleFKJNT, ballFKJNT] + thighTwistFKJNT + kneeTwistFKJNT
            ikJnts = [thighIKJNT, kneeIKJNT, ankleIKJNT, ballIKJNT] + thighTwistIKJNT + kneeTwistIKJNT
            
            #Connecting the FK-IK joints with the bind joints using blendColors node
            for bind, fk, ik in zip (bindJnts, fkJnts, ikJnts):
                for i in ['translate', 'rotate', 'scale']:
                    blendColor = cmds.createNode('blendColors', n = bind.replace('JNT', 'blendColors_{}'.format(i))) #Creating a blendnode to blend the bind joint between fk and ik joints
                    cmds.connectAttr('{0}.{1}'.format(fk, i), blendColor + '.color2')
                    cmds.connectAttr('{0}.{1}'.format(ik, i), blendColor + '.color1')
                    
                    #Only when dealing with the thigh joint, since the local values for the thigh bind joint and fk & ik joints are different, due to the bind thigh joint being parented to the clavicle joint
                    #That is why we need to convert the world translate values to local translate values for the thigh bind joint
                    if bind == bindJnts[0] and i == 'translate':
                        pointMatMult = cmds.createNode('pointMatrixMult', n = bind.replace('JNT', 'pointMatMult_{}'.format(i))) #Using 'pointMatrixMult' to get the local translate, rotate and scale values for the thigh bind joint
                        cmds.connectAttr(pelvisJNT + '.worldInverseMatrix', pointMatMult + '.inMatrix')
                        cmds.connectAttr(blendColor + '.output', pointMatMult + '.inPoint')
                        cmds.connectAttr(pointMatMult + '.output', '{0}.{1}'.format(bind, i))
                    else:
                        cmds.connectAttr(blendColor + '.output', '{0}.{1}'.format(bind, i))
                    
                    cmds.connectAttr (ikFkControl + '.FKIK', blendColor + '.blender')            
                
            #Locking the unwanted attributes for the switch controller
            cmds.setAttr(ikFkControl + ".tx", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".ty", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".tz", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".rx", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".ry", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".rz", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".sx", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".sy", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".sz", lock = True, keyable = False, channelBox = False)
            cmds.setAttr(ikFkControl + ".v", lock = True, keyable = False, channelBox = False)
            
            cmds.setAttr(ikFkControl + ".FKIK", 1)
            
            #Setting up the controllers in their hierachy
            cmds.group (em = True, n = side + "_legMain_CTRL_GRP")
            cmds.parent (side + "_legSwitch_CTRL_GRP", side + "_legMain_CTRL_GRP", r = False)
            
            legCTRL_grp = cmds.group (em = True, n = side + "_leg_CTRL_GRP")
            cmds.parent (side + "_legFK_CTRL_GRP", side + "_legIK_CTRL_GRP", side + "_legMain_CTRL_GRP", side + "_leg_CTRL_GRP", r = False)
            
            legJNT_grp = cmds.group(em = True, n = side + "_leg_JNT_GRP")
            cmds.parent (thighFKJNT, thighIKJNT, side + "_leg_JNT_GRP", r = False)
            
            #Connecting the visibility of the controllers to the switch using nodes
            cmds.connectAttr (ikFkControl + '.FKIK', side + "_legIK_CTRL_GRP.visibility")
            reverseNode = cmds.createNode('reverse', n = side + '_legControlVis_rev')
            cmds.connectAttr(ikFkControl + '.FKIK', reverseNode +'.inputX')
            cmds.connectAttr(reverseNode + '.outputX', side + "_legFK_CTRL_GRP.visibility")
                
            if (cmds.xform (thighJNT, q = True, ws = True, translation = True)[0] > 0): #Checking the side of the controllers usinmg the X position of the shoulder joint 
                controllerColorAssign(255, 0, 0, thighFKCTRL, kneeFKCTRL, ankleFKCTRL, ballFKCTRL, legIKCTRL, kneeIKCTRL, ikFkControl)
            else:                    
                controllerColorAssign(0, 0, 255, thighFKCTRL, kneeFKCTRL, ankleFKCTRL, ballFKCTRL, legIKCTRL, kneeIKCTRL, ikFkControl)
            
        elif (legfkSetup and not legikSetup):
            legCTRL_grp = cmds.group (em = True, n = side + "_leg_CTRL_GRP")
            cmds.parent (side + "_legFK_CTRL_GRP", side + "_leg_CTRL_GRP", r = False)
            
            legJNT_grp = cmds.group(em = True, n = side + "_leg_JNT_GRP")
            cmds.parent (thighFKJNT, side + "_leg_JNT_GRP", r = False)
                
            if (cmds.xform (thighJNT, q = True, ws = True, translation = True)[0] > 0): #Checking the side of the controllers usinmg the X position of the shoulder joint 
                controllerColorAssign(255, 0, 0, thighFKCTRL, kneeFKCTRL, ankleFKCTRL, ballFKCTRL)
            else:                    
                controllerColorAssign(0, 0, 255, thighFKCTRL, kneeFKCTRL, ankleFKCTRL, ballFKCTRL)
            
        elif (legikSetup and not legfkSetup):
            legCTRL_grp = cmds.group (em = True, n = side + "_leg_CTRL_GRP")
            cmds.parent (side + "_legIK_CTRL_GRP", side + "_leg_CTRL_GRP", r = False)
            
            legJNT_grp = cmds.group(em = True, n = side + "_leg_JNT_GRP")
            cmds.parent (thighIKJNT, side + "_leg_JNT_GRP", r = False)
                
            if (cmds.xform (thighJNT, q = True, ws = True, translation = True)[0] > 0): #Checking the side of the controllers usinmg the X position of the shoulder joint 
                controllerColorAssign(255, 0, 0, legIKCTRL, kneeIKCTRL)
            else:                    
                controllerColorAssign(0, 0, 255, legIKCTRL, kneeIKCTRL)
            
        else:
            #Give out an error message
            om.MGlobal.displayError("SELECT EITHER FK,IK OR BOTH FOR THE leg SETUP")
            return

def finalConnections (armFKSetup, legFKSetup, controllerScale):         
    with UndoContext():  
        cmds.delete ("L_footRollInfo_doNotDelete")
        
        #Grouping everything together
        #Arm Group
        cmds.group (em = True, n = "arm_JNT_GRP")
        cmds.parent ("L_arm_JNT_GRP", "R_arm_JNT_GRP", "arm_JNT_GRP", r = False)
        
        cmds.group (em = True, n = "clavicle_JNT_GRP")
        cmds.parent ("L_clavicle_JNT_GRP", "R_clavicle_JNT_GRP", "clavicle_JNT_GRP", r = False)
        
        cmds.group (em = True, n = "arm_CTRL_GRP")
        cmds.parent ("L_arm_CTRL_GRP", "R_arm_CTRL_GRP", "arm_CTRL_GRP", r = False)
        
        cmds.group (em = True, n = "clavicle_CTRL_GRP")
        cmds.parent ("L_clavicle_CTRL_GRP", "R_clavicle_CTRL_GRP", "clavicle_CTRL_GRP", r = False)
        
        #Leg Group
        cmds.group (em = True, n = "leg_JNT_GRP")
        cmds.parent ("L_leg_JNT_GRP", "R_leg_JNT_GRP", "leg_JNT_GRP", r = False)
        
        cmds.group (em = True, n = "leg_CTRL_GRP")
        cmds.parent ("L_leg_CTRL_GRP", "R_leg_CTRL_GRP", "leg_CTRL_GRP", r = False)
        
        #MISC Group
        if (armFKSetup):
            cmds.group (em = True, n = "arm_MISC_GRP")
            cmds.parent ("L_arm_MISC_GRP", "R_arm_MISC_GRP", "arm_MISC_GRP", r = False)   
        
        if (legFKSetup):
            cmds.group (em = True, n = "leg_MISC_GRP")
            cmds.parent ("L_leg_MISC_GRP", "R_leg_MISC_GRP", "leg_MISC_GRP", r = False)    
        
        if (armFKSetup and legFKSetup):
            cmds.group (em = True, n = "MISC_GRP")
            cmds.parent ("spine_MISC_GRP", "arm_MISC_GRP", "leg_MISC_GRP", "MISC_GRP", r = False)
        elif (armFKSetup and not legFKSetup):
            cmds.group (em = True, n = "MISC_GRP")
            cmds.parent ("spine_MISC_GRP", "arm_MISC_GRP", "MISC_GRP", r = False)
        elif (legFKSetup and not armFKSetup):
            cmds.group (em = True, n = "MISC_GRP")
            cmds.parent ("spine_MISC_GRP", "leg_MISC_GRP", "MISC_GRP", r = False)
        else:
            cmds.group (em = True, n = "MISC_GRP")
            cmds.parent ("spine_MISC_GRP", "MISC_GRP", r = False)
        
        #JNT Group
        cmds.group (em = True, n = "JNT_GRP")
        cmds.parent ("spine_JNT_GRP", "neck_JNT_GRP", "clavicle_JNT_GRP", "arm_JNT_GRP", "leg_JNT_GRP", "JNT_GRP", r = False)
        
        #CTRL Group
        cmds.group (em = True, n = "CTRL_GRP")
        cmds.parent ("spine_CTRL_GRP", "neck_CTRL_GRP", "arm_CTRL_GRP", "leg_CTRL_GRP", "clavicle_CTRL_GRP", "CTRL_GRP", r = False)
        
        #Connecting the clavicles to the chest controller
        cmds.select ("splineTip_CTRL","clavicle_CTRL_GRP", r = True)
        cmds.parentConstraint (mo = True, weight = 1)
        
        #Create a main controller
        mainCTRL = mel.eval ("curve -d 1 -p 0 0 -0.9857426965 -p -0.2950522357 0 -0.543164343 -p -0.1475261178 0 -0.543164343 -p -0.1475261178 0 -0.1475261178 -p -0.543164343 0 -0.1475261178 -p -0.543164343 0 -0.2950522357 -p -0.9857426965 0 0 -p -0.543164343 0 0.2950522357 -p -0.543164343 0 0.1475261178 -p -0.1475261178 0 0.1475261178 -p -0.1475261178 0 0.543164343 -p -0.2950522357 0 0.543164343 -p 0 0 0.9857426965 -p 0.2950522357 0 0.543164343 -p 0.1475261178 0 0.543164343 -p 0.1475261178 0 0.1475261178 -p 0.543164343 0 0.1475261178 -p 0.543164343 0 0.2950522357 -p 0.9857426965 0 0 -p 0.543164343 0 -0.2950522357 -p 0.543164343 0 -0.1475261178 -p 0.1475261178 0 -0.1475261178 -p 0.1475261178 0 -0.543164343 -p 0.2950522357 0 -0.543164343 -p 0 0 -0.98574269651;")
        mainCTRL = cmds.rename (mainCTRL, "MAIN_CTRL")
        cmds.scale(10 * controllerScale, 10 * controllerScale, 10 * controllerScale, r = True)
        cmds.makeIdentity (apply = True, r = 1, t = 1, s = 1, n = 0)
        cmds.DeleteHistory()
        
        controllerColorAssign (255, 255, 255, mainCTRL)
        
        cmds.select(mainCTRL, r = True)
        cmds.connectAttr (mainCTRL + '.sy' , mainCTRL + '.sx', f = True)
        cmds.connectAttr (mainCTRL + '.sy' , mainCTRL + '.sz', f = True)
        cmds.setAttr (mainCTRL + '.sx', keyable = False, channelBox = False)
        cmds.setAttr (mainCTRL + '.sz', keyable = False, channelBox = False)
        
        cmds.select (all = True)
        cmds.select (mainCTRL, d = True)
        
        cmds.select (mainCTRL, add = True)
        cmds.parent()
        
        #Checking off inherit transform from all the geo
        
        cmds.SelectAllPolygonGeometry()
        geoMeshes = cmds.ls(selection = True)
        
        for mesh in geoMeshes:
            cmds.setAttr (mesh + ".inheritsTransform", 0)
            
        #Turning off the visibility for the JNT and the MISC group
        cmds.setAttr ("MISC_GRP.v", 0)
        cmds.setAttr ("JNT_GRP.v", 0)
        
        cmds.select(cl = True)
        
        
def controllerColorAssign (r, g, b, *args):
    #Adding in Color to the New Controllers
    cmds.select (args, r = True)
    shapesSelect = cmds.ls (selection = 1, shapes = True, dag = True) #Selecting all the shapes from the newly created controller
    
    #Going through all the shapes and changing the RGB color through the 'Drawing Overrides'
    for shape in shapesSelect:
        cmds.setAttr(shape + ".overrideEnabled", 1)
        cmds.setAttr(shape + ".overrideRGBColors", 1)
        cmds.setAttr(shape + ".overrideColorRGB", r, g, b)
    
'''
####################################################################################################
BIPED CONTROL RIG SETUP
END
####################################################################################################
'''
 
'''
####################################################################################################
RANGE OF MOTION SETUP
START
####################################################################################################
'''   
def createROM (rotXP, rotYP, rotZP, rotXN, rotYN, rotZN, rotAngle, keyFramePadding, keyFrameStart):
    selected = cmds.ls (selection = True)
    frameNumber = keyFrameStart

    for selection in selected:
        cmds.select ( selection, r = 1)
        cmds.setKeyframe (t = frameNumber)
        
        if rotYP:
            frameNumber = frameNumber + keyFramePadding
            cmds.rotate (0, rotAngle, 0, a= 1)
            cmds.setKeyframe (t = frameNumber)
            
            frameNumber = frameNumber + keyFramePadding
            cmds.rotate (0, 0, 0, a= 1)
            cmds.setKeyframe (t = frameNumber)
        
        if rotYN:
            frameNumber = frameNumber + keyFramePadding    
            cmds.rotate (0, -rotAngle, 0, a = 1)
            cmds.setKeyframe (t = frameNumber)
            
            frameNumber = frameNumber + keyFramePadding
            cmds.rotate (0, 0, 0, a= 1)
            cmds.setKeyframe (t = frameNumber)
            
        if rotZN:
            frameNumber = frameNumber + keyFramePadding    
            cmds.rotate (0, 0, -rotAngle, a = 1)
            cmds.setKeyframe (t = frameNumber)
            
            frameNumber = frameNumber + keyFramePadding
            cmds.rotate (0, 0, 0, a= 1)
            cmds.setKeyframe (t = frameNumber)
        
        if rotZP:
            frameNumber = frameNumber + keyFramePadding
            cmds.rotate (0, 0, rotAngle, a= 1)
            cmds.setKeyframe (t = frameNumber)
            
            frameNumber = frameNumber + keyFramePadding
            cmds.rotate (0, 0, 0, a= 1)
            cmds.setKeyframe (t = frameNumber)
        
        if rotXP:
            frameNumber = frameNumber + keyFramePadding
            cmds.rotate (rotAngle, 0, 0, a= 1)
            cmds.setKeyframe (t = frameNumber)
            
            frameNumber = frameNumber + keyFramePadding
            cmds.rotate (0, 0, 0, a= 1)
            cmds.setKeyframe (t = frameNumber)
        
        if rotXN:
            frameNumber = frameNumber + keyFramePadding    
            cmds.rotate (-rotAngle, 0, 0, a = 1)
            cmds.setKeyframe (t = frameNumber)
            
            frameNumber = frameNumber + keyFramePadding
            cmds.rotate (0, 0, 0, a= 1)
            cmds.setKeyframe (t = frameNumber)
    
    #Setting the frame in the timeline
    currentMaxTimeline = cmds.playbackOptions(query=True, maxTime=True)
    if (currentMaxTimeline > frameNumber):
        cmds.playbackOptions(maxTime = currentMaxTimeline)
    else:        
        cmds.playbackOptions(maxTime = frameNumber)

'''
####################################################################################################
RANGE OF MOTION SETUP
END
####################################################################################################
'''

#Function to open the help documentation
def showHelp():
    cmds.showHelp("http://urtdocs.shakyatul.com/", absolute=True)

#For development mode... only checks if the window exists when pressed numpad 'enter'
# Showing the MainDialog window
if __name__ == "__main__":
    
    #Checks if the windows already exists. If it does, deletes it before creating a new window. If not, passes (does nothing) before creating the new window
    try:
        test_dialog.close()
        test_dialog.deleteLater()
    except:
            pass
    
    test_dialog = MainDialog()
    test_dialog.show()

