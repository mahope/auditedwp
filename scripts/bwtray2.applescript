on run
	tell application "System Events"
		tell process "Bitwarden"
			set mbi to menu bar item 1 of menu bar 2
			set out to ""
			try
				repeat with e in UI elements of mbi
					set out to out & (role of e as text) & " | "
				end repeat
			end try
			try
				set out to out & "AXPress=" & ((value of attribute "AXPress" of mbi) as text)
			end try
			return "desc=" & (description of mbi as text) & " role=" & (role of mbi as text) & " elems=[" & out & "]"
		end tell
	end tell
end run
