# crawler_for_discogs

Crawler for the Discogs database that downloads data via the Discogs API and
stores it as (sorted) JSON in a Git repository.

## Design

Each release in Discogs has a release number. The crawling queue is a Redis
queue containing the release numbers for which the release data needs to be
fetched by workers.

As soon as a worker has fetched a release number it downloads the relevant
data via the Discogs API in JSON format. The JSON data is then cleaned up to
remove irrelevant data such as:

* `num_for_sale`
* `lowest_price`
* some fields in the `community` field

and possibly some other fields in the data as well that are not relevant to
the release itself, or irrelevant to data quality:

* `estimated_weight`
* `videos`

The JSON is then sorted, written to a file and added to a Git repository.

Processing scripts could then take the data in the Git repository and process
the data.

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

The Discogs database consists of many files (more than 28M if artists, labels
and other data is also taken into account). There might be performance issues.
A solution could be to use Git submodules and use multiple repositories instead
of a single one.

## Preseeding the queue

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
output file:

```
$ python3 discogs_xml_split.py -d ~/discogs-data/discogs_20231001_releases.xml.gz -r /tmp/september2023-hashes.txt
....
```

The output should be redirected to a file which can then be processed further.
It should be noted that the current implementation will run for many hours. As
this script is typically only run once per month this is acceptable.

# References

1. <https://vinylanddata.blogspot.com/2017/11/how-sparse-is-discogs.html>
2. <https://data.discogs.com/>
