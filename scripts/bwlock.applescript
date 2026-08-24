on run
	tell application "System Events"
		tell process "Bitwarden"
			click menu item "Lås boks" of menu 1 of menu bar item "Bitwarden" of menu bar 1
		end tell
	end tell
	delay 8
	tell application "System Events"
		tell process "Bitwarden"
			return "windows=" & (count of windows as text)
		end tell
	end tell
end run
