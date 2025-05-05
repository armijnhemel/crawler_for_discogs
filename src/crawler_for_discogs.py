#! /usr/bin/env python3

#-*- coding: utf-8 -*-

# SPDX-License-Identifier: Apache-2.0
# Licensed under Apache 2.0, see LICENSE file for details
# Copyright - Armijn Hemel

import json
import pathlib
import sys
import time

import click
import dulwich
import dulwich.porcelain
import redis
import requests

# import YAML module for the configuration
from yaml import load
from yaml import YAMLError
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


AUTHOR = "Discogs Crawler <armijn@tjaldur.nl>"

# lists with names of queues release numbers are read from for downloading
LISTS_READ = {1: 'discogs-1M', 2: 'discogs-2M', 3: 'discogs-3M',
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
              100: 'discogs-100M', 101: 'discogs-101M', 102: 'discogs-102M',
              103: 'discogs-103M', 104: 'discogs-104M', 105: 'discogs-105M',
              106: 'discogs-106M', 107: 'discogs-107M', 108: 'discogs-108M',
              109: 'discogs-109M', 110: 'discogs-110M', 111: 'discogs-111M',
}

# lists with names of queues release numbers are written to after downloading
LISTS_PROCESS = {1: 'process-1M', 2: 'process-2M', 3: 'process-3M',
                 4: 'process-4M', 5: 'process-5M', 6: 'process-6M',
                 7: 'process-7M', 8: 'process-8M', 9: 'process-9M',
                 10: 'process-10M', 11: 'process-11M', 12: 'process-12M',
                 13: 'process-13M', 14: 'process-14M', 15: 'process-15M',
                 16: 'process-16M', 17: 'process-17M', 18: 'process-18M',
                 19: 'process-19M', 20: 'process-20M', 21: 'process-21M',
                 22: 'process-22M', 23: 'process-23M', 24: 'process-24M',
                 25: 'process-25M', 26: 'process-26M', 27: 'process-27M',
                 28: 'process-28M', 29: 'process-29M', 30: 'process-30M',
                 31: 'process-31M', 32: 'process-32M', 33: 'process-33M',
                 34: 'process-34M', 35: 'process-35M', 36: 'process-36M',
                 37: 'process-37M', 38: 'process-38M', 39: 'process-39M',
                 40: 'process-40M', 41: 'process-41M', 42: 'process-42M',
                 43: 'process-43M', 44: 'process-44M', 45: 'process-45M',
                 46: 'process-46M', 47: 'process-47M', 48: 'process-48M',
                 49: 'process-49M', 50: 'process-50M', 51: 'process-51M',
                 52: 'process-52M', 53: 'process-53M', 54: 'process-54M',
                 55: 'process-55M', 56: 'process-56M', 57: 'process-57M',
                 58: 'process-58M', 59: 'process-59M', 60: 'process-60M',
                 61: 'process-61M', 62: 'process-62M', 63: 'process-63M',
                 64: 'process-64M', 65: 'process-65M', 66: 'process-66M',
                 67: 'process-67M', 68: 'process-68M', 69: 'process-69M',
                 70: 'process-70M', 71: 'process-71M', 72: 'process-72M',
                 73: 'process-73M', 74: 'process-74M', 75: 'process-75M',
                 76: 'process-76M', 77: 'process-77M', 78: 'process-78M',
                 79: 'process-79M', 80: 'process-80M', 81: 'process-81M',
                 82: 'process-82M', 83: 'process-83M', 84: 'process-84M',
                 85: 'process-85M', 86: 'process-86M', 87: 'process-87M',
                 88: 'process-88M', 89: 'process-89M', 90: 'process-90M',
                 91: 'process-91M', 92: 'process-92M', 93: 'process-93M',
                 94: 'process-94M', 95: 'process-95M', 96: 'process-96M',
                 97: 'process-97M', 98: 'process-98M', 99: 'process-99M',
                 100: 'process-100M', 101: 'process-101M', 102: 'process-102M',
                 103: 'process-103M', 104: 'process-104M', 105: 'process-105M',
                 106: 'process-106M', 107: 'process-107M', 108: 'process-108M',
                 109: 'process-109M', 110: 'process-110M', 111: 'process-111M',
}

# process json: cleanup, sort, compare to already stored version
# and add or update in case it is different.
def process_json(json_data, removes, git_directory, repo, remove_thumbnails=True):
    '''Helper function to cleanup and sort JSON obtained from Discogs,
       write to a file and store in Git'''
    for remove_item in removes:
        try:
            if '/' in remove_item:
                key1, key2 = remove_item.split('/', 1)
                del json_data[key1][key2]
            else:
                del json_data[remove_item]
        except KeyError:
            pass

    if remove_thumbnails:
        for artist in json_data['artists']:
            try:
                del artist['thumbnail_url']
            except KeyError:
                pass
        for artist in json_data['extraartists']:
            try:
                del artist['thumbnail_url']
            except KeyError:
                pass
        for company in json_data['companies']:
            try:
                del company['thumbnail_url']
            except KeyError:
                pass
        for label in json_data['labels']:
            try:
                del label['thumbnail_url']
            except KeyError:
                pass
        for label in json_data['series']:
            try:
                del label['thumbnail_url']
            except KeyError:
                pass
        for track in json_data['tracklist']:
            if 'artists' in track:
                for artist in track['artists']:
                    try:
                        del artist['thumbnail_url']
                    except KeyError:
                        pass
            if 'extraartists' in track:
                for artist in track['extraartists']:
                    try:
                        del artist['thumbnail_url']
                    except KeyError:
                        pass

    json_filename = f"{json_data['id']}.json"
    new_file = True

    # first check if the file has changed. If not, then don't add
    # the file. Git has some intelligence built-in which prevents
    # unchanged files to be committed again, which Dulwich
    # doesn't seem to implement.
    if (git_directory / json_filename).exists():
        new_file = False
        with open(git_directory / json_filename, 'r') as json_file:
            existing_json = json.load(json_file)
            if existing_json == json_data:
                return

    # write to a file in the correct Git directory
    with open(git_directory / json_filename, 'w') as json_file:
        json.dump(json_data, json_file, sort_keys=True, indent=4)

    # add the file and commit
    dulwich.porcelain.add(repo, git_directory / json_filename)
    if new_file:
        dulwich.porcelain.commit(repo, f"Add {json_data['id']}", committer=AUTHOR, author=AUTHOR)
    else:
        dulwich.porcelain.commit(repo, f"Update {json_data['id']}", committer=AUTHOR, author=AUTHOR)

@click.command(short_help='Continuously grab data from the Discogs API and store in Git')
@click.option('--config-file', '-c', required=True, help='configuration file (YAML)',
              type=click.File('r'))
@click.option('-v', '--verbose', is_flag=True, help='Enable debug logging')
@click.option('-g', '--git', help='Location of Git repository (override config)',
              type=click.Path('exists=True', path_type=pathlib.Path))
@click.option('-u', '--user', help='User name (override config)')
@click.option('-t', '--token', help='Token (override config)')
@click.option('-l', '--list', 'redis_list_number', type=click.IntRange(min=1, max=90),
              required=True, help='Redis list number (1-90)')
def main(config_file, verbose, git, user, token, redis_list_number):
    # read the configuration file. This is in YAML format
    removes = []

    discogs_git = None
    discogs_user = None
    discogs_token = None

    try:
        config = load(config_file, Loader=Loader)
        if 'fields' in config:
            if 'remove' in config['fields']:
                for remove_item in config['fields']['remove']:
                    removes.append(remove_item)
    except (YAMLError, PermissionError, UnicodeDecodeError) as e:
        print(f"Cannot open configuration file, exiting, {e}", file=sys.stderr)
        sys.exit(1)

    # override the configuration using commandline options.
    if user is not None:
        discogs_user = user

    if token is not None:
        discogs_token = token

    if git is not None:
        discogs_git = git

    if discogs_user is None:
        print("User name not supplied in either configuration or command line, exiting",
              file=sys.stderr)
        sys.exit(1)

    if discogs_token is None:
        print("Token not supplied in either configuration or command line, exiting",
              file=sys.stderr)
        sys.exit(1)

    if discogs_git is None:
        print("Git repository not supplied in either configuration or command line, exiting",
              file=sys.stderr)
        sys.exit(1)

    # verify there is a valid Git repository
    try:
        repo = dulwich.porcelain.open_repo(discogs_git)
    except dulwich.errors.NotGitRepository:
        print(f"{git} is not a valid Git repository, exiting", file=sys.stderr)
        sys.exit(1)

    redis_host = 'localhost'
    redis_port = 6379

    # first check if redis is running or not
    try:
        redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

        # check if Redis is running
        redis_client.ping()
    except redis.exceptions.ConnectionError as e:
        print("Cannot connect to Redis server", e, file=sys.stderr)
        sys.exit(1)

    # set the User Agent and Authorization header for each user request
    user_agent_string = f"DiscogsCrawlerForUser-{user}/0.1"
    headers = {'user-agent': user_agent_string,
               'Authorization': f'Discogs token={token}'
              }

    # use a (somewhat) exponential backoff in case too many requests have been made
    rate_limit_backoff = 5

    redis_list = LISTS_READ[redis_list_number]

    discogs_git_directory = discogs_git / str(redis_list_number)
    if discogs_git_directory.exists():
        pass
    else:
        discogs_git_directory.mkdir()

    current_identifier = None

    # continuously grab an identifier from Redis
    while True:
        try:
            if current_identifier is None:
                identifier = int(redis_client.lpop(redis_list))
            else:
                identifier = current_identifier
        except ValueError as e:
            print("Invalid data received from Redis server, exiting", e, file=sys.stderr)
            sys.exit(1)
        except IndexError as e:
            print(f"End, exiting: {e}", file=sys.stderr)
            sys.exit(1)

        default_sleep = 60

        try:
            # grab stuff from Discogs
            request = requests.get(f'https://api.discogs.com/releases/{identifier}',
                                   headers=headers)

            # now first check the headers to see if it is OK to do more requests
            if request.status_code != 200:
                if request.status_code == 401:
                    print("Denied by Discogs, exiting", file=sys.stderr)
                    sys.exit(1)
                elif request.status_code == 404:
                    # TODO: record discogs entries that have been removed
                    pass
                elif request.status_code == 429:
                    if 'Retry-After' in request.headers:
                        try:
                            retry_after = int(request.headers['Retry-After'])
                            print(f"Rate limiting, sleeping for {retry_after} seconds",
                                  file=sys.stderr)
                            time.sleep(retry_after)
                            sys.stderr.flush()
                        except:
                            print(f"Rate limiting, sleeping for {default_sleep} seconds",
                                  file=sys.stderr)
                            time.sleep(default_sleep)
                            sys.stderr.flush()
                    else:
                        print(f"Rate limiting, sleeping for {default_sleep} seconds",
                              file=sys.stderr)
                        time.sleep(default_sleep)
                        sys.stderr.flush()

                continue

            # in case there is no 429 response check the headers
            if 'X-Discogs-Ratelimit-Remaining' in request.headers:
                rate_limit = int(request.headers['X-Discogs-Ratelimit-Remaining'])
            if rate_limit == 0:
                # no more requests are allowed, so sleep for some
                # time, max 60 seconds
                print(f"Rate limiting, sleeping for {rate_limit_backoff} seconds", file=sys.stderr)
                sys.stderr.flush()
                time.sleep(rate_limit_backoff)

                if rate_limit_backoff < default_sleep:
                    rate_limit_backoff = min(default_sleep, rate_limit_backoff * 2)
            else:
                rate_limit_backoff = 5

            json_data = request.json()
            process_json(json_data, removes, discogs_git_directory, repo)
            current_identifier = None
        except Exception as e:
            #print(e)
            pass


if __name__ == "__main__":
    main()
