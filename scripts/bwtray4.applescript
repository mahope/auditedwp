on run
	tell application "System Events"
		tell process "Bitwarden"
			set mbi to menu bar item 1 of menu bar 2
			perform action "AXPress" of mbi
			delay 2
			set out to ""
			try
				repeat with w in windows
					set out to out & (name of w as text) & linefeed
				end repeat
			end try
			return "windows after press: [" & out & "] count=" & (count of windows as text)
		end tell
	end tell
end run
