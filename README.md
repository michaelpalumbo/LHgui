# LHgui
gui / interface for lasg/pbai workshop2018...

<!-- #CLI
'run' - start the luddyLaptopMaster.py script
'stop' - kills the luddyLaptopMaster.py process
'quit' - kills the luddylaptopmaster.py process before stopping server -->


#todo
DONE need to free up a file if a client isn't using it anymore
DONE allow viewing currently opened files, but prevent others from editing these (make these read-only in codemirror)
  --- allow auto-switching to a branch in a new worktree if someone does want to work on a 'locked file'

webRTC notify all clients with other clients' activity

- a way to mark a file that you're not working on but lock it away: i don't want anyone touching this while i'm working on this other file. 
  --- auto-switch to a branch in a new worktree if someone does want to work on a 'locked file'
- seeing which client is working on which file (also add in usernames?)