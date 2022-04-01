
import numpy as np
from numpy import linspace
import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from functools import partial

import sys


# import numpy as np


class gearPlot(pg.GraphicsLayoutWidget):
    def __init__(self, p):
        super().__init__()
        # self.gr = p.ratio

        self.input_v = {'WD': 0.7, 'Pedal Rad': 0.13, 'Wind': 0}
        # legforce could be both
        self.depend_v = {'Ratio': p.ratio}

        self.ambi_v = {'Leg Force': 1000, 'Cadence': 80, 'Ground Speed': 50, }

        self.par = p
        self.gear_plot = self.addPlot(1, 0)
        self.cadence_plot = self.addPlot(0, 0)
        self.torque_plot = self.addPlot(0, 1)
        self.air_plot = self.addPlot(1, 1)
        self._set_g_plot()
        self._set_pow_plot()
        self.reset_v_cad()
        self._set_cad_p()
        self._set_t_p()

    def _set_g_plot(self):
        self.gear_plot.addLegend()
        self.gear_plot.setLabels(**{'title': 'Ratio per rear gear', 'left': 'ratio', 'bottom': 'rear index'})
        self.g_p = []
        col = ['r', 'g', 'b', 'y']
        for i in range(len(self.par.gear[0])):
            st = 'Front chainring: ' + str(i)
            self.g_p.append(self.gear_plot.plot(pen=col[i], width=3, name=st))
        self.combine_p = self.gear_plot.plot(pen='c', width=3, name='Combined')

    def _set_t_p(self):
        self.torque_plot.setLabels(
            **{'title': 'Torque vs speed', 'left': ('Torque', 'Nm'), 'bottom': ('speed', 'km/h')})
        self.tor_s = self.torque_plot.plot(pen='c', width=3, name='Speed')
        pass

    def _set_cad_p(self):

        self.cadence_plot.setLabels(
            **{'title': 'cadence vs speed', 'left': ('cad', 'RPM'), 'bottom': ('speed', 'km/h')})
        self.cad = self.cadence_plot.plot(pen='c', width=3)
        pass

    def _set_pow_plot(self):
        self.air_plot.addLegend()
        self.air_plot.setLabels(**{'title': 'Air resisrace vs speed', 'left': ('power', 'W'),
                                   'bottom': ('speed', 'km/h')})
        self.na = self.air_plot.plot(pen='c', width=3, name='No resestance')
        self.air_r = self.air_plot.plot(pen='b', width=3, name='Air')

    def res(self, v, c):
        s1 = v.shape[1]
        z = np.arange(s1)
        z2 = np.arange(c.size)
        for n, i in enumerate(self.g_p):
            i.setData(z, v[n])
        self.combine_p.setData(z2, c)
        self.res_other()

    def res_other(self):
        # cadence
        s = linspace(0, 20)

        # air

        power = 150 + 17.5 * s
        w_p = []
        w_t = []
        w_cad = []
        for si in range(s.size):
            self.ambi_v['Ground Speed'] = s[si]
            self.reset_air(power[si])
            w_p.append(self.depend_v['Pow'])
            self.reset_air(power[si], False)
            w_t.append(self.depend_v['Torque'])
            w_cad.append(self.ambi_v['Cadence'])

        s_km = s * 3.6
        self.air_r.setData(s_km, w_p)
        self.na.setData(s_km, power)

        self.cad.setData(s_km, w_cad)

        self.tor_s.setData(s_km, w_t)

    def reset_pre(self):
        self.depend_v['WR'] = self.input_v['WD'] / 2
        self.depend_v['WC'] = self.input_v['WD'] * np.pi

    def reset_v_cad(self):
        self.reset_pre()
        # pre defined

        self.depend_v['Omega'] = self.ambi_v['Cadence'] * np.pi / 30
        self.depend_v['Torque'] = self.ambi_v['Leg Force'] * self.input_v['Pedal Rad']
        self.depend_v['W Omega'] = self.depend_v['Omega'] * self.depend_v['Ratio']
        self.depend_v['W M'] = self.depend_v['Torque'] / self.depend_v['Ratio']
        self.ambi_v['Ground Speed'] = self.depend_v['W Omega'] * self.depend_v['WC']
        self.depend_v['Ground Force'] = self.depend_v['W M'] / self.depend_v['WR']

        # ||wheel tor=fric*wrad||power, vs no wind"""

    def reset_v_ground(self):
        self.reset_pre()
        self.depend_v['W Omega'] = self.ambi_v['Ground Speed'] / self.depend_v['WC']
        self.depend_v['Omega'] = self.depend_v['W Omega'] / self.depend_v['Ratio']
        self.ambi_v['Cadence'] = self.depend_v['Omega'] * 30 / np.pi
        self.depend_v['Pow'] = self.depend_v['Torque'] * self.depend_v['Omega']

    def reset_air(self, resistace, drag=True):
        v = self.ambi_v['Ground Speed'] - self.input_v['Wind']
        a = 2  # m^2
        c = 1
        if drag:
            wind_drag = 0.5 * 1.255 * a * c * v ** 2
        else:
            wind_drag = 0
        self.reset_v_ground()
        self.depend_v['Ground Force'] = wind_drag
        # print(f'power n: {resistace}, drag: {wind_drag}, total: {self.depend_v["Ground Force"]}')
        self.depend_v['W Omega'] = self.ambi_v['Ground Speed'] / self.depend_v['WC']
        self.depend_v['Omega'] = self.depend_v['W Omega'] / self.depend_v['Ratio']
        self.depend_v['W M'] = self.depend_v['Ground Force'] * self.depend_v['WR']
        self.depend_v['Torque'] = self.depend_v['Ratio'] * self.depend_v['W M']
        self.depend_v['Pow'] = self.depend_v['Torque'] * self.depend_v['Omega'] + resistace

    def current_n(self):

        self.reset_v_cad()  # since no values changed just cal any


class Window(QMainWindow):
    # noinspection PyArgumentList
    def __init__(self):
        super().__init__()
        self.gear = [[34, 52],
                     [11, 12, 13, 14, 15, 17, 19, 21, 23, 25, 28]]
        self.active_g = np.ones(2)
        self.ratio = 1

        self.setWindowTitle('QMainWindow')
        self.cen = QWidget()
        self.scale_n = [[10, 2], [10, 3]]

        self.setCentralWidget(self.cen)
        self.running = False

        self.p_win = gearPlot(self)
        self.p_dock = QDockWidget('plots')
        self.p_dock.setWidget(self.p_win)
        self.addDockWidget(Qt.RightDockWidgetArea, self.p_dock)
        self.tb = QToolBar(self)
        self.addToolBar(self.tb)
        self.da = QAction('Set Gear')
        self.tb.addAction(self.da)
        self.da.triggered.connect(self.dia)

        self._set_tool()
        self._set_out()
        # self._set_data()
        # self._set_tar()

    def _set_tool(self):
        # scale
        self.gears = []
        self.layout = QVBoxLayout()
        self.cen.setLayout(self.layout)
        for w in range(len(self.gear)):
            gn = []
            lay = QHBoxLayout()

            for n, g in enumerate(self.gear[w]):
                sp = QPushButton()
                sp.setFixedSize(self.scale_n[w][0], self.scale_n[w][1] * g)
                lay.addWidget(sp)
                sp.clicked.connect(partial(self.change_gear, w, n))
                gn.append(sp)
            self.layout.addLayout(lay)
            self.gears.append(gn)
        self.res()

    def res(self):
        self.ratios()

    def change_gear(self, sprock, gear):
        self.active_g[sprock] = self.gear[sprock][gear]
        self.ratio = self.active_g[1] / self.active_g[0]

        for n, g in enumerate(self.gears[sprock]):
            if n == gear:
                v = 'red'
            else:
                v = 'grey'
            g.setStyleSheet("background-color: " + v + "; }")
        print(self.ratio)
        self.p_win.depend_v['Ratio'] = self.ratio
        self.p_win.current_n()
        self.reset_all_inputs()

    def ratios(self):
        ra = np.zeros((len(self.gear[0]), len(self.gear[1])))
        for i in range(ra.shape[0]):
            for j in range(ra.shape[1]):
                ra[i, j] = self.gear[1][j] / self.gear[0][i]
        com = np.sort(ra.flatten())
        self.p_win.res(ra, com)

    def _set_out(self):
        tool_wig = QWidget()
        tool_dock = QDockWidget('Current V')
        tool_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        tool_dock.setFeatures(QDockWidget.DockWidgetMovable)
        tool_dock.setWidget(tool_wig)
        self.addDockWidget(Qt.TopDockWidgetArea, tool_dock)
        lay = QGridLayout()
        tool_wig.setLayout(lay)
        self.data_v = {}
        self.data_out = {}
        n = 0
        ni = 0
        for ii in [self.p_win.input_v, self.p_win.ambi_v]:
            for i, j in ii.items():
                m = QLabel(i)
                k = QLineEdit(str(j))
                self.data_v[i] = k
                # k.setReadOnly(True)
                lay.addWidget(m, n, ni)
                lay.addWidget(k, n + 1, ni)
                ni += 1
                if ni >= 4:
                    ni = 0
                    n += 2
                k.editingFinished.connect(partial(self.data_res, i))
        if ni != 0:
            ni = 0
            n += 2

        for i, j in self.p_win.depend_v.items():
            m = QLabel(i)
            k = QLabel(str(j))
            self.data_out[i] = k
            lay.addWidget(m, n, ni)
            lay.addWidget(k, n + 1, ni)
            ni += 1
            if ni >= 4:
                ni = 0
                n += 2

    def data_res(self, i):
        v = float(self.data_v[i].text())
        if i in self.p_win.input_v.keys():
            self.p_win.input_v[i] = v
            self.p_win.current_n()
        else:
            self.p_win.ambi_v[i] = v
            if i == 'Ground Speed':
                self.p_win.reset_v_ground()
            else:
                self.p_win.current_n()
        self.reset_all_inputs()

    def reset_all_inputs(self):
        for ii in [self.p_win.input_v, self.p_win.ambi_v]:
            for i, j in ii.items():
                self.data_v[i].setText(str(j))
                # k.setReadOnly(True)

        for i, j in self.p_win.depend_v.items():
            self.data_out[i].setText(str(j))
        self.p_win.res_other()

    def dia(self):
        da = QInputDialog()

        da.setCancelButtonText('Rear')
        da.setOkButtonText('Front')
        da.setComboBoxItems(['Cancle', 'Front', 'rear'])
        tex, v_front = da.getText(self, 'Chose gear', 'select comma delimate')
        tex = tex.replace(' ', '')
        print(f'text: {tex}, bool: {v_front}')
        tex_int = [int(x) for x in tex.split(',')]
        tex_int = sorted(tex_int)
        if v_front:
            i = 0
        else:
            i = 1
        self.gear[i] = tex_int
        self._set_tool()


"""for x = o, zerod distance solve no wind 0 = z and x=0:z=0, 
then solve for x,y,z = 0, 0, 0 and x = tar, y=0:include wind, z=0
subtract to find clicks"""



if __name__ == "__main__":
    app = QApplication(sys.argv)
    audio_app = Window()
    audio_app.show()
    sys.exit(app.exec_())
