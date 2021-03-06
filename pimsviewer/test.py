from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import six

import os
import unittest
import nose
import numpy as np
from pimsviewer import Viewer, Slider, ProcessPlugin, AnnotatePlugin, PlottingPlugin
from pims import FramesSequence, Frame

import pandas as pd

class RandomReader(FramesSequence):
    def __init__(self, length=10, shape=(128, 128), dtype='uint8'):
        self._len = length
        self._dtype = dtype
        self._shape = shape

    def __len__(self):
        return self._len

    @property
    def frame_shape(self):
        return self._shape

    @property
    def pixel_type(self):
        return self._dtype

    def get_frame(self, i):
        if np.issubdtype(self._dtype, np.float):
            frame = np.random.random(self._shape).astype(self._dtype)
        else:
            frame = np.random.randint(0, np.iinfo(self._dtype).max,
                                     self._shape).astype(self._dtype)
        return Frame(frame, frame_no=i)


def add_noise(img, noise_level):
    return img + (np.random.random(img.shape) * noise_level).astype(img.dtype)


def tp_locate(image, radius, minmass, separation, noise_size, ax):
    _plot_style = dict(markersize=15, markeredgewidth=2,
                       markerfacecolor='none', markeredgecolor='r',
                       marker='o', linestyle='none')
    from trackpy import locate
    f = locate(image, radius * 2 + 1, minmass, None, separation, noise_size)
    if len(f) == 0:
        return None
    else:
        return ax.plot(f['x'], f['y'], **_plot_style)

def make_black_y(img, x):
    img = img.copy()
    img[..., :x] = 0
    return img


def convert_to_grey(img, r, g, b):
    color_axis = img.shape.index(3)
    img = np.rollaxis(img, color_axis, 3)
    grey = (img * [r, g, b]).sum(2)
    return grey.astype(img.dtype)  # coerce to original dtype


# TODO: this does not work because it changes the image shape
# RGBToGrey = ViewerPipeline(convert_to_grey, 'RGB to Grey', dock='right') + \
#             Slider('r', 0, 1, 0.2125, orientation='vertical') + \
#             Slider('g', 0, 1, 0.7154, orientation='vertical') + \
#             Slider('b', 0, 1, 0.0721, orientation='vertical')

class TestViewer(unittest.TestCase):
    def test_viewer_noreader(self):
        viewer = Viewer()
        viewer.show()

    def test_viewer_2d(self):
        viewer = Viewer(RandomReader(shape=(128, 128)))
        viewer.show()

    def test_viewer_rgb(self):
        viewer = Viewer(RandomReader(shape=(128, 128, 3)))
        viewer.show()

    def test_viewer_multichannel(self):
        viewer = Viewer(RandomReader(shape=(2, 128, 128)))
        viewer.show()

    def test_viewer_3d(self):
        viewer = Viewer(RandomReader(shape=(10, 128, 128)))
        viewer.show()

    def test_viewer_3d_rgb(self):
        viewer = Viewer(RandomReader(shape=(10, 128, 128, 3)))
        viewer.show()

    def test_viewer_3d_multichannel(self):
        viewer = Viewer(RandomReader(shape=(3, 10, 128, 128)))
        viewer.show()

    def test_viewer_processplugin(self):
        AddNoise = ProcessPlugin(add_noise, 'Add noise', dock='right') + \
           Slider('noise_level', 0, 100, 0, orientation='vertical')
        viewer = Viewer(RandomReader()) + AddNoise
        viewer.show()

    def test_viewer_processplugin_multiple(self):
        AddNoise = ProcessPlugin(add_noise, 'Add noise', dock='right') + \
           Slider('noise_level', 0, 100, 0, orientation='vertical')
        Reduce = ProcessPlugin(make_black_y, 'Make black', dock='left') + \
                       Slider('x', 0, 128, 0, value_type='int', orientation='vertical')
        viewer = Viewer(RandomReader(shape=(128, 128, 3))) + AddNoise + Reduce
        viewer.show()

    def test_viewer_interactive_plotting(self):
        Locate = PlottingPlugin(tp_locate, 'Locate', dock='right') + \
           Slider('radius', 1, 20, 7, value_type='int', orientation='vertical') + \
           Slider('separation', 1, 20, 7, value_type='float', orientation='vertical') + \
           Slider('noise_size', 1, 20, 1, value_type='int', orientation='vertical') + \
           Slider('minmass', 1, 10000, 100, value_type='int', orientation='vertical')
        viewer = Viewer(RandomReader(shape=(128, 128))) + Locate
        viewer.show()

    def test_viewer_annotate(self):
        f = pd.DataFrame(np.random.random((100, 2)) * 100 + 10, columns=['x', 'y'])
        f['frame'] = np.repeat(np.arange(10), 10)
        f['particle'] = np.tile(np.arange(10), 10)
        (Viewer(RandomReader(shape=(128, 128))) + AnnotatePlugin(f)).show()

    def test_viewer_annotate_mp(self):
        f = pd.DataFrame(np.random.random((300, 2)) * 100 + 10, columns=['x', 'y'])
        f['frame'] = np.repeat(np.arange(30), 10)
        f['particle'] = np.tile(np.arange(10), 30)
        (Viewer(RandomReader(shape=(128, 128, 3))) + AnnotatePlugin(f, frame_axes='tc')).show()

    def test_viewer_annotate_3d(self):
        f = pd.DataFrame(np.random.random((3000, 3)) * np.array([100, 100, 30]) + 10, columns=['x', 'y', 'z'])
        f['frame'] = np.repeat(np.arange(10), 300)
        f['particle'] = np.tile(np.arange(300), 10)
        (Viewer(RandomReader(shape=(50, 128, 128))) + AnnotatePlugin(f)).show()


if __name__ == '__main__':
    nose.runmodule(argv=[__file__, '-vvs'], exit=False)
