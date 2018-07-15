import argparse
import json
import os.path
import sys
import click

from microbench_plot import specification
from microbench_plot import figure
from microbench_plot.benchmark import GoogleBenchmark
from microbench_plot import utils

""" If the module has a command line interface then this
file should be the entry point for that interface. """


@click.command()
@click.argument('output', type=click.Path(dir_okay=False, resolve_path=True))
@click.argument('spec', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument('target')
@click.pass_context
def deps(ctx, output, spec, target):
    """Create a Makefile dependence"""

    utils.debug("Loading {}".format(spec))
    figure_spec = specification.load(spec)
    figure_spec = specification.apply_search_dirs(figure_spec, ctx.obj.get("INCLUDE", []))
    figure_deps = specification.get_deps(figure_spec)
    utils.debug("Saving to {}".format(output))
    specification.save_makefile_deps(output, target, figure_deps)


@click.command()
@click.argument('benchmark', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument('output', type=click.Path(dir_okay=False, resolve_path=True))
@click.option('--name-regex', help="a YAML spec for a figure")
@click.option('--x-field', help="field for X axis")
@click.option('--y-field', help="field for Y axis")
@click.pass_context
def bar(ctx, benchmark, name_regex, output, x_field, y_field):
    """Create a bar graph from BENCHMARK and write to OUTPUT"""
    default_spec = {
        "generator": "bar",
        "series": [
            {
                "input_file": benchmark,
            }
        ],
    }

    if x_field:
        default_spec["series"][0]["xfield"] = x_field
        default_spec["xaxis"] = {"label": x_field}
    if y_field:
        default_spec["series"][0]["yfield"] = y_field
        default_spec["yaxis"] = {"label": y_field, "scale": "log"}
    if name_regex:
        default_spec["series"][0]["regex"] = name_regex
        default_spec["title"] = name_regex

    fig = figure.generate(default_spec)
    fig.savefig(output, clip_on=False, transparent=False)


@click.command()
@click.argument('spec', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('-o', '--output', help="Output path.", type=click.Path(dir_okay=False, resolve_path=True))
@click.pass_context
def spec(ctx, output, spec):
    """Create a figure from a spec file"""
    include = ctx.obj.get("INCLUDE", [])

    figure_spec = specification.load(spec)
    if include:
        for d in include:
            utils.debug("searching dir {}".format(d))
        figure_spec = specification.apply_search_dirs(figure_spec, include)

        fig = figure.generate(figure_spec)

    # Decide output path
    if output is None and figure_spec.get("output_file", None) is not None:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        output_path = os.path.join(script_dir, figure_spec.get("output_file"))
        if not output_path.endswith(".pdf") and not output_path.endswith(".png"):
            base_output_path = output_path
            output_path = []
            for ext in figure_spec.get("output_format", ["pdf"]):
                ext = ext.lstrip(".")
                output_path.append(base_output_path + "." + ext)

    if fig is not None:
        # fig.show()
        utils.debug("writing to {}".format(output))
        fig.savefig(output, clip_on=False, transparent=False)


@click.group()
@click.option('--debug/--no-debug', help="print debug messages to stderr.", default=False)
@click.option('--include', help="Search location for input_file in spec.",
              multiple=True, type=click.Path(exists=True, file_okay=False, readable=True, resolve_path=True))
@click.pass_context
def main(ctx, debug, include):
    ctx.obj["INCLUDE"] = include
    utils.DEBUG = debug


main.add_command(deps)
main.add_command(bar)
main.add_command(spec)
