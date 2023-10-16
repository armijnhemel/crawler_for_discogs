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
    # first check if redis is running or not
    try:
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

        # check if Redis is running
        redis_client.ping()
    except redis.exceptions.ConnectionError as e:
        print("Cannot connec to Redis server", e, file=sys.stderr)
        sys.exit(1)

    old_releases = set()

    try:
        if old_result_file is not None:
            with open(old_result_file, 'r') as result_file:
                for line in result_file:
                    release_id, release_hash = line.strip().split()
                    release_id = int(release_id)
                    old_releases.add((release_id, release_hash))

        new_releases = 0
        with redis_client.pipeline(transaction=False) as pipe:
            with open(new_result_file, 'r') as result_file:
                for line in result_file:
                    release_id, release_hash = line.strip().split()
                    release_id = int(release_id)
                    if (release_id, release_hash) in old_releases:
                        continue
                    pipe.rpush('discogs', release_id)
                    new_releases += 1
            pipe.execute()

    except Exception as e:
        print("Cannot process dump file", e, file=sys.stderr)
        sys.exit(1)

    print(f"Queuing {new_releases} releases")


if __name__ == "__main__":
    main()
