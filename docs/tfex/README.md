# A proposal for a flexible time and frequency link data exchange format.

## Context

There is currently no standard format for exchanging time or frequency link data. Most of the time it is simple enough so that implicit conventions allow to understand the content (e.g. first column = some sort of timetag, second column = value in units that seems natural to both the data producer and the data consumer). Metadata is then implicit or embedded in the file name, or written in free form as a header (again, with some implicit choices on what a header is).

This is a proposal for a standardized yet flexible format for T&F data exchange, based on our current practices.

## Design goals

- Format should be human readable and editable. This rules out binary formats, which does not appear to be an issue for small datasets such as the ones we usually exchange and read/write. Large database would not be adapted to be serialized this way.
- Some metadata needs to be imbedded in the file. We would like to use nested lists and dictionaries so that it is possible to embed complex information
- It should as much as possible conform to existing syntax, to avoid reinventing the wheel.
- The general idea is to use this exchange format as an output of the software producing time or frequency comparisons with any method, and then as input and output for further processing (i.e. chaining links, smoothing, cleaning, clipping, comparing, etc...). This would then allow to build a toolbox operating on this, relying on the embedded metadata pour perform certain operations.
- This is developped by the BIPM Time department as a possible help for internal software development. But the aim is to make it available to NMIs and more generally the T&F community.

## Structure of the file (as of v0.2)

The above considerations lead to the choice of a text-based file, encoded as UTF-8, with termination LF (0x0A). 

### Header

The header starts at the first line of the file. Each line begins with the character "\#" (0x23). It ends at the first line not beginning with "\#".

When stripped from its first character, the strings form a valid TOML (https://toml.io) encoding. A list of mandatory and optional keywords is allowed :

Mandatory:

- TFEXVER: a string containing the version of TFEX format, e.g. `0.2`
- COLUMNS: a list of dictionaries describing each column of the file through the label of data ('label', unique), unit ('unit', using the prefix above to resolve to a PID for a known digital representation of units), format descriptor ('format'). Optional attribute 'timetag', if set to 'true', identifies columns used to date the data points (as opposed to values). It is then possible to specify the scale used (UTC by default). The optional 'trip' descriptor combines REFPOINTS (see below) to indicate what link is used. Type 'flag' should have an associated set of values ('possible\_values').

Strongly recommended:

- PREFIX: a dictionary of string:URI pointing to ontologies, e.g. `{'si': 'https://si-digital-framework.org/SI/units/'}`

Optional:

- MJDSTART: a float representing the start of the period covered by the file, in MJD (UTC tiem scale)
- MJDSTOP: a float representing the end of the period covered by the file, in MJD (UTC timescale)
- NDATA: an integer representing the number of data points in the file
- SAMPLING\_INTERVAL\_s: a float representing the sampling interval separating each data point, in second
- AVERAGING\_WINDOW\_s: a float representing the period during which data has been averaged for each data point, in second (if AVERAGING\_WINDOW\_s = SAMPLING\_INTERVAL\_s, the duty cycle is 100%)
- MISSING\_EPOCHS: a boolean stating if the file lacks some epochs ("True") or if it is a continuous succession of timetags. The idea is to provide a way to trust that 2 files with identical MJDSTART, MJDSTOP, SAMPLING\_INTERVAL\_s and MISSING\_EPOCHS=False can be compared line-to-line without interpolation.
- AUTHOR: a string identifying the author
- REFPOINTS: a list of dictionaries describing each (time) reference point by an ID label ('id'), a reference time scale ('ts'), a device ('dev'), a device type ('type'). These reference points will be used in the COLUMNS field to identify the link corresponding to the value. E.g. `[{'id': 'A', 'ts': 'UTC(NICT)', 'dev': 'NICT01', 'type': 'TW'},{'id': 'B', 'ts': 'UTC(PTB)', 'dev': 'PTB05', 'type': 'TW'}]`.
- CONSTANT\_DELAYS: a list of dictionary that associates to specific links a constant delay (useful for calibration, or for applying arbitrary offsets for comparison purposes). E.g. `[{trip = ['ED'], unit = "si:nanosecond", value = 102.7, type = "TOTDLY"}]` 
- COMMENT: a string for comments. There should be only one "COMMENT" record, but multiline comment is accepted (through TOML syntax).

### Data

Data starts just after the header. Empty lines are ignored. The width of each column is set by the width in the "COLUMNS" header, the ordering is the same as in the list, columns are separated by a space character (0x20). Non-values are represented by the character "\*". Otherwise the representation of the value must be parsable using the format string provided in the COLUMNS header. 

### Authorized sets of timetags

One aim of TFEX is to provide flexibility on input and output timetags, providing tools to convert to and from most common formats. Detection is based on the list of "labels" assigned to each column carrying "timetag: true".

- `['MJD', 'SoD']`: the column identified by "MJD" contains an integer representing the MJD, and "SoD" contains an integer or a float (according to its "format" field) representing the number of seconds elapsed since midnight of the corresponding MJD.


# Example of TFEX file generated from a TSOFT output

```
# TFEXVER = 0.3
# PREFIX = { si = 'https://si-digital-framework.org/SI/units/'}
# AUTHOR = BIPM
# REFPOINTS = [
#   { id = 'A', ts = 'Unknown', dev = 'OP3', type = 'GPSPPP'},
#   { id = 'B', ts = 'Unknown', dev = 'PT3', type = 'GPSPPP'},
# ]
# COLUMNS = [
#   {timetag = true, label = 'MJD', scale = 'utc', unit = 'si:day', format = '5d'},
#   {timetag = true, label = 'SoD', scale = 'utc', unit = 'si:second', format = '5d'},
#   {label = 'delta_t', label = 'link', trip = ['AB'], unit = 'si:nanosecond', format = '8.3f'},
# ]
# COMMENT = 
60547   281   -1.421 
60547   582   -1.434 
60547   882   -1.465 
60547  1181   -1.508 
60547  1481   -1.530 
60547  1781   -1.530 
60547  2082   -1.539 
60547  2382   -1.532 
60547  2681   -1.557 
60547  2981   -1.567 
60547  3282   -1.555 
```
