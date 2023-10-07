#! /usr/bin/env python3

#-*- coding: utf-8 -*-

# SPDX-License-Identifier: Apache-2.0
# Licensed under Apache 2.0, see LICENSE file for details

import json
import sys

import click
import dulwich
import redis

# import YAML module for the configuration
from yaml import load
from yaml import YAMLError
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

# process json: sort, cleanup
def process_json(json_data, config):
    pass

@click.command(short_help='Continuously grab data from the Discogs API and store in Git')
@click.option('--config-file', '-c', required=True, help='configuration file (YAML)', type=click.File('r'))
@click.option('-v', '--verbose', is_flag=True, help='Enable debug logging')
def main(config_file, verbose):
    # read the configuration file. This is in YAML format
    try:
        config = load(config_file, Loader=Loader)
    except (YAMLError, PermissionError, UnicodeDecodeError) as e:
        print(f"Cannot open configuration file, exiting, {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
