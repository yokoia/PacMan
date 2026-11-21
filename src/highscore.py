import json


class HighscoreManager:
    """Manage and save the game's highscore."""

    def __init__(self, filename: str = "highscores.json") -> None:
        self.filename = filename
        self.scores: list[dict[str, str | int]] = []

    def load_highscores(self) -> None:
        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            self.scores = []
            return

        except (OSError, json.JSONDecodeError, UnicodeError) as error:
            print(f"Error loading highscore: {error}")
            self.scores = []
            return

        if not isinstance(data, list):
            print("Invalid Hisghscore file format")
            self.scores = []
            return

        valid_scores: list[dict[str, str | int]] = []

        for entry in data:
            if not isinstance(entry, dict):
                continue

            name = entry.get("name")
            score = entry.get("score")

            if (
                isinstance(name, str)
                and 1 <= len(name) <= 10
                and name.strip()
                and name.isascii()
                and all(char.isalnum() or char == " " for char in name)
                and type(score) is int
                and score >= 0
            ):
                valid_scores.append({
                    "name": name,
                    "score": score
                })
        valid_scores.sort(
            key=lambda entry: int(entry["score"]),
            reverse=True
        )
        self.scores = valid_scores[:10]

    def save_highscores(self) -> None:
        """Save highscores to a JSON file."""
        try:
            with open(self.filename, "w", encoding="utf-8") as file:
                json.dump(self.scores, file, indent=4)
        except OSError as error:
            print(f"Error saving highscores: {error}")

    def add_score(self, name: str, score: int) -> bool:
        """Validate and add a new player score."""

        if not isinstance(name, str):
            print("Invalid name type")
            return False

        if not isinstance(score, int):
            print("Invalid score type")
            return False

        if not 1 <= len(name) <= 10:
            print("Invalid name length")
            return False

        if not name.strip():
            print("Invalid name")
            return False

        if not name.isascii():
            print("Invalid name characters")
            return False

        if not all(char.isalnum() or char == " " for char in name):
            print("Invalid name characters")
            return False

        if score < 0:
            print("Invalid score")
            return False

        new_entry: dict[str, str | int] = {
            "name": name,
            "score": score
        }

        self.scores.append(new_entry)

        self.scores.sort(
            key=lambda entry: int(entry["score"]),
            reverse=True
        )
        self.scores = self.scores[:10]

        self.save_highscores()

        return True
