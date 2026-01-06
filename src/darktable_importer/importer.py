import sys
from lrtools.lrcat import LRCatDB, LRCatException
from lrtools.lrselectgeneric import LRSelectException
from lrtools.display import display_results
from pathlib import Path

class ImageData:
    path : str

    def __init__(self, path: str) -> None:
        self.path = path

class LRImporter:

    def __init__(self) -> None:
        pass

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

    def import_images(self, db_path: Path) -> list[ImageData]:
        # Based on example from https://github.com/fdenivac/Lightroom-SQL-tools/blob/master/README.md
        try:
            self.lrdb = LRCatDB(db_path)
        except LRCatException as _e:
            sys.exit(' ==> FAILED: %s' % _e)
        root_folder = self.lrdb.cursor.execute("select absolutePath from AgLibraryRootFolder").fetchone()[0]
        absolute_db_path = db_path.resolve()
        actual_root_folder = self.find_actual_root_path(root_folder, absolute_db_path)
        print(f"Database folder: {absolute_db_path}")
        print(f"Actual root folder: {actual_root_folder}")
        print(f"Root folder: {root_folder}")
        columns = "name=full, keywords, rating, flag,"
        criteria = ""
        try:
            rows = self.lrdb.lrphoto.select_generic(columns, criteria).fetchall()
        except LRSelectException as _e:
            sys.exit(' ==> FAILED: %s' % _e)
        result = []
        for row in rows:
            photo_path = self.fix_path(root_folder, actual_root_folder, row[0])
            print(photo_path)
            result.append(ImageData(photo_path))
        return result