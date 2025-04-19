import cv2 as cv
import numpy as np

from pcot.sources import SourceSet
from pcot.xform import XFormType, xformtype
from pcot.xforms.tabdata import TabData
from pcot.imagecube import ImageCube
from pcot.datum import Datum
from pcot.value import Value
from pcot.datumtypes import Type
from PySide2.QtGui import QColor
from pcot.expressions.register import datumfunc

import pcot.config

@xformtype
class XFormImageRectify(XFormType):
    """
    A node designed to rectify an image

    Author: Henry Howe
    Date:2025-04-19

    """

    def __init__(self):

        super().__init__("rectify", "processing", "0.0.0")

        self.addInputConnector("Left Image", Datum.IMG)
        self.addInputConnector("Right Image", Datum.IMG)
        
        self.addOutputConnector("Output", Datum.IMG)

    def createTab(self, n, w):
        return TabData(n, w)

    def init(self, n):
        # No initialisation required.
        pass

    def perform(self, node):
        pass