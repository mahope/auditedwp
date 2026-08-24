on run
	tell application "System Events"
		tell process "Bitwarden"
			set out to ""
			set mbs to every menu bar
			repeat with mb in mbs
				set out to out & "MENUBAR: "
				repeat with mbi in menu bar items of mb
					set out to out & (name of mbi as text) & " / "
				end repeat
				set out to out & linefeed
			end repeat
			return out
		end tell
	end tell
end run
