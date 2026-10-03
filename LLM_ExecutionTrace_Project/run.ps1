param(
    [Parameter(ValueFromRemainingArguments=$true)]
    $RemainingArgs
)

& C:\Users\gsadaramodu\.local\bin\python3.14.exe main.py @RemainingArgs
