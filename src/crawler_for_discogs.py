#! /usr/bin/env python3

#-*- coding: utf-8 -*-

# SPDX-License-Identifier: Apache-2.0
# Licensed under Apache 2.0, see LICENSE file for details

import json
import sys

import click
import dulwich
import redis
import requests

# import YAML module for the configuration
from yaml import load
from yaml import YAMLError
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


# process json: sort, cleanup
def process_json(json_data, removes):
    for r in removes:
        try:
            if '/' in r:
                key1, key2 = r.split('/', 1)
                del json_data[key1][key2]
            else:
                del json_data[r]
        except KeyError:
            pass

    # write to a file in the correct Git directory
    print(json.dumps(json_data, sort_keys=True, indent=4))

@click.command(short_help='Continuously grab data from the Discogs API and store in Git')
@click.option('--config-file', '-c', required=True, help='configuration file (YAML)', type=click.File('r'))
@click.option('-v', '--verbose', is_flag=True, help='Enable debug logging')
def main(config_file, verbose):
    # read the configuration file. This is in YAML format
    removes = []
    try:
        config = load(config_file, Loader=Loader)
        if 'fields' in config:
            if 'remove' in config['fields']:
                for r in config['fields']['remove']:
                    removes.append(r)
    except (YAMLError, PermissionError, UnicodeDecodeError) as e:
        print(f"Cannot open configuration file, exiting, {e}", file=sys.stderr)
        sys.exit(1)

    try:
        with open('/home/armijn/discogs-data/json/24/24639869.json', 'rb') as json_file:
            json_data = json.load(json_file)
            process_json(json_data, removes)
    except Exception as e:
        pass


if __name__ == "__main__":
    main()
