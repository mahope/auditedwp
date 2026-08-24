on run
	tell application "System Events"
		tell process "Bitwarden"
			set mbi to menu bar item 1 of menu bar 2
			click mbi
			delay 1.5
			set out to ""
			try
				repeat with mi in menu items of menu 1 of mbi
					set out to out & (name of mi as text) & linefeed
				end repeat
			on error errMsg
				set out to "ERR: " & errMsg
			end try
			return out
		end tell
	end tell
end run
