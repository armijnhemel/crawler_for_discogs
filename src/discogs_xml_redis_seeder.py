#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
#
# Copyright 2023 - Armijn Hemel

import math
import sys

import click
import redis

REDIS_LISTS = {1: 'discogs-1M', 2: 'discogs-2M', 3: 'discogs-3M',
               4: 'discogs-4M', 5: 'discogs-5M', 6: 'discogs-6M',
               7: 'discogs-7M', 8: 'discogs-8M', 9: 'discogs-9M',
               10: 'discogs-10M', 11: 'discogs-11M', 12: 'discogs-12M',
               13: 'discogs-13M', 14: 'discogs-14M', 15: 'discogs-15M',
               16: 'discogs-16M', 17: 'discogs-17M', 18: 'discogs-18M',
               19: 'discogs-19M', 20: 'discogs-20M', 21: 'discogs-21M',
               22: 'discogs-22M', 23: 'discogs-23M', 24: 'discogs-24M',
               25: 'discogs-25M', 26: 'discogs-26M', 27: 'discogs-27M',
               28: 'discogs-28M', 29: 'discogs-29M', 30: 'discogs-30M',
               31: 'discogs-31M', 32: 'discogs-32M', 33: 'discogs-33M',
               34: 'discogs-34M', 35: 'discogs-35M', 36: 'discogs-36M',
               37: 'discogs-37M', 38: 'discogs-38M', 39: 'discogs-39M',
}


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
                    list_nr = math.ceil(release_id/1000000)
                    pipe.rpush(REDIS_LISTS[list_nr], release_id)
                    new_releases += 1
            pipe.execute()

    except Exception as e:
        print("Cannot process dump file", e, file=sys.stderr)
        sys.exit(1)

    print(f"Queuing {new_releases} releases")


if __name__ == "__main__":
    main()
