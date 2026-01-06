import sys
from lrtools.lrcat import LRCatDB, LRCatException
from lrtools.lrselectgeneric import LRSelectException
from lrtools.display import display_results
from pathlib import Path
import zlib
import re

class ImageData:
    path : str
    id : str
    picked : bool = False
    keywords : list[str] = []

    def __init__(self, id: str, path: str) -> None:
        self.id = id
        self.path = path
        self.picked = False
        self.keywords = []

class LRImporter:

    db_path : Path

    def __init__(self, db_path: Path) -> None:
        try:
            self.db_path = db_path
            self.lrdb = LRCatDB(db_path)
        except LRCatException as _e:
            sys.exit(' ==> FAILED: %s' % _e)

    def find_actual_root_path(self, db_root_path: str, actual_db_path: Path) -> str:
        # Assumption - catalogue file is a subpath of the reported root folder
        db_parts = Path(db_root_path).parts
        last_db_part = db_parts[-1]
        
        search_path = actual_db_path.parent
        while search_path:
            print(f"Searching actual root in: {search_path}")
            if (search_path.name == last_db_part):
                return str(search_path)
            parent = search_path.parent
            if parent == search_path:
                break
            search_path = parent
        
        return str(actual_db_path.parent)

    def fix_path(self, db_root_path : str, actual_root_path : str, photo_path : str) -> str:
        if not photo_path.startswith(db_root_path):
            return photo_path
        relative_path = photo_path[len(db_root_path):]
        relative_path = relative_path.replace('\\', '/')
        fixed_path = str(Path(actual_root_path) / relative_path)
        return fixed_path

    def import_images(self) -> list[ImageData]:
        # Based on example from https://github.com/fdenivac/Lightroom-SQL-tools/blob/master/README.md
        root_folder = self.lrdb.cursor.execute("select absolutePath from AgLibraryRootFolder").fetchone()[0]
        absolute_db_path = self.db_path.resolve()
        actual_root_folder = self.find_actual_root_path(root_folder, absolute_db_path)
        print(f"Database folder: {absolute_db_path}")
        print(f"Actual root folder: {actual_root_folder}")
        print(f"Root folder: {root_folder}")
        columns = "id, name=full, keywords, flag"
        criteria = ""
        try:
            rows = self.lrdb.lrphoto.select_generic(columns, criteria).fetchall()
        except LRSelectException as _e:
            sys.exit(' ==> FAILED: %s' % _e)
        result = []
        for row in rows:
            photo_path = self.fix_path(root_folder, actual_root_folder, row[1])        
            image_data = ImageData(row[0], photo_path)
            image_data.keywords = [kw.strip() for kw in row[2].split(',')] if row[2] else []
            image_data.picked = (row[3] == 1)
            print(f"{photo_path} ID: {image_data.id} Keywords: {image_data.keywords} Picked: {image_data.picked}")
            result.append(image_data)
        return result

    def ensure_lr_namespace(self, xmp_string : str) -> str:
        lr_ns = 'http://ns.adobe.com/lightroom/1.0/'
        if 'xmlns:xmp=' in xmp_string and 'xmlns:lr=' not in xmp_string:
            xmp_string = xmp_string.replace('xmlns:xmp=', f'xmlns:lr="{lr_ns}"\nxmlns:xmp=', 1)
        return xmp_string

    def ensure_keywords_container(self, xmp_string : str) -> str:    
        # Ensure namespace exists
        new_xmp_string = self.ensure_lr_namespace(xmp_string)
        # Ensure hierarchicalSubject exists; if not, insert it before first <exif:, otherwise before the end of rdf:Description
        if '<lr:hierarchicalSubject' not in new_xmp_string:
            idx = new_xmp_string.find('<exif:')
            if idx == -1:
                idx = new_xmp_string.find('</rdf:Description>')
            if idx == -1:
                # Unexpected format, return as is
                return xmp_string
            insertion = (
            '<lr:hierarchicalSubject>\n'
            '   <rdf:Bag>\n'
            '   </rdf:Bag>\n'
            '</lr:hierarchicalSubject>\n'
            )
            new_xmp_string = new_xmp_string[:idx] + insertion + new_xmp_string[idx:]
        return new_xmp_string

    def add_keywords_to_xmp(self, xmp_string : str, keywords : list[str]) -> str:
        # Darktable adds tags the following way:
        # <lr:hierarchicalSubject>
        #     <rdf:Bag>
        #         <rdf:li>MyTag</rdf:li>
        #         <rdf:li>darktable|format|nef</rdf:li>
        #     </rdf:Bag>
        # </lr:hierarchicalSubject>  

        # Why processing is done using regexes and string manipulation?
        # XMP Toolkit library relies on native code, just returns errors and cannot be easily debugged.
        # Parsing and reassembling the XML is more invasive, I would like to avoid touching anything unless necessary.
        # There is no need to be pedantic about indentation, because Darktable needs to be launched anyway to import the images,
        # and upon opening, the XMP files are reparsed and reformatted by Darktable itself.
        if not keywords:
            return xmp_string
        new_xmp_string = self.ensure_keywords_container(xmp_string)
        items = "\n".join([f"       <rdf:li>{keyword}</rdf:li>" for keyword in keywords])

        # Insert items into first <lr:hierarchicalSubject>...<rdf:Bag> using regex
        match = re.search(
            r'(<lr:hierarchicalSubject\b[^>]*>.*?<rdf:Bag\b[^>]*>)(?P<content>.*?)(</rdf:Bag>)',
            new_xmp_string,
            flags=re.DOTALL
        )
        if match:
            prefix = match.group(1)
            content = match.group('content')
            suffix = match.group(3)
            if content.strip() == "":
                new_content = "\n" + items + "\n"
            else:
                new_content = content + items + "\n"            
            new_xmp_string = new_xmp_string[:match.start()] + prefix + new_content + suffix + new_xmp_string[match.end():]
            return new_xmp_string   
        # TODO log error
        return xmp_string

    def export_xmp(self, images: list[ImageData]) -> None:
        for image in images:
            try:
                # First (the only) column is the XMP data; why is it additionally packed in a tuple? Don't know.
                xmp_data = self.lrdb.get_xmp(image.id)[0][0]
                # Compressed XMP data is stored with a 4-byte header, skip it
                # TODO - possibly check whether there is a possibility that the data is not compressed
                xmp_data_decompressed = zlib.decompress(xmp_data[4:])
                xmp_string = xmp_data_decompressed.decode('utf-8', errors='replace')
                if image.keywords:
                    xmp_string = self.add_keywords_to_xmp(xmp_string, image.keywords)
                if image.picked:
                    xmp_string = self.add_keywords_to_xmp(xmp_string, ['picked'])
                xmp_path = Path(f"{image.path}.xmp")
                xmp_path.parent.mkdir(parents=True, exist_ok=True)
                xmp_path.write_text(xmp_string, encoding="utf-8")               
            except LRCatException as _e:
                print(f" ==> WARNING: Failed to get XMP for image {image.id}: {_e}")
       
