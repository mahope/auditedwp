on run
	tell application "System Events"
		tell process "Bitwarden"
			set out to ""
			repeat with e in UI elements
				set out to out & (role of e as text) & " | "
			end repeat
			return out
		end tell
	end tell
end run
