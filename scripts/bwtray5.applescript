on run
	tell application "System Events"
		tell process "Bitwarden"
			set mb to menu bar 2
			set mbi to menu bar item 1 of mb
			set out to "name=" & (name of mbi as text) & " desc=" & (description of mbi as text)
			click mbi
			delay 2
			-- after click, look for any window or AXMenu anywhere
			try
				repeat with e in UI elements
					set out to out & linefeed & (role of e as text)
				end repeat
			end try
			return out & linefeed & "windows=" & (count of windows as text)
		end tell
	end tell
end run
