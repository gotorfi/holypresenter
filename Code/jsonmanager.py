import json
import os

class JsonManager:
    def __init__(self, filepath="savecloud/galleries/playlists.json"):
        self.filepath = filepath

    def save(self, playlists, slides, songs, images):
        data = {
            "playlists": playlists,
            "slides": slides,
            "songs": songs,
            "images": images
        }
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load(self):
        if not os.path.exists(self.filepath):
            return {"playlists": [], "slides": [], "songs": [], "images": []}

        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "playlists": data.get("playlists", []),
                "slides": data.get("slides", []),
                "songs": data.get("songs", []),
                "images": data.get("images", [])
            }