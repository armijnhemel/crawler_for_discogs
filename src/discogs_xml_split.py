#!/usr/bin/env python3

# Tool to split entries from the Discogs data dump and compute a hash
#
# SPDX-License-Identifier: Apache-2.0
#
# Copyright 2023-2024 - Armijn Hemel

import gzip
import hashlib
import sys

import click

import defusedxml.ElementTree as et


@click.command(short_help='process Discogs XML file and compute SHA1 hashes for each release')
@click.option('--datadump', '-d', 'datadump', required=True, help='discogs data dump file',
              type=click.Path(exists=True))
@click.option('--result-file', '-r', 'result_file', required=True, help='file to write results to',
              type=click.Path())
def main(datadump, result_file):

    try:
        with gzip.open(datadump, 'rb') as dumpfile:
            with open(result_file, 'w') as res:
                for event, element in et.iterparse(dumpfile):
                    if element.tag == 'release':
                        release_id = element.attrib['id']
                        release_hash = hashlib.sha1(et.tostring(element, encoding='unicode').encode()).hexdigest()
                        res.write(f"{release_id}\t{release_hash}\n")
                        element.clear()

    except Exception as e:
        print("Cannot process dump file", e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
