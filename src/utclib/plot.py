""" Plot TFEX data
"""
import numpy as np
import logging

import plotly.graph_objects as go
from plotly.subplots import make_subplots

log = logging.getLogger(__name__)


# This should be generated from SIRP (or used directly ?)
conv = {
    "si:femtosecond": {'symbol': 'fs',
                       'factor': 1e-15},
    "si:picosecond": {'symbol': 'ps',
                      'factor': 1e-12},
    "si:nanosecond": {'symbol': 'ns',
                      'factor': 1e-9},
    "si:microsecond": {'symbol': 'µs',
                       'factor': 1e-6},
    "si:millisecond": {'symbol': 'ms',
                       'factor': 1e-3},
    "si:second": {'symbol': 's',
                  'factor': 1},
    "si:minute": {'symbol': 'mn',
                  'factor': 60},
    "si:hour": {'symbol': 'h',
                'factor': 3600},
    "si:day": {'symbol': 'd',
               'factor': 86400},
    }


class Plot():
    def __init__(self, stats=None, unit="si:nanosecond"):
        self.stats = stats
        if stats:
            self.fig = make_subplots(rows=2, cols=1)
        else:
            self.fig = make_subplots(rows=1, cols=1)
        self.unit_factor = conv[unit]['factor']
        self.unit_symbol = conv[unit]['symbol']
        self.content = []

    def add_link(self, tf, offset_s=0, median=False,
                 rebin=False, start_midnight=True,
                 window_width=86400, show_average=None, jumps=None,
                 *kwargs):
        # find first non-timetag colum
        # In the future : add ability to select label(s)
        for col in tf.hdr.COLUMNS:
            if 'timetag' in col and col['timetag']:
                continue
            label = col['label']
            unit_str = col['unit']
            break
        data = tf.data[label]
        mjd = tf.timestamps.getMJD()

        data_unit = float(conv[unit_str]['factor'])
        if offset_s != 0:
            label += "({:+} {})".format(offset_s / self.unit_factor,
                                        self.unit_symbol)
        self.fig.add_trace(
            go.Scatter(
                x=mjd,
                y=(data * data_unit + offset_s) / self.unit_factor,
                mode="markers",
                name=label
            ),
            row=1, col=1)
        if median:
            hw = 0.5 * window_width / 86400
            median = np.zeros(len(data))
            for i in range(len(data)):
                curdate = mjd[i]
                date_array = ((mjd > curdate - hw) &
                              (mjd <= curdate + hw))
                median[i] = np.median(data[date_array])
            self.fig.add_trace(
                go.scatter(x=mjd , y=median),
                row=1, col=1)
        if rebin:
            dates = []
            values = []
            if start_midnight:
                curstart = np.floor(mjd[0])
            else:
                curstart = mjd[0]
            while curstart < mjd[-1]:
                curstop = curstart + window_width / 86400
                dates.append((curstart + curstop) / 2)
                values.append(np.mean(
                    data[(mjd > curstart) & (mjd < curstop)]))
                curstart = curstop
            self.fig.add_trace(
                go.Scatter(x=dates, y=values),
                row=1, col=1)

        if show_average:
            for mjdrange in show_average:
                mjd1, mjd2 = [float(x) for x in mjdrange.split(':')]
                sample = data[(mjd >= mjd1) & (mjd < mjd2)]
                mean = np.nanmean(sample)
                std = np.nanstd(sample)
                p = self.data_ax.plot(
                    [mjd1, mjd2], [mean, mean],
                    '-',
                    label="mean = {:.3f} ns, $\\sigma$ = {:.3f} ns".format(
                        mean, std))
                self.data_ax.fill_between(
                    [mjd1, mjd2],
                    [mean - std / 2, mean - std / 2],
                    [mean + std / 2, mean + std / 2],
                    interpolate=True,
                    alpha=0.5,
                    facecolor=p[-1].get_color())

#        self.content.append("{}-{}-{}".format(
#            tlink.hdr['LOC'], tlink.hdr['REM'], tlink.hdr['LINKTYPE']))
        self.content.append("test")

    def post_draw(self):
        self.fig.update_xaxes(title_text="MJD")
        self.fig.update_yaxes(title_text="dt /ns")
        self.fig['data'][0]['showlegend']=True
        self.fig.update_layout(
            xaxis_tickformat = "%d")

    def savefig(self, filename=None, **kwargs):
        if filename is None:
            filename = "_".join(self.content) + ".html"
        self.fig.write_html(
            filename,
            config={"displaylogo": False,
                    "displayModeBar": True,
                    'modeBarButtonsToRemove': [
                        'select2d',
                        'lasso2d',
                    ]
                   }
        )

