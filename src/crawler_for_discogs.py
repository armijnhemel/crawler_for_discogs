#! /usr/bin/env python3

#-*- coding: utf-8 -*-

# SPDX-License-Identifier: Apache-2.0
# Licensed under Apache 2.0, see LICENSE file for details

import click
import dulwich
import redis


@click.command(short_help='Continuously grab data from the Discogs API and store in Git')
@click.option('--config-file', '-c', required=True, help='configuration file (YAML)', type=click.File('r'))
def main(config_file):
    pass

if __name__ == "__main__":
    main()
