#!/usr/bin/env python3

# Tool to split entries from the Discogs data dump and compute a hash
#
# SPDX-License-Identifier: Apache-2.0
#
# Copyright 2023 - Armijn Hemel

import configparser
import datetime
import gzip
import hashlib
import os
import sys

import xml.dom.pulldom

import click
import defusedxml.pulldom


@click.command(short_help='process BANG result files and output ELF graphs')
@click.option('--datadump', '-d', 'datadump', required=True, help='discogs data dump file', type=click.Path(exists=True))
def main(datadump):

    try:
        with gzip.open(datadump, 'rb') as dumpfile:
            doc = defusedxml.pulldom.parse(dumpfile)
            for event, node in doc:
                if event == xml.dom.pulldom.START_ELEMENT and node.tagName == 'release':
                    release_id = node.getAttribute('id')
                    doc.expandNode(node)

                    # compute a SHA1 hash of the XML
                    release_hash = hashlib.sha1(node.toxml().encode()).hexdigest()
                    print(release_id, release_hash)

    except Exception as e:
        print("Cannot open dump file", e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
