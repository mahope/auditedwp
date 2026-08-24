tell application "System Events"
  tell process "Bitwarden"
    set wc to count of windows
    set out to "windows: " & wc
    repeat with w in windows
      try
        set out to out & linefeed & (name of w)
      end try
    end repeat
    return out
  end tell
end tell
