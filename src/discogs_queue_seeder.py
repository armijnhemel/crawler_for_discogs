#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
#
# Copyright - Armijn Hemel

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
               40: 'discogs-40M', 41: 'discogs-41M', 42: 'discogs-42M',
               43: 'discogs-43M', 44: 'discogs-44M', 45: 'discogs-45M',
               46: 'discogs-46M', 47: 'discogs-47M', 48: 'discogs-48M',
               49: 'discogs-49M', 50: 'discogs-50M', 51: 'discogs-51M',
               52: 'discogs-52M', 53: 'discogs-53M', 54: 'discogs-54M',
               55: 'discogs-55M', 56: 'discogs-56M', 57: 'discogs-57M',
               58: 'discogs-58M', 59: 'discogs-59M', 60: 'discogs-60M',
               61: 'discogs-61M', 62: 'discogs-62M', 63: 'discogs-63M',
               64: 'discogs-64M', 65: 'discogs-65M', 66: 'discogs-66M',
               67: 'discogs-67M', 68: 'discogs-68M', 69: 'discogs-69M',
               70: 'discogs-70M', 71: 'discogs-71M', 72: 'discogs-72M',
               73: 'discogs-73M', 74: 'discogs-74M', 75: 'discogs-75M',
               76: 'discogs-76M', 77: 'discogs-77M', 78: 'discogs-78M',
               79: 'discogs-79M', 80: 'discogs-80M', 81: 'discogs-81M',
               82: 'discogs-82M', 83: 'discogs-83M', 84: 'discogs-84M',
               85: 'discogs-85M', 86: 'discogs-86M', 87: 'discogs-87M',
               88: 'discogs-88M', 89: 'discogs-89M', 90: 'discogs-90M',
               91: 'discogs-91M', 92: 'discogs-92M', 93: 'discogs-93M',
               94: 'discogs-94M', 95: 'discogs-95M', 96: 'discogs-96M',
               97: 'discogs-97M', 98: 'discogs-98M', 99: 'discogs-99M',
}


@click.command(short_help='Queue release numbers from the Discogs XML into redis as tasks')
@click.option('--new-result-file', '-n', 'new_result_file', required=True,
              help='new results file', type=click.Path(exists=True))
@click.option('--old-result-file', '-o', 'old_result_file', help='old results file',
              type=click.Path(exists=True))
@click.option('--verbose', '-v', help='verbose (default: False)', is_flag=True, default=False)
def main(new_result_file, old_result_file, verbose):
    # first check if redis is running or not
    try:
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

        # check if Redis is running
        redis_client.ping()
    except redis.exceptions.ConnectionError as e:
        print("Cannot connect to Redis server", e, file=sys.stderr)
        sys.exit(1)

    old_releases = set()

    try:
        if old_result_file is not None:
            with open(old_result_file, 'r') as result_file:
                for line in result_file:
                    release_id, release_hash = line.strip().split()
                    release_id = int(release_id)
                    old_releases.add((release_id, release_hash))

        if verbose:
            print(f"Found {len(old_releases)} old releases")

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
            if verbose:
                print(f"Queuing {new_releases} new/changed releases")

    except Exception as e:
        print("Cannot process dump file", e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
