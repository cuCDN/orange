'''
<name>Scatterplot 3D</name>
<priority>2001</priority>
'''

from OWWidget import *
from plot.owplot3d import *

import orange
Discrete = orange.VarTypes.Discrete
Continuous = orange.VarTypes.Continuous

from Orange.preprocess.scaling import get_variable_values_sorted

import OWGUI
import OWToolbars
import orngVizRank
from OWkNNOptimization import *
from orngScaleScatterPlotData import *

import numpy

TooltipKind = enum('NONE', 'VISIBLE', 'ALL')

class ScatterPlotTheme(PlotTheme):
    def __init__(self):
        super(ScatterPlotTheme, self).__init__()
        self.grid_color = [0.8, 0.8, 0.8, 1.]

class LightTheme(ScatterPlotTheme):
    pass

class DarkTheme(ScatterPlotTheme):
    def __init__(self):
        super(DarkTheme, self).__init__()
        self.grid_color = [0.3, 0.3, 0.3, 1.]
        self.labels_color = [0.9, 0.9, 0.9, 1.]
        self.helpers_color = [0.9, 0.9, 0.9, 1.]
        self.axis_values_color = [0.7, 0.7, 0.7, 1.]
        self.axis_color = [0.8, 0.8, 0.8, 1.]
        self.background_color = [0., 0., 0., 1.]

class ScatterPlot(OWPlot3D, orngScaleScatterPlotData):
    def __init__(self, parent=None):
        OWPlot3D.__init__(self, parent)
        orngScaleScatterPlotData.__init__(self)

        null = lambda: None
        self.activateZooming = null

        self.disc_palette = ColorPaletteGenerator()
        self._theme = LightTheme()
        self.show_grid = True
        self.show_chassis = True

    def set_data(self, data, subset_data=None, **args):
        if data == None:
            return
        args['skipIfSame'] = False
        orngScaleScatterPlotData.set_data(self, data, subset_data, **args)
        OWPlot3D.set_plot_data(self, self.scaled_data, self.scaled_subset_data)

    def update_data(self, x_attr, y_attr, z_attr,
                    color_attr, symbol_attr, size_attr, label_attr):
        if self.data == None:
            return
        self.before_draw_callback = self.before_draw

        color_discrete = symbol_discrete = size_discrete = False

        color_index = -1
        if color_attr != '' and color_attr != '(Same color)':
            color_index = self.attribute_name_index[color_attr]
            if self.data_domain[color_attr].varType == Discrete:
                color_discrete = True
                self.disc_palette.setNumberOfColors(len(self.data_domain[color_attr].values))

        symbol_index = -1
        num_symbols_used = -1
        if symbol_attr != '' and symbol_attr != 'Same symbol)' and\
           len(self.data_domain[symbol_attr].values) < len(Symbol):
            symbol_index = self.attribute_name_index[symbol_attr]
            if self.data_domain[symbol_attr].varType == Discrete:
                symbol_discrete = True
                num_symbols_used = len(self.data_domain[symbol_attr].values)

        size_index = -1
        if size_attr != '' and size_attr != '(Same size)':
            size_index = self.attribute_name_index[size_attr]
            if self.data_domain[size_attr].varType == Discrete:
                size_discrete = True

        label_index = -1
        if label_attr != '' and label_attr != '(No labels)':
            label_index = self.attribute_name_index[label_attr]

        x_index = self.attribute_name_index[x_attr]
        y_index = self.attribute_name_index[y_attr]
        z_index = self.attribute_name_index[z_attr]

        x_discrete = self.data_domain[x_attr].varType == Discrete
        y_discrete = self.data_domain[y_attr].varType == Discrete
        z_discrete = self.data_domain[z_attr].varType == Discrete

        colors = []
        if color_discrete:
            for i in range(len(self.data_domain[color_attr].values)):
                c = self.disc_palette[i]
                colors.append(c)

        data_scale = [self.attr_values[x_attr][1] - self.attr_values[x_attr][0],
                      self.attr_values[y_attr][1] - self.attr_values[y_attr][0],
                      self.attr_values[z_attr][1] - self.attr_values[z_attr][0]]
        data_translation = [self.attr_values[x_attr][0],
                            self.attr_values[y_attr][0],
                            self.attr_values[z_attr][0]]
        data_scale = 1. / numpy.array(data_scale)
        if x_discrete:
            data_scale[0] = 0.5 / float(len(self.data_domain[x_attr].values))
            data_translation[0] = 1.
        if y_discrete:
            data_scale[1] = 0.5 / float(len(self.data_domain[y_attr].values))
            data_translation[1] = 1.
        if z_discrete:
            data_scale[2] = 0.5 / float(len(self.data_domain[z_attr].values))
            data_translation[2] = 1.

        self.clear()
        self.set_shown_attributes_indices(x_index, y_index, z_index,
            color_index, symbol_index, size_index, label_index,
            colors, num_symbols_used,
            x_discrete, y_discrete, z_discrete, self.jitter_size, self.jitter_continuous,
            data_scale, data_translation)

        if self.show_legend:
            legend_keys = {}
            color_index = color_index if color_index != -1 and color_discrete else -1
            size_index = size_index if size_index != -1 and size_discrete else -1
            symbol_index = symbol_index if symbol_index != -1 and symbol_discrete else -1

            single_legend = [color_index, size_index, symbol_index].count(-1) == 2
            if single_legend:
                legend_join = lambda name, val: val
            else:
                legend_join = lambda name, val: name + '=' + val 

            color_attr = self.data_domain[color_attr] if color_index != -1 else None
            symbol_attr = self.data_domain[symbol_attr] if symbol_index != -1 else None
            size_attr = self.data_domain[size_attr] if size_index != -1 else None

            if color_index != -1:
                num = len(color_attr.values)
                val = [[], [], [1.]*num, [Symbol.RECT]*num]
                var_values = get_variable_values_sorted(color_attr)
                for i in range(num):
                    val[0].append(legend_join(color_attr.name, var_values[i]))
                    c = self.disc_palette[i]
                    val[1].append([c.red()/255., c.green()/255., c.blue()/255., 1.])
                legend_keys[color_attr] = val

            if symbol_index != -1:
                num = len(symbol_attr.values)
                if legend_keys.has_key(symbol_attr):
                    val = legend_keys[symbol_attr]
                else:
                    val = [[], [(0, 0, 0, 1)]*num, [1.]*num, []]
                var_values = get_variable_values_sorted(symbol_attr)
                val[3] = []
                val[0] = []
                for i in range(num):
                    val[3].append(i)
                    val[0].append(legend_join(symbol_attr.name, var_values[i]))
                legend_keys[symbol_attr] = val

            if size_index != -1:
                num = len(size_attr.values)
                if legend_keys.has_key(size_attr):
                    val = legend_keys[size_attr]
                else:
                    val = [[], [(0, 0, 0, 1)]*num, [], [Symbol.RECT]*num]
                val[2] = []
                val[0] = []
                var_values = get_variable_values_sorted(size_attr)
                for i in range(num):
                    val[0].append(legend_join(size_attr.name, var_values[i]))
                    val[2].append(0.1 + float(i) / len(var_values))
                legend_keys[size_attr] = val

            for val in legend_keys.values():
                for i in range(len(val[1])):
                    self.legend.add_item(val[3][i], val[1][i], val[2][i], val[0][i])

        self.set_axis_title(Axis.X, x_attr)
        self.set_axis_title(Axis.Y, y_attr)
        self.set_axis_title(Axis.Z, z_attr)

        if x_discrete:
            self.set_axis_labels(Axis.X, get_variable_values_sorted(self.data_domain[x_attr]))
        if y_discrete:
            self.set_axis_labels(Axis.Y, get_variable_values_sorted(self.data_domain[y_attr]))
        if z_discrete:
            self.set_axis_labels(Axis.Z, get_variable_values_sorted(self.data_domain[z_attr]))

        self.updateGL()

    def before_draw(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMultMatrixd(numpy.array(self.projection.data(), dtype=float))
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glMultMatrixd(numpy.array(self.modelview.data(), dtype=float))

        if self.show_grid:
            self.draw_grid()
        if self.show_chassis:
            self.draw_chassis()

    def draw_chassis(self):
        glColor4f(*self._theme.axis_values_color)
        glEnable(GL_LINE_STIPPLE)
        glLineStipple(1, 0x00FF)
        glDisable(GL_DEPTH_TEST)
        glLineWidth(1)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        edges = [self.x_axis, self.y_axis, self.z_axis,
                 self.x_axis+self.unit_z, self.x_axis+self.unit_y,
                 self.x_axis+self.unit_z+self.unit_y,
                 self.y_axis+self.unit_x, self.y_axis+self.unit_z,
                 self.y_axis+self.unit_x+self.unit_z,
                 self.z_axis+self.unit_x, self.z_axis+self.unit_y,
                 self.z_axis+self.unit_x+self.unit_y]
        glBegin(GL_LINES)
        for edge in edges:
            start, end = edge
            glVertex3f(*start)
            glVertex3f(*end)
        glEnd()
        glDisable(GL_LINE_STIPPLE)
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

    def draw_grid(self):
        cam_in_space = numpy.array([
          self.camera[0]*self.camera_distance,
          self.camera[1]*self.camera_distance,
          self.camera[2]*self.camera_distance
        ])

        def _draw_grid(axis0, axis1, normal0, normal1, i, j):
            glColor4f(*self._theme.grid_color)
            for axis, normal, coord_index in zip([axis0, axis1], [normal0, normal1], [i, j]):
                start, end = axis.copy()
                start_value = self.map_to_data(start.copy())[coord_index]
                end_value = self.map_to_data(end.copy())[coord_index]
                values, _ = loose_label(start_value, end_value, 7)
                for value in values:
                    if not (start_value <= value <= end_value):
                        continue
                    position = start + (end-start)*((value-start_value) / float(end_value-start_value))
                    glBegin(GL_LINES)
                    glVertex3f(*position)
                    glVertex3f(*(position-normal*1.))
                    glEnd()

        glDisable(GL_DEPTH_TEST)
        glLineWidth(1)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        planes = [self.axis_plane_xy, self.axis_plane_yz,
                  self.axis_plane_xy_back, self.axis_plane_yz_right]
        axes = [[self.x_axis, self.y_axis],
                [self.y_axis, self.z_axis],
                [self.x_axis+self.unit_z, self.y_axis+self.unit_z],
                [self.z_axis+self.unit_x, self.y_axis+self.unit_x]]
        normals = [[numpy.array([0,-1, 0]), numpy.array([-1, 0, 0])],
                   [numpy.array([0, 0,-1]), numpy.array([ 0,-1, 0])],
                   [numpy.array([0,-1, 0]), numpy.array([-1, 0, 0])],
                   [numpy.array([0,-1, 0]), numpy.array([ 0, 0,-1])]]
        coords = [[0, 1],
                  [1, 2],
                  [0, 1],
                  [2, 1]]
        visible_planes = [plane_visible(plane, cam_in_space) for plane in planes]
        xz_visible = not plane_visible(self.axis_plane_xz, cam_in_space)
        if xz_visible:
            _draw_grid(self.x_axis, self.z_axis, numpy.array([0,0,-1]), numpy.array([-1,0,0]), 0, 2)
        for visible, (axis0, axis1), (normal0, normal1), (i, j) in\
             zip(visible_planes, axes, normals, coords):
            if not visible:
                _draw_grid(axis0, axis1, normal0, normal1, i, j)

        glEnable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

class OWScatterPlot3D(OWWidget):
    settingsList = ['plot.show_legend', 'plot.symbol_size', 'plot.show_x_axis_title', 'plot.show_y_axis_title',
                    'plot.show_z_axis_title', 'plot.show_legend', 'plot.use_2d_symbols',
                    'plot.alpha_value', 'plot.show_grid', 'plot.pitch', 'plot.yaw', 'plot.use_ortho',
                    'plot.show_chassis', 'plot.show_axes',
                    'auto_send_selection', 'auto_send_selection_update',
                    'plot.jitter_size', 'plot.jitter_continuous']
    contextHandlers = {'': DomainContextHandler('', ['x_attr', 'y_attr', 'z_attr'])}
    jitter_sizes = [0.0, 0.1, 0.5, 1, 2, 3, 4, 5, 7, 10, 15, 20, 30, 40, 50]

    def __init__(self, parent=None, signalManager=None, name='Scatter Plot 3D'):
        OWWidget.__init__(self, parent, signalManager, name, True)

        self.inputs = [('Examples', ExampleTable, self.set_data, Default), ('Subset Examples', ExampleTable, self.set_subset_data)]
        self.outputs = [('Selected Examples', ExampleTable), ('Unselected Examples', ExampleTable)]

        self.x_attr = ''
        self.y_attr = ''
        self.z_attr = ''

        self.x_attr_discrete = False
        self.y_attr_discrete = False
        self.z_attr_discrete = False

        self.color_attr = ''
        self.size_attr = ''
        self.symbol_attr = ''
        self.label_attr = ''

        self.tabs = OWGUI.tabWidget(self.controlArea)
        self.main_tab = OWGUI.createTabPage(self.tabs, 'Main')
        self.settings_tab = OWGUI.createTabPage(self.tabs, 'Settings', canScroll=True)

        self.x_attr_cb = OWGUI.comboBox(self.main_tab, self, 'x_attr', box='X-axis attribute',
            tooltip='Attribute to plot on X axis.',
            callback=self.on_axis_change,
            sendSelectedValue=1,
            valueType=str)

        self.y_attr_cb = OWGUI.comboBox(self.main_tab, self, 'y_attr', box='Y-axis attribute',
            tooltip='Attribute to plot on Y axis.',
            callback=self.on_axis_change,
            sendSelectedValue=1,
            valueType=str)

        self.z_attr_cb = OWGUI.comboBox(self.main_tab, self, 'z_attr', box='Z-axis attribute',
            tooltip='Attribute to plot on Z axis.',
            callback=self.on_axis_change,
            sendSelectedValue=1,
            valueType=str)

        self.color_attr_cb = OWGUI.comboBox(self.main_tab, self, 'color_attr', box='Point color',
            tooltip='Attribute to use for point color',
            callback=self.on_axis_change,
            sendSelectedValue=1,
            valueType=str)

        # Additional point properties (labels, size, symbol).
        additional_box = OWGUI.widgetBox(self.main_tab, 'Additional Point Properties')
        self.size_attr_cb = OWGUI.comboBox(additional_box, self, 'size_attr', label='Point size:',
            tooltip='Attribute to use for point size',
            callback=self.on_axis_change,
            indent=10,
            emptyString='(Same size)',
            sendSelectedValue=1,
            valueType=str)

        self.symbol_attr_cb = OWGUI.comboBox(additional_box, self, 'symbol_attr', label='Point symbol:',
            tooltip='Attribute to use for point symbol',
            callback=self.on_axis_change,
            indent=10,
            emptyString='(Same symbol)',
            sendSelectedValue=1,
            valueType=str)

        self.label_attr_cb = OWGUI.comboBox(additional_box, self, 'label_attr', label='Point label:',
            tooltip='Attribute to use for pointLabel',
            callback=self.on_axis_change,
            indent=10,
            emptyString='(No labels)',
            sendSelectedValue=1,
            valueType=str)

        self.plot = ScatterPlot(self)
        self.vizrank = OWVizRank(self, self.signalManager, self.plot, orngVizRank.SCATTERPLOT3D, 'ScatterPlot3D')
        self.optimization_dlg = self.vizrank

        self.optimization_buttons = OWGUI.widgetBox(self.main_tab, 'Optimization dialogs', orientation='horizontal')
        OWGUI.button(self.optimization_buttons, self, 'VizRank', callback=self.vizrank.reshow,
            tooltip='Opens VizRank dialog, where you can search for interesting projections with different subsets of attributes',
            debuggingEnabled=0)

        box = OWGUI.widgetBox(self.settings_tab, 'Point properties')
        ss = OWGUI.hSlider(box, self, 'plot.symbol_scale', label='Symbol scale',
            minValue=0, maxValue=20,
            tooltip='Scale symbol size',
            callback=self.on_checkbox_update)
        ss.setValue(4)

        OWGUI.hSlider(box, self, 'plot.alpha_value', label='Transparency',
            minValue=10, maxValue=255,
            tooltip='Point transparency value',
            callback=self.on_checkbox_update)
        OWGUI.rubber(box)

        box = OWGUI.widgetBox(self.settings_tab, 'Jittering Options')
        self.jitter_size_combo = OWGUI.comboBox(box, self, 'plot.jitter_size', label='Jittering size (% of size)'+'  ',
            orientation='horizontal',
            callback=self.handleNewSignals,
            items=self.jitter_sizes,
            sendSelectedValue=1,
            valueType=float)
        OWGUI.checkBox(box, self, 'plot.jitter_continuous', 'Jitter continuous attributes',
            callback=self.handleNewSignals,
            tooltip='Does jittering apply also on continuous attributes?')

        self.dark_theme = False

        box = OWGUI.widgetBox(self.settings_tab, 'General settings')
        OWGUI.checkBox(box, self, 'plot.show_x_axis_title',   'X axis title',   callback=self.on_checkbox_update)
        OWGUI.checkBox(box, self, 'plot.show_y_axis_title',   'Y axis title',   callback=self.on_checkbox_update)
        OWGUI.checkBox(box, self, 'plot.show_z_axis_title',   'Z axis title',   callback=self.on_checkbox_update)
        OWGUI.checkBox(box, self, 'plot.show_legend',         'Show legend',    callback=self.on_checkbox_update)
        OWGUI.checkBox(box, self, 'plot.use_ortho',           'Use ortho',      callback=self.on_checkbox_update)
        OWGUI.checkBox(box, self, 'plot.use_2d_symbols',      '2D symbols',     callback=self.update_plot)
        OWGUI.checkBox(box, self, 'dark_theme',               'Dark theme',     callback=self.on_theme_change)
        OWGUI.checkBox(box, self, 'plot.show_grid',           'Show grid',      callback=self.on_checkbox_update)
        OWGUI.checkBox(box, self, 'plot.show_axes',           'Show axes',      callback=self.on_checkbox_update)
        OWGUI.checkBox(box, self, 'plot.show_chassis',        'Show chassis',   callback=self.on_checkbox_update)
        OWGUI.checkBox(box, self, 'plot.hide_outside',        'Hide outside',   callback=self.on_checkbox_update)
        OWGUI.rubber(box)

        self.auto_send_selection = True
        self.auto_send_selection_update = False
        self.plot.selection_changed_callback = self.selection_changed_callback
        self.plot.selection_updated_callback = self.selection_updated_callback
        box = OWGUI.widgetBox(self.settings_tab, 'Auto Send Selected Data When...')
        OWGUI.checkBox(box, self, 'auto_send_selection', 'Adding/Removing selection areas',
            callback = self.on_checkbox_update, tooltip='Send selected data whenever a selection area is added or removed')
        OWGUI.checkBox(box, self, 'auto_send_selection_update', 'Moving selection areas',
            callback = self.on_checkbox_update, tooltip='Send selected data when a user moves or resizes an existing selection area')

        self.zoom_select_toolbar = OWToolbars.ZoomSelectToolbar(self, self.main_tab, self.plot, self.auto_send_selection,
            buttons=(1, 4, 5, 0, 6, 7, 8))
        self.connect(self.zoom_select_toolbar.buttonSendSelections, SIGNAL('clicked()'), self.send_selections)
        self.connect(self.zoom_select_toolbar.buttonSelectRect, SIGNAL('clicked()'), self.change_selection_type)
        self.connect(self.zoom_select_toolbar.buttonSelectPoly, SIGNAL('clicked()'), self.change_selection_type)
        self.connect(self.zoom_select_toolbar.buttonZoom, SIGNAL('clicked()'), self.change_selection_type)
        self.connect(self.zoom_select_toolbar.buttonRemoveLastSelection, SIGNAL('clicked()'), self.plot.remove_last_selection)
        self.connect(self.zoom_select_toolbar.buttonRemoveAllSelections, SIGNAL('clicked()'), self.plot.remove_all_selections)
        self.toolbarSelection = None

        self.tooltip_kind = TooltipKind.NONE
        box = OWGUI.widgetBox(self.settings_tab, 'Tooltips Settings')
        OWGUI.comboBox(box, self, 'tooltip_kind', items = [
            'Don\'t Show Tooltips', 'Show Visible Attributes', 'Show All Attributes'])

        self.plot.mouseover_callback = self.mouseover_callback

        self.main_tab.layout().addStretch(100)
        self.settings_tab.layout().addStretch(100)

        self.mainArea.layout().addWidget(self.plot)
        self.connect(self.graphButton, SIGNAL('clicked()'), self.plot.save_to_file)

        self.loadSettings()
        self.plot.update_camera()

        self.data = None
        self.subset_data = None
        self.resize(1100, 600)

    def mouseover_callback(self, index):
        if self.tooltip_kind == TooltipKind.VISIBLE:
            self.plot.show_tooltip(self.get_example_tooltip(self.data[index], self.shown_attr_indices))
        elif self.tooltip_kind == TooltipKind.ALL:
            self.plot.show_tooltip(self.get_example_tooltip(self.data[index]))

    def get_example_tooltip(self, example, indices=None, max_indices=20):
        if indices and type(indices[0]) == str:
            indices = [self.plot.attribute_name_index[i] for i in indices]
        if not indices:
            indices = range(len(self.data.domain.attributes))

        if example.domain.classVar:
            classIndex = self.plot.attribute_name_index[example.domain.classVar.name]
            while classIndex in indices:
                indices.remove(classIndex)

        text = '<b>Attributes:</b><br>'
        for index in indices[:max_indices]:
            attr = self.plot.data_domain[index].name
            if attr not in example.domain:  text += '&nbsp;'*4 + '%s = ?<br>' % (attr)
            elif example[attr].isSpecial(): text += '&nbsp;'*4 + '%s = ?<br>' % (attr)
            else:                           text += '&nbsp;'*4 + '%s = %s<br>' % (attr, str(example[attr]))

        if len(indices) > max_indices:
            text += '&nbsp;'*4 + ' ... <br>'

        if example.domain.classVar:
            text = text[:-4]
            text += '<hr><b>Class:</b><br>'
            if example.getclass().isSpecial(): text += '&nbsp;'*4 + '%s = ?<br>' % (example.domain.classVar.name)
            else:                              text += '&nbsp;'*4 + '%s = %s<br>' % (example.domain.classVar.name, str(example.getclass()))

        if len(example.domain.getmetas()) != 0:
            text = text[:-4]
            text += '<hr><b>Meta attributes:</b><br>'
            for key in example.domain.getmetas():
                try: text += '&nbsp;'*4 + '%s = %s<br>' % (example.domain[key].name, str(example[key]))
                except: pass
        return text[:-4]

    def selection_changed_callback(self):
        if self.plot.selection_type == SelectionType.ZOOM:
            indices = self.plot.get_selection_indices()
            if len(indices) < 1:
                self.plot.remove_all_selections()
                return
            selected_indices = [1 if i in indices else 0
                                for i in range(len(self.data))]
            selected = self.plot.raw_data.selectref(selected_indices)
            x_min = y_min = z_min = 1e100
            x_max = y_max = z_max = -1e100
            x_index = self.plot.attribute_name_index[self.x_attr]
            y_index = self.plot.attribute_name_index[self.y_attr]
            z_index = self.plot.attribute_name_index[self.z_attr]
            # TODO: there has to be a faster way
            for example in selected:
                x_min = min(example[x_index], x_min)
                y_min = min(example[y_index], y_min)
                z_min = min(example[z_index], z_min)
                x_max = max(example[x_index], x_max)
                y_max = max(example[y_index], y_max)
                z_max = max(example[z_index], z_max)
            self.plot.set_new_zoom(x_min, x_max, y_min, y_max, z_min, z_max)
        else:
            if self.auto_send_selection:
                self.send_selections()

    def selection_updated_callback(self):
        if self.plot.selection_type != SelectionType.ZOOM and self.auto_send_selection_update:
            self.send_selections()

    def change_selection_type(self):
        if self.toolbarSelection < 3:
            selection_type = [SelectionType.ZOOM, SelectionType.RECTANGLE, SelectionType.POLYGON][self.toolbarSelection]
            self.plot.set_selection_type(selection_type)

    def set_data(self, data=None):
        self.closeContext()
        self.vizrank.clearResults()
        same_domain = self.data and data and\
            data.domain.checksum() == self.data.domain.checksum()
        self.data = data
        if not same_domain:
            self.init_attr_values()
        self.openContext('', data)

    def init_attr_values(self):
        self.x_attr_cb.clear()
        self.y_attr_cb.clear()
        self.z_attr_cb.clear()
        self.color_attr_cb.clear()
        self.size_attr_cb.clear()
        self.symbol_attr_cb.clear()
        self.label_attr_cb.clear()

        self.discrete_attrs = {}

        if not self.data:
            return

        self.color_attr_cb.addItem('(Same color)')
        self.label_attr_cb.addItem('(No labels)')
        self.symbol_attr_cb.addItem('(Same symbol)')
        self.size_attr_cb.addItem('(Same size)')

        icons = OWGUI.getAttributeIcons() 
        for metavar in [self.data.domain.getmeta(mykey) for mykey in self.data.domain.getmetas().keys()]:
            self.label_attr_cb.addItem(icons[metavar.varType], metavar.name)

        for attr in self.data.domain:
            if attr.varType in [Discrete, Continuous]:
                self.x_attr_cb.addItem(icons[attr.varType], attr.name)
                self.y_attr_cb.addItem(icons[attr.varType], attr.name)
                self.z_attr_cb.addItem(icons[attr.varType], attr.name)
                self.color_attr_cb.addItem(icons[attr.varType], attr.name)
                self.size_attr_cb.addItem(icons[attr.varType], attr.name)
            if attr.varType == Discrete: 
                self.symbol_attr_cb.addItem(icons[attr.varType], attr.name)
            self.label_attr_cb.addItem(icons[attr.varType], attr.name)

        self.x_attr = str(self.x_attr_cb.itemText(0))
        if self.y_attr_cb.count() > 1:
            self.y_attr = str(self.y_attr_cb.itemText(1))
        else:
            self.y_attr = str(self.y_attr_cb.itemText(0))

        if self.z_attr_cb.count() > 2:
            self.z_attr = str(self.z_attr_cb.itemText(2))
        else:
            self.z_attr = str(self.z_attr_cb.itemText(0))

        if self.data.domain.classVar and self.data.domain.classVar.varType in [Discrete, Continuous]:
            self.color_attr = self.data.domain.classVar.name
        else:
            self.color_attr = ''

        self.symbol_attr = self.size_attr = self.label_attr = ''
        self.shown_attr_indices = [self.x_attr, self.y_attr, self.z_attr, self.color_attr]

    def set_subset_data(self, data=None):
        self.subset_data = data

    def handleNewSignals(self):
        self.vizrank.resetDialog()
        self.plot.set_data(self.data, self.subset_data)
        self.update_plot()
        self.send_selections()

    def saveSettings(self):
        OWWidget.saveSettings(self)

    def sendReport(self):
        self.startReport('%s [%s - %s - %s]' % (self.windowTitle(), self.x_attr, self.y_attr, self.z_attr))
        self.reportSettings('Visualized attributes',
                            [('X', self.x_attr),
                             ('Y', self.y_attr),
                             ('Z', self.z_attr),
                             self.color_attr and ('Color', self.color_attr),
                             self.label_attr and ('Label', self.label_attr),
                             self.symbol_attr and ('Symbol', self.symbol_attr),
                             self.size_attr  and ('Size', self.size_attr)])
        self.reportSettings('Settings',
                            [('Symbol size', self.plot.symbol_scale),
                             ('Transparency', self.plot.alpha_value),
                             ('Jittering', self.jitter_size),
                             ('Jitter continuous attributes', OWGUI.YesNo[self.jitter_continuous])
                             ])
        self.reportSection('Plot')
        self.reportImage(self.plot.save_to_file_direct, QSize(400, 400))

    def send_selections(self):
        if self.data == None:
            return
        indices = self.plot.get_selection_indices()
        selected = [1 if i in indices else 0 for i in range(len(self.data))]
        unselected = map(lambda n: 1-n, selected)
        selected = self.data.selectref(selected)
        unselected = self.data.selectref(unselected)
        self.send('Selected Examples', selected)
        self.send('Unselected Examples', unselected)

    def on_axis_change(self):
        if self.data is not None:
            self.update_plot()

    def on_theme_change(self):
        if self.dark_theme:
            self.plot.theme = DarkTheme()
        else:
            self.plot.theme = LightTheme()

    def on_checkbox_update(self):
        self.plot.updateGL()

    def update_plot(self):
        if self.data is None:
            return

        self.plot.update_data(self.x_attr, self.y_attr, self.z_attr,
                              self.color_attr, self.symbol_attr, self.size_attr,
                              self.label_attr)

    def showSelectedAttributes(self):
        val = self.vizrank.getSelectedProjection()
        if not val: return
        if self.data.domain.classVar:
            self.attr_color = self.data.domain.classVar.name
        if not self.plot.have_data:
            return
        attr_list = val[3]
        if attr_list and len(attr_list) == 3:
            self.x_attr = attr_list[0]
            self.y_attr = attr_list[1]
            self.z_attr = attr_list[2]

        self.update_plot()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = OWScatterPlot3D()
    data = orange.ExampleTable('../../doc/datasets/iris')
    w.set_data(data)
    w.handleNewSignals()
    w.show()
    app.exec_()