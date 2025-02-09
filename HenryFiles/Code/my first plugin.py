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

@datumfunc
def example_func(a, b):
    """
    Example function that takes two numbers a,b and returns a+b*2
    @param a: number: first number
    @param b: number: second number
    """
    return a + b * Datum.k(2)

@datumfunc
def example_func2(img, k=2):
    """
    Example function that takes two numbers a,b and returns a+b*2
    @param img:img:the image
    @param k:number:the multiplier
    """
    # no need to construct a Datum with Datum.k(), because k is already
    # a Datum.
    return img * k

@datumfunc
def stringexample(a, b, op='add'):
    """
    String argument example
    @param a: number: first number
    @param b: number: second number
    @param op: string: operation to perform
    """
    if op.get(Datum.STRING) == 'add':
        return a + b
    elif op.get(Datum.STRING) == 'sub':
        return a - b
    else:
        raise ValueError("Unknown operation")
    
@datumfunc
def sumall(*args):
    """
    Sum all arguments
    """
    s = sum([x.get(Datum.NUMBER).n for x in args])
    return Datum(Datum.NUMBER, Value(s, 0, NOUNCERTAINTY), nullSourceSet)
