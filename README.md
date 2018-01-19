### ArchiveSpace tools

parse_marc.py does the following:

* Takes single EOS-exported MARC XML consisting of one or more records and splits it into single MARC XML files, named with the call number of the item, and with the namespaces ASpace expects.
* Cleans up lots of punctuation!
* If there are multiple extents in the 300 field (e.g., "1 box (0.25 linear ft.)"), separates them out so they import as discrete extents in ASpace.
* If "ALS" is in 245 subfield k, adds a 500 note of "Autograph letter signed."
* If there is no date in control field 008, and also no date in 245 subfield f or g, adds a subfield f of "undated." This prevents records with no date from throwing an error during import.