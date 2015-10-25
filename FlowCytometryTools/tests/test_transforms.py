'''
@author: jonathanfriedman
'''
import os
import unittest

import numpy as np
from numpy.testing import assert_almost_equal, assert_equal

from FlowCytometryTools import FCMeasurement
from FlowCytometryTools.core import transforms as trans
from FlowCytometryTools.core.transforms import Transformation


base_path = os.path.dirname(os.path.realpath(__file__))

test_path = os.path.join(base_path,'data', 'FlowCytometers', 
        'HTS_BD_LSR-II', 'HTS_BD_LSR_II_Mixed_Specimen_001_D6_D06.fcs')

n = 1000
_xmax = 2 ** 18  # max machine value
_ymax = 10 ** 4  # max display value
_xpos = np.logspace(-3, np.log10(_xmax), n)
_xneg = -_xpos[::-1]
_xall = np.r_[_xneg, _xpos]
_ypos = np.logspace(-3, np.log10(_ymax), n)
_yneg = -_ypos[::-1]
_yall = np.r_[_yneg, _ypos]


class TestTransforms(unittest.TestCase):
    def test_tlog(self):
        th = 2
        r = 10 ** 4
        d = np.log10(2 ** 18)
        result = trans.tlog(_xall, th, r, d)
        assert_almost_equal(result[_xall < th], np.log10(th) * 1. * r / d, decimal=3)
        self.assertTrue(np.all(result[_xall > th]))
        assert_almost_equal(r, result.max())

    def test_tlog_inv(self):
        th = 2
        expected = _xall.copy()
        expected[_xall <= th] = th
        result = trans.tlog_inv(trans.tlog(_xall, th=th), th=th)
        assert_almost_equal(result, expected)

    def test_x_for_spln(self):
        result = trans._x_for_spln(_xpos, len(_xpos), True)
        expected = _xpos
        assert_equal(result, expected)

        result = trans._x_for_spln(_xneg, len(_xneg), True)
        expected = _xneg
        assert_equal(result, expected)

        nx = 10
        result = trans._x_for_spln(0, nx, True)
        expected = [0] * nx
        assert_equal(result, expected)

        result = trans._x_for_spln(_xall, nx, True)
        assert_equal(result.min(), _xall.min())
        assert_equal(result.max(), _xall.max())
        assert_equal(len(np.where(result < 0)[0]),
                     len(np.where(result > 0)[0]))

    def test_hlog(self):
        hlpos = trans.hlog(_xpos)
        hlneg = trans.hlog(_xneg)
        assert_almost_equal((hlpos[-1] - _ymax) / _ymax, 0, decimal=2)
        assert_almost_equal(hlpos, -hlneg[::-1])  # check symmetry
        # test that values get larger as b decreases
        hlpos10 = trans.hlog(_xpos, b=10)
        self.assertTrue(np.all(hlpos10 >= hlpos))
        # check that converges to tlog for large values
        tlpos = trans.tlog(_xpos)
        i = np.where(_xpos > 1e4)[0]
        tlpos_large = tlpos[i]
        hlpos_large = hlpos10[i]
        d = (hlpos_large - tlpos_large) / hlpos_large
        assert_almost_equal(d, np.zeros(len(d)), decimal=2)
        # test spline option
        transformation = Transformation(transform='hlog', direction='forward')
        result1 = transformation(_xall, use_spln=True)
        result2 = transformation(_xall, use_spln=False)
        d = (result1 - result2) / result1
        assert_almost_equal(d, np.zeros(len(d)), decimal=2)

    def test_hlog_inv(self):
        expected = _xall
        result = trans.hlog_inv(trans.hlog(_xall))
        d = (result - expected) / expected
        assert_almost_equal(d, np.zeros(len(d)), decimal=2)

        result = trans.hlog_inv(trans.hlog(_xall, b=10), b=10)
        d = (result - expected) / expected
        assert_almost_equal(d, np.zeros(len(d)), decimal=2)

    def test_hlog_on_fc_measurement(self):
        fc_measurement = FCMeasurement(ID='test', datafile=test_path)
        fc_measurement = fc_measurement.transform(transform='hlog', b=10)
        data = fc_measurement.data.values[:3, :4]
        correct_output = np.array([[-8.22113965e+03, 1.20259949e+03, 1.01216449e-06,
                                    5.21899170e+03],
                                   [-8.66184277e+03, 1.01013794e+03, 1.01216449e-06,
                                    5.71275928e+03],
                                   [-8.79974414e+03, 1.52737976e+03, 1.01216449e-06,
                                    -4.95852930e+03]])
        np.testing.assert_array_almost_equal(data, correct_output, 5,
                                             err_msg='the hlog transformation gives '
                                                     'an incorrect result')
