# Brewing Controller

## Structure of the repository
The main `BrewingController.py` is the main executable for the program. In the same directory are several auxiliary python files that handle other functions of the program such as controlling SQL requests, the relays, LEDs and or the temperature sensor

## Gitub Guide
Changes attempted to be made to a file are stashed until the file is committed.
Stashed changes discarded (`drop`), or applied with stash deleted (`pop`), or applied without deletion (`apply`)
There is a commited version which is not the same as the one in the folder
`Git Status` - to name of branch, what has changed in this branch
`Git checkout <branch name>` - to switch branch (its a tree)
`Git <command> --help` to get help
`Git stash list` - to see what is in it
`Git add <file>` - to flag a version that is currently in the folder, ready for committing (staged)
`Git commit` - add the changes into the git tree

## Tasks to do
Add temperature sensor into controller
Select GPIO for outputs
Setup cron job
Change allreadings to NAS
Add fields into NAS SQL
Interface Brew Controller with NAS batch data
Develop web page	- trend
					- setup buttons
					- space for taste notes
Add error checking into controller
Place orders for	- enclosure
					- flex
					- breadboard
					- fermenter seal
					- LEDs
					- Temperature readout
					
