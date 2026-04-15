import json
import os
from paths import resource_path, data_path
from pathlib import Path

class JsonManager:
    def __init__(self, filepath="galleries/playlists.json"):
        self.filepath = data_path(filepath)

    def _clean_element(self, el):
        """Remove non-serializable widget references from element"""
        return {k: v for k, v in el.items() if k != "ref"}

    def _clean_slide(self, slide):
        """Remove non-serializable widget references from slide"""
        new_slide = {}
        for k, v in slide.items():
            if k == "elements" and isinstance(v, list):
                new_slide["elements"] = [self._clean_element(e) for e in v]
            else:
                new_slide[k] = v
        return new_slide

    def _clean_show(self, show):
        """Remove non-serializable widget references from show"""
        new_show = show.copy()
        if "slides" in show and isinstance(show["slides"], list):
            new_show["slides"] = [self._clean_slide(s) for s in show["slides"]]
        return new_show

    def _clean_playlists(self, playlists):
        """Remove non-serializable widget references from all playlists"""
        clean = []
        for pl in playlists:
            new_pl = pl.copy()
            if "slides" in pl and isinstance(pl["slides"], list):
                new_pl["slides"] = [self._clean_show(s) for s in pl["slides"]]
            clean.append(new_pl)
        return clean

    def save(self, playlists, slides, songs, images):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

        if os.path.exists(self.filepath):
            try:
                import shutil
                shutil.copy(self.filepath, self.filepath + ".bak")
            except:
                pass

        # Clean widget references before saving
        clean_playlists = self._clean_playlists(playlists)
        clean_slides = [self._clean_slide(s) for s in slides] if slides else []

        data = {
            "playlists": clean_playlists,
            "slides": clean_slides,
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