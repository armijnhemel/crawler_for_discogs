#! /usr/bin/env python3

#-*- coding: utf-8 -*-

# SPDX-License-Identifier: Apache-2.0
# Licensed under Apache 2.0, see LICENSE file for details

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

# process json: cleanup, sort, compare to already stored version
def process_json(json_data, removes, git_directory, repo, remove_thumbnails=True):
    for r in removes:
        try:
            if '/' in r:
                key1, key2 = r.split('/', 1)
                del json_data[key1][key2]
            else:
                del json_data[r]
        except KeyError:
            pass

    if remove_thumbnails:
        for artist in json_data['artists']:
            try:
                del artist['thumbnail_url']
            except KeyError as e:
                pass
        for artist in json_data['extraartists']:
            try:
                del artist['thumbnail_url']
            except KeyError as e:
                pass
        for company in json_data['companies']:
            try:
                del company['thumbnail_url']
            except KeyError as e:
                pass
        for label in json_data['labels']:
            try:
                del label['thumbnail_url']
            except KeyError as e:
                pass
        for label in json_data['series']:
            try:
                del label['thumbnail_url']
            except KeyError as e:
                pass
        for track in json_data['tracklist']:
            if 'artists' in track:
                for artist in track['artists']:
                    try:
                        del artist['thumbnail_url']
                    except KeyError as e:
                        pass
            if 'extraartists' in track:
                for artist in track['extraartists']:
                    try:
                        del artist['thumbnail_url']
                    except KeyError as e:
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
@click.option('--config-file', '-c', required=True, help='configuration file (YAML)', type=click.File('r'))
@click.option('-v', '--verbose', is_flag=True, help='Enable debug logging')
@click.option('-g', '--git', help='Location of Git repository (override config)', type=click.Path('exists=True', path_type=pathlib.Path))
@click.option('-u', '--user', help='User name (override config)')
@click.option('-t', '--token', help='Token (override config)')
@click.option('-l', '--list', 'redis_list_number', type=click.IntRange(min=1, max=39), required=True, help='Redis list number (1-39)')
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
                for r in config['fields']['remove']:
                    removes.append(r)
    except (YAMLError, PermissionError, UnicodeDecodeError) as e:
        print(f"Cannot open configuration file, exiting, {e}", file=sys.stderr)
        sys.exit(1)

    # override the configuration using commandline options
    if user is not None:
        discogs_user = user

    if token is not None:
        discogs_token = token

    if git is not None:
        discogs_git = git

    if discogs_user is None:
        print(f"User name not supplied in either configuration or command line, exiting", file=sys.stderr)
        sys.exit(1)

    if discogs_token is None:
        print(f"Token not supplied in either configuration or command line, exiting", file=sys.stderr)
        sys.exit(1)

    if discogs_git is None:
        print(f"Git repository not supplied in either configuration or command line, exiting", file=sys.stderr)
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

    redis_list = REDIS_LISTS[redis_list_number]

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
            r = requests.get(f'https://api.discogs.com/releases/{identifier}', headers=headers)

            # now first check the headers to see if it is OK to do more requests
            if r.status_code != 200:
                if r.status_code == 401:
                    print(f"Denied by Discogs, exiting", file=sys.stderr)
                    sys.exit(1)
                elif r.status_code == 404:
                    # TODO: record
                    pass
                elif r.status_code == 429:
                    if 'Retry-After' in r.headers:
                        try:
                            retry_after = int(r.headers['Retry-After'])
                            print(f"Rate limiting, sleeping for {retry_after} seconds", file=sys.stderr)
                            time.sleep(retry_after)
                            sys.stderr.flush()
                        except:
                            print(f"Rate limiting, sleeping for {default_sleep} seconds", file=sys.stderr)
                            time.sleep(default_sleep)
                            sys.stderr.flush()
                    else:
                        print(f"Rate limiting, sleeping for {default_sleep} seconds", file=sys.stderr)
                        time.sleep(default_sleep)
                        sys.stderr.flush()

                continue

            # in case there is no 429 response check the headers
            if 'X-Discogs-Ratelimit-Remaining' in r.headers:
                rate_limit = int(r.headers['X-Discogs-Ratelimit-Remaining'])
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

            json_data = r.json()
            process_json(json_data, removes, discogs_git_directory, repo)
            current_identifier = None
        except Exception as e:
            print(e)
            pass


if __name__ == "__main__":
    main()
