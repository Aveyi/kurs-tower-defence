extends Node
## Current play session (autoload "Session"): the chosen level and saved best results.

const PROGRESS_PATH := "user://progress.cfg"
## Levels shown on the level select screen, in order. An empty path is a level still in development.
const LEVELS: Array[Dictionary] = [
	{path = "res://data/levels/level_01.tres"},
	{path = ""},
]

## Level to start when the game scene opens (null: the scene's own default).
var level: LevelData
## Automated tests switch this off so they do not overwrite the player's results.
var record_results := true


## Best result for a level: {victory: bool, lives: int, max_lives: int} or empty if never finished.
func best_result(level_id: StringName) -> Dictionary:
	var config := ConfigFile.new()
	config.load(PROGRESS_PATH)
	return config.get_value("best", level_id, {})


func record_result(played: LevelData, victory: bool, lives: int) -> void:
	if not record_results:
		return
	var best := best_result(played.id)
	var better: bool = best.is_empty() or (victory and not best.victory) or (victory == best.victory and lives > best.lives)
	if not better:
		return
	var config := ConfigFile.new()
	config.load(PROGRESS_PATH)
	config.set_value("best", played.id, {victory = victory, lives = lives, max_lives = played.lives})
	config.save(PROGRESS_PATH)


## 0..3 stars: a victory gives one, keeping most of the lives gives up to three.
static func stars(result: Dictionary) -> int:
	if result.is_empty() or not result.victory:
		return 0
	var ratio := float(result.lives) / maxf(result.max_lives, 1.0)
	return 3 if ratio >= 0.8 else 2 if ratio >= 0.4 else 1
