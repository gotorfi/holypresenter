import json
import os
from paths import resource_path, data_path
from pathlib import Path

class JsonManager:
    def __init__(self, filepath="savecloud/galleries/playlists.json"):
        self.filepath = data_path(filepath)

    def save(self, playlists, slides, songs, images):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

        if os.path.exists(self.filepath):
            try:
                import shutil
                shutil.copy(self.filepath, self.filepath + ".bak")
            except:
                pass

        data = {
            "playlists": playlists,
            "slides": slides,
            "songs": songs,
            "images": images
        }

        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        self.cleanup_unused_images()

    def load(self):
        if not os.path.exists(self.filepath):
            return {"playlists": [], "slides": [], "songs": [], "images": []}

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return {"playlists": [], "slides": [], "songs": [], "images": []}

        return {
            "playlists": data.get("playlists", []),
            "slides": data.get("slides", []),
            "songs": data.get("songs", []),
            "images": data.get("images", [])
        }

    def cleanup_unused_images(self):
        data = self.load()
        used_files = set()
        for playlist in data.get('playlists', []):
            for slide in playlist.get('slides', []):
                for element in slide.get('elements', []):
                    if 'path' in element:
                        path_str = element['path']
                        path = Path(path_str)
                        if 'slideimages' in path_str:
                            used_files.add(path.name)
        image_folder = Path(__file__).resolve().parent / "savecloud" / "slideimages"
        if image_folder.exists():
            for file_path in image_folder.iterdir():
                if file_path.is_file() and file_path.name not in used_files:
                    file_path.unlink()