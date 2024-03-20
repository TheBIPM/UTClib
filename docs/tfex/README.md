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

