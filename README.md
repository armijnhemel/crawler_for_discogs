# crawler_for_discogs

Crawler for the Discogs database that downloads data via the Discogs API and
stores it as (sorted) JSON in a Git repository.

## Design

Each release in Discogs has a release number. The crawling queue is a Redis
queue containing the release numbers for which the release data needs to be
fetched by workers. Note: the dependency on Redis will likely be replaced soon
because of the recent Redis license change.

As soon as a worker has fetched a release number it downloads the relevant
data via the Discogs API in JSON format. The JSON data is then cleaned up to
remove data that is not directly related to the data describing a release:

* `num_for_sale`
* `lowest_price`
* some fields in the `community` field which are also available via another
  API endpoint:
  * `have`
  * `want`
  * `rating`

and possibly some other fields in the data as well that are not relevant to
the release itself, or irrelevant to data quality:

* `estimated_weight`
* `videos`
* `thumbnail_url` (in various fields)

The JSON is then sorted, written to a file and added to a Git repository if the
(cleaned up) contents have changed, or if the release is new.

Processing scripts could then take the data in the Git repository and process
the data. Some potential uses:

* sanity checking to see if the data is actually correct (are the right fields
  used, is there potentially data missing, and so on)
* notification scripts for a certain artist, label, country, and so on, either
  per update or as a "daily digest"

### Why store in Git?

There are a few good reasons to store files in Git, instead of in a regular
database:

1. it is distributed: multiple clients can download and manipulate files at
   the same time
2. processing scripts only need to keep track of the latest revision they
   looked at and then find out which of the files have been changed (as this
   will be the releases that were changed), for example using:
   `$ git diff --name-only <REVISION>..HEAD`

#### Git drawback: race conditions

Git works fine, as long as the workers are not working on the same files at
the same time. There are a few ways that this can be prevented, for example by
segmenting the data set and having different crawlers focus on a single segment
(for example: a block of 2 million releases), by working in branches and
periodically merging these branches, or by making sure that the same release
isn't scheduled immediately again after it has been removed from the queue, and
by forcing clients to make sure that their copy is up to date before adding
something. This doesn't necessarily prevent race conditions but it will make
it easier to manage.

#### Git drawback: size

The Discogs database consists of many files (more than 31M if artists, labels
and other data is also taken into account). There might be performance issues.
A solution could be to use Git submodules and use multiple repositories instead
of a single one.

## Preseeding the crawling queue

Not every number is in use, and some of the release numbers have disappeared
or were never used[1]. Adding every number (from 1 to the latest one known) to
the queue therefore doesn't make sense.

The Discogs XML dumps[2] contain a fairly up to date list of which release
numbers are in use. This list will not be current: release numbers are retired
every now and then (but never added!) due to merges and deletions and new data
is being added to the catalog continuously. The latest dump (if made, as
sometimes the dump files are incomplete or missing for a month) will be at
most a bit over 35 days old.

Optionally there can be several optimisations to avoid that entries that
haven't been changed are queued again. This can for example be done by
computing a hash of the XML data and comparing it to a stored hash and only
queuing the entry if the hashes are different.

The script `discogs_xml_split.py` can process files and writes the release
number and SHA1 in a tab separated format (release number and SHA1 hash) to an
output file, for example:

```
$ python3 discogs_xml_split.py -d -d ~/discogs-data/discogs_20240201_releases.xml.gz -r ~/discogs-data/february_2024_release_numbers_and_hashes.txt
```

It should be noted that the current implementation will run for quite some
time:

```
$ time python3 discogs_xml_split.py -d ~/discogs-data/discogs_20240201_releases.xml.gz -r ~/discogs-data/february_2024_release_numbers_and_hashes.txt

real	158m24.965s
user	157m39.111s
sys	0m10.797s
```

although this also depends on your Linux and Python installation.

As this script is typically only run once per month this is acceptable.
Optimizations are likely possible but remember that the XML file that is
processed is very big (at least 12 GiB gzip compressed) so it is important to
take memory usage into account: creating a full DOM representation in memory is
impossible. A first version of the splitter script used `xml.dom.pulldom` which
has very low memory usage but which isn't the fastest. The current version
uses `xml.etree.ElementTree` which is a lot faster.

What is important to know is that the XML that is used for computing the hash
is the XML as written by `ElementTree's` `tostring()` method. It is *not* byte
for byte identical to the original XML. This means that when comparing the
output of two different Discogs dump files they should be prcessed with the
same script using the same libraries.

The next step is actually seeding the releases that need to be crawled into
the Redis queue. This can be done using the `discogs_queue_seeder.py` script,
for example:

```
$ python3 discogs_queue_seeder.py -n /tmp/discogs_september2023_hashes.txt
```

The script takes two parameters (one optional):

1. path to list of new release number/hash combinations (mandatory)
2. path to list of already known (old) release number/hash
   combinations (optional)

Both lists should be generated with `discogs_xml_split.py`. If both parameters
are provided only release numbers in the new list that were either added or
changed (different hash) are written to Redis. If only one parameter is
provided all release numbers from the list are written to Redis.

To make it easier to distribute the work across multiple workers the releases
numbers are put in different lists in Redis and a crawler will only look at
a single list.

## Crawling the data

The `crawler_for_discogs.py` continuously grabs release numbers from a Redis
queue, downloads the JSON data using the Discogs API, removes unnecessary
elements and stores the data in a Git repository if the data is new or has
changed.

Each crawler is configured to use a specific Redis list. The seeder script
puts releases into specific lists depending on the number: the first 1M
releases are stored in a list, the next 1M releases are stored in the next
list, and so on.

Example:

```
$ python3 crawler_for_discogs.py -c config.yaml -u bla -t bla-token -g /tmp/git -l 14
```

The parameters are:

* configuration file (in YAML)
* Discogs user name (if not provided in the configuration file)
* Discogs token (if not provided in the configuration file)
* path to Git repository (if not provided in the configration file)
* Redis list number (1-99)

Currently both the Git repository and the Redis queue are assumed to be local
but this will eventually be changed so the crawlers can be distributed and
using different locations for crawling.

# References

1. <https://vinylanddata.blogspot.com/2017/11/how-sparse-is-discogs.html>
2. <https://data.discogs.com/>
