on run
	tell application "System Events"
		set out to ""
		set ps to every application process whose name contains "Bitwarden"
		repeat with p in ps
			set out to out & (name of p) & " bgonly=" & (background only of p as text) & linefeed
		end repeat
		return out
	end tell
end run
