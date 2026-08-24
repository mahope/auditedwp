on run
	tell application "System Events"
		tell process "Bitwarden"
			set mb2 to menu bar 2
			return count of menu bar items of mb2
		end tell
	end tell
end run
