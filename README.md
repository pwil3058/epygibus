# epygibus - Experimental Python Git Inspired Back Up System

The purpose of __epigybus__ is to provide a backup system that can use a
file system that does not support hard links to efficiently store
back up files.  This will allow products such as Western Digital's
__WdMyCloud__ to be used out of the box for backup storage on a Linux
system.  Inspired by __git__, it achieves this by storing the contents
of the files to be backed up and their directory tree separately.

## Content Repositories

The content of the files to be backed are stored in a repository where
their paths (ala __git__) are determined by the SHA1 hex digest of their
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

By making the assumption that if the modification time and size of a
file being backed up is the same as that in the previous snapshot then
the content is unchanged considerable reductions in the time to take
a snapshot are achieved (approximately 1 order of magnitude).  There
is a __--paranoid__ option on the __bu__ subcommand to turn off this
feature.
