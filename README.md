# epygibus
# Experimental Python Git Inspired Back Up System

As the name implies, __epygibus__ is a __git__ inspired back up system
implemented in __Python__ using nothing but the standard Python
library.
It is intended to provide a backup system that can use a
file system that may not support hard links (or has relatively slow
I/O speeds e.g. a cifs mounted network device)to efficiently store
back up files.
This will allow products such as Western Digital's
__WdMyCloud__ to be used out of the box for backup storage on a Linux
system.

The basic design comprises two (independent) components, one for
storing the contents of the files to be backed up and one for storing
snapshots.

## Content Repositories

The content of the files to be backed are stored in repositories where
their paths (a la __git__) are determined by the SHA1 hex digest of their
content. This content data is shared by multiple back up snapshots.
Consequently, a reference count for these files is maintained so that
when they are no longer referenced by any snapshots they may be deleted.

## Snapshot Archives

The series of snapshots for a defined snapshot archive are stored in
a directory (whose path is stored in archive's specification file) and
are Python __pickle__ files containing an instance of a single Python
class representing the root directory of the file tree of the files
specified in the archive's specification file for back up.  This class
contains the paths, attributes and context hex digest for each regular
file in the snapshot and similar data for directories and soft links.

The data in a snapshot together with it's associated repository is
sufficient to recreate the backed up files when required.

## Communication Between Components

To all intents and purposes, the content repository component is unaware
of the existence of the snapshot component and it concerns itself solely
with managing any content that it is given to manage.  It presents a
very simple interface to the snapshot component:

1. __store_contents__: which the snapshot generator calls with the
absolute path to a file whose contents the snapshot wishes to have
stored and gets a __token__ in return with which it stores in the
snapshot so that it can be used refer to that content in further
requests.
2. __copy_contents_to__: which the snapshot manager calls with a token
and an absolute file path as arguments and the repository manager
responds by copying the contents associated with the token into the
file specified by the path.
3. __release_contents__: which the snapshot manager calls with a list
of tokens in a snapshot when it is deleting that snapshot.
4. __open_contents_read_only__: which is called by the snapshot manager
with a token as its argument and gets a read only Python __file__ object
giving it access to the contents.
5. __get_content_storage_stats__: which is called by the snapshot manager
with a token as its argument and returns the amount of disk space the
content is currently occupying and the number of tokens currently issued
for that content.  This is used to generate statistics that can be used
to demonstrate how efficient the back system is. The size returned here
may be different to its original size as the content repository is at
liberty to compress content for storage if it is so directed.

## User Interface

At this point in time, the only available user interface is via the
command line (but a GUI is in the forward planning) and it provides
sub commands to:

1. create repositories
2. create snapshot archives (which are essentially a specification file
for a snapshot series)
3. create a snapshot for an archive
4. extract files or directories from the latest (or a specified)
snapshot within a specified archive and copy them to the current
working directory (or a specified directory)
4. restore specified files or directories (or the whole snapshot) from
the latest (or a specified) snapshot within a specified archive.
5. delete the oldest (or a specified) snapshot form a specified archive
6. prune unreferenced content from a specified content repository.

There are also sub command for looking at various statistics.

Run:

```
epygibus --help
```

for more details.

## Installing __epygibus__.

It is __not__ necessary to install __epygibus__ as it can be run
directly from the source tree's base directory (or anywhere else,
if that directory is in your PATH).
