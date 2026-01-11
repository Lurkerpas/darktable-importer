# darktable-importer
NOTE: Project will not be further developed

Simple importer of photo collections into darktable. For more about darktable, an open source photography workflow application, please visit https://www.darktable.org/ Please note that the project and the author are not affiliated in any way with the darktable project.

# rationale
The purpose of this application was to allow importing of existing Lightroom catalogues into darktable, preserving basic metadata, like ratings, colors, pick flags, and, hopefully, basic edits like cropping or orientation. The app is a success in the sense that it allowed me to better understand how Lightroom and darktable handle metadata. The app is also... a useful learning experience, as it does not and will not achieve its desired outcome. To my surprise, it is not the fault of Lightroom - the data is neatly organized, and while it is originally stored in a proprietary database, the database itself is actually SQLite. Thanks to Lightroom SQL Tools (https://github.com/fdenivac/Lightroom-SQL-tools), all data can be easily extracted into the XMP sidecars, that are standardized way to store image metadata. Whatever is expressed in custom tags, could be translated into other custom or standard tags...
However, due to various issues with darktable, I decided that further development does not make sense.

# usage
Install via: `make install`

Launch:
Type `darktable-importer --help` for CLI documentation.
Type `darktable-importer --input MyCatalogue.lrcat --xmp` to launch darktable with an import script.
Type `darktable-importer --input MyCatalogue.lrcat --xmp --donotlaunch` to just extract the XMP sidecars.