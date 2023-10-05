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

and then it is sorted.

After that it is written to a file and added to a Git repository.

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


# References

[1] <https://vinylanddata.blogspot.com/2017/11/how-sparse-is-discogs.html>
[2] <https://data.discogs.com/>
