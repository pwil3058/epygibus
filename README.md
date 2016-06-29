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

## Setting __epygibus__ Up For Use.

### Creating a Content Repository

The first thing that needs to be done is create a content repository:

```
epygibus new_repo --location=<directory path> <repository name>
```

will create a directory with path `<directory path>/epygibus.d/repos/<user name>/<repository name>`
and initialize a lock file and reference count file in that directory.
To refer to this repository in future __epygibus__ <repository name>
should be used.  By default, file content will be stored in compressed files
(using gzip) in the repository. The `-U` option to the above command would
override this default cause them to be created uncompressed.  This
option only effects the way the content files are __created__ and they
may be compressed/uncompressed at any time using:

```
epygibus compress [-U] -R <repository name>
```

without effecting __epygibus__ functionality.

### Creating a Snapshot Archive

Once a content repository has been created, it is now possible to
create snapshot archives and the command:

```
epygibus new --location=<directory path> -I <file/directory path> -R <repository name> -A <archive name>
```

will create a directory with path
`<directory path>/epygibus.d/snapshots/<hostname>/<user name>/<archive name>`
and <archive name> should be used to identify this archive and its
snapshots with __epygibus__ commands.  For example, after the above
command:

```
epygibus bu -A <archive name>
```

would cause a snapshot to be taken of the file or directory
identified by `<file/directory path>` and placed in the directory mentioned
above with the contents of any files being stored separately in the
`<repository name>` content repository.  If `<file/directory path>` is a
symbolic link then both the link and its target will be included in the
snapshot but within included directories symbolic links are not followed.

By default, the snapshot will be compressed (using gzip) but this
default behaviour can be altered by giving the `-U` option to the `new`
command.  As for repositories, existing snapshots can be compressed/uncompressed
using:

```
epygibus compress [-U] -A <archive name> [--back=N]
```

without effecting __epygibus__ functionality where the `--back` argument
specifies which snapshot (`N` before the latest snapshot, default `0`) should be
compressed/uncompressed.

Also by default, back up snapshots would skip any broken symbolic links
encountered but this behaviour can be overridden by using the
`--keep_broken_soft_links` option to the `new` command above.

Multiple `-I` arguments can be used with the `new` command to specify
multiple files or directories for inclusion in the back up snapshots.
Also, there are options for specifying files/directories (using blob expressions)
that should be excluded  from snapshots (see `epygibus new -h` for details).

The files/directories to be included/excluded in an existing archive's
snapshots can be changed using the command:

```
epygibus edit (--includes | --excluded_dirs | --excluded_files) -A <archive name>
```

which will open the editor specified by the `EDITOR` environment variable
(or `vi` if that variable is not set) on the file containing the
specification of the files/directories to be included, the glob
expressions describing directories to be excluded or the glob expressions
describing files to be excluded according to the option specified.

## Managing a Snapshot Archive and Its Snapshots.

As already mentioned, back up snapshots are created using the `bu` sub command.
The essential signature for this command is:

```
epygibus [--stats] [--quiet] [-U|-C] -A <archive_name> [-A <another_archive_name>]
```

and it should be noted that it will accept multiple `-A` arguments to
allow a single command to make multiple snapshots which will be created
in the given order. As part of the experimental nature of this project
commands such as `bu` gather statistics on their performance and these
will be displayed if the `--stats` option is specified.  The `--quiet`
option will turn off the reporting of skipped broken symbolic links.
The `-U` and `-C` can be used to override the archive's default
compression setting and cause this snapshot to be uncompressed or
compressed respectively.

### Deleting a Snapshot

The `del` sub command is provided as a mechanism for deleting an
archives snapshots.  Its essential signature is:

```
epygibus del [--remove_last_ok] [--back N] -A <archive-name>
```

and by default (as a safety measure) it will not delete a snapshot
if it is the only existing snapshot for the specified archive but
this behaviour can be overridden by using the `-remove_last_ok` option.
By default, if no `--back` option is specified, the __oldest__ snapshot
belonging to the specified archive will be deleted.  The argument to the
`--back` option can a __positive__ integer specifying how far back from
the __newest__ snapshot the desired snapshot to be deleted is (i.e. `--back=1` will
chose the second __newest__ for deletion and `--back=0` will select the
newest) or a __negative__ integer to select relative to the oldest
snapshot starting with `-1` for the oldest (i.e. `--back=-1` will select
the __oldest__ snapshot, `--back=-2` will select the second oldest, etc.)

### Listing Available Snapshots

The `lss` command is provided for getting a list of an archive's current
snapshots and its essential signature is:

```
epygibus lss [--newest_first] [--build_stats | --storage_stats] -A name
```

and without any optional arguments it will list the "names" of the
snapshots in order of creation (use `--newest_first` to reverse this order).
The "name" of a snapshot is a 19 character
date time group (DTG) string indicating the time (UTC/GMT) at which the snapshot
was made (e.g. "2016-06-14-00-57-11" would be the name of a snapshot taken
at 57 minutes and 11 seconds after midnight on the 14th June 2016) and
in conjunction with name of the archive to which it belongs should form
a unique identifier for the snapshot.  The name will be decorated with
a "**" if its file is compressed.

If the `--build_stats` is specified the `**` decoration will be replaced
with the creation statistics for each snapshot and the `--storage-stats`
will give statistics for the current storage being used by the snapshots.
These are useful for evaluating the time/space efficiency of the snapshots.

### Restoring a File or Directory from a Snapshot

The command `restore` is provided to restore a file, a directory or a
full snapshot and its signature is:

```
epygibus restore -A <archive_name> [--back N] (--file <path> | --dir <path> | --all)
```

where `--back` works the same as for previously described for
selecting which snapshot to use and
the __newest__ snapshot will be used if the `--back` option is omitted.

### Extracting a File or Directory from a Snapshot

The command `extract` is provided to extract a copy of a file or directory
from a snapshot and its signature is:

```
epygibus extract -A <archive_name> [--back N] (--file <path> | --dir <path>) [--into_dir <path>] [--with_name <name>] [--overwrite]
```

where `--back` works the same as for previously described for
selecting which snapshot to use and
the __newest__ snapshot will be used if the `--back` option is omitted.

By default, the copy of the file or directory will be placed in the
current working directory unless otherwise specified with the `--into_dir <path>`
option.  The `--with_name` option can be used to change the __name__ of the
extracted file or directory if desired.

Because of the danger of accidental overwriting of existing files or
directories `extract` will fail if it detects such a case but the
`--overwrite` option can be used to override this behaviour and overwrite
existing files and directories where necessary.
