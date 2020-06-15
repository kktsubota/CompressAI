"""
Simple plotting utility to display Rate-Distortion curves (RD) comparison
between codecs.
"""
import argparse
import json
import sys

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

_backends = ['matplotlib']

try:
    import plotly.graph_objs as go
    import plotly.offline
    _backends.append('plotly')
except ImportError:
    pass


def parse_json_file(filepath, metric):
    filepath = Path(filepath)
    name = filepath.name.split('.')[0]
    with filepath.open('r') as f:
        try:
            data = json.load(f)
        except json.decoder.JSONDecodeError as err:
            print(f'Error reading file "{filepath}"')
            raise err

    if 'results' not in data or \
            'bpp' not in data['results']:
        raise ValueError(f'Invalid file "{filepath}"')

    if metric not in data['results']:
        raise ValueError(
            f'Error: metric "{metric}" not available.'
            f' Available metrics: {", ".join(data["results"].keys())}')

    if metric == 'msssim':
        # Convert to db
        values = np.array(data['results'][metric])
        data['results'][metric] = -10 * np.log10(1 - values)

    return {
        'name': data.get('name', name),
        'xs': data['results']['bpp'],
        'ys': data['results'][metric]
    }


def matplotlib_plt(scatters, title, ylabel, output_file, limits=None):
    fig, ax = plt.subplots(figsize=(9, 6))
    for sc in scatters:
        ax.plot(sc['xs'], sc['ys'], '.-', label=sc['name'])

    ax.set_xlabel('Bit-rate [bpp]')
    ax.set_ylabel(ylabel)
    if limits is not None:
        ax.axis(limits)
    ax.legend(loc='lower right')

    if title:
        ax.title.set_text(title)
    if output_file:
        fig.savefig(output_file)

    plt.show()


def plotly_plt(scatters, title, ylabel, output_file, limits=None):
    scatters = [
        go.Scatter(x=sc['xs'], y=sc['ys'], name=sc['name']) for sc in scatters
    ]
    plotly.offline.plot(
        {
            "data":
            scatters,
            "layout":
            go.Layout(
                title=title,
                legend={
                    'font': {
                        'size': 14,
                    },
                },
                xaxis={
                    'title': 'Bit-rate [bpp]',
                    'range': [limits[0], limits[1]]
                },
                yaxis={
                    'title': ylabel,
                    'range': [limits[2], limits[3]]
                },
            )
        },
        auto_open=False,
        filename=output_file or 'plot.html')


def setup_args():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-f',
                        '--results-file',
                        metavar='',
                        default='',
                        type=str,
                        nargs='*',
                        required=True)
    parser.add_argument('-m',
                        '--metric',
                        metavar='',
                        type=str,
                        default='psnr',
                        help='Metric (default: %(default)s)')
    parser.add_argument('-t',
                        '--title',
                        metavar='',
                        type=str,
                        help='Plot title')
    parser.add_argument('-o',
                        '--output',
                        metavar='',
                        type=str,
                        help='Output file name')
    parser.add_argument(
        '--axes',
        metavar='',
        type=int,
        nargs=4,
        default=(0, 2, 28, 43),
        help='Axes limit (xmin, xmax, ymin, ymax), default: %(default)s')
    parser.add_argument('--backend',
                        type=str,
                        metavar='',
                        default=_backends[0],
                        choices=_backends,
                        help='Change plot backend (default: %(default)s)')
    return parser


def main(argv):
    args = setup_args().parse_args(argv)

    scatters = []
    for f in args.results_file:
        rv = parse_json_file(f, args.metric)
        scatters.append(rv)

    ylabel = args.metric
    func_map = {
        'matplotlib': matplotlib_plt,
        'plotly': plotly_plt,
    }
    func_map[args.backend](scatters,
                           args.title,
                           ylabel,
                           args.output,
                           limits=args.axes)


if __name__ == '__main__':
    main(sys.argv[1:])
