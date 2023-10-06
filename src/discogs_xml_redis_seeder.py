#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
#
# Copyright 2023 - Armijn Hemel

import sys

import click
import redis


@click.command(short_help='Queue release numbers from the Discogs XML into redis as tasks')
@click.option('--new-result-file', '-n', 'new_result_file', required=True, help='new results file', type=click.Path(exists=True))
@click.option('--old-result-file', '-o', 'old_result_file', help='old results file', type=click.Path(exists=True))
def main(new_result_file, old_result_file):

    old_releases = set()
    new_releases = set()

    try:
        if old_result_file is not None:
            with open(old_result_file, 'r') as result_file:
                for line in result_file:
                    release_id, release_hash = line.strip().split()
                    release_id = int(release_id)
                    old_releases.add((release_id, release_hash))

        with open(new_result_file, 'r') as result_file:
            for line in result_file:
                release_id, release_hash = line.strip().split()
                release_id = int(release_id)
                new_releases.add((release_id, release_hash))

        # remove everything that has not changed
        new_releases -= old_releases

        # now queue into redis
        print(f"Queuing {len(new_releases)} releases")
    except Exception as e:
        print("Cannot process dump file", e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
