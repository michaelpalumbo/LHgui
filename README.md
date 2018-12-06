#LHgui
gui / interface for lasg/pbai workshop2018...

<!-- #CLI
'run' - start the luddyLaptopMaster.py script
'stop' - kills the luddyLaptopMaster.py process
'quit' - kills the luddylaptopmaster.py process before stopping server -->


#todo
DONE need to free up a file if a client isn't using it anymore
DONE allow viewing currently opened files, but prevent others from editing these (make these read-only in codemirror)
  --- allow auto-switching to a branch in a new worktree if someone does want to work on a 'locked file'

?webRTC notify all clients with other clients' activity

- a way to mark a file that you're not working on but lock it away: i don't want anyone touching this while i'm working on this other file. 
  --- auto-switch to a branch in a new worktree if someone does want to work on a 'locked file'
- seeing which client is working on which file (also add in usernames?)

- Node-RED RPi stats(!!!): https://www.npmjs.com/package/node-red-contrib-device-stats
#diagnostics page
- all devices checked in with the laptop at set interval
  -- this info gets transfered to the server; flags if device didn't check in. 
- cpu usage
- ram usage
- network diagnostics 
- main python script's speed (loops per second?)
- see npmjs package 'vitals' for per-PID diagnosticing. Runs on Windows & Unix!

#public_web_GUI (hosted on different port, but accessible from LHGUI)
- mute
- volume
- start
- stop
- modes: 
  opening mode (release show)
  test mode (self test, show one-by-one elements in system)

#Sim/Viz
- matt has mentioned 
philip's questions:

#communicating between MQTT and Tavola/Encephalo?
tangible examples in this workshop? 

#two themes:
##resilience
##modularity
  - exposing the namespace of all devices!
    - i.e. what are the handshakes?

Rob mentioned they rewrote the code for each installation. 

microsoft onenote?

software in the memory of the studio. 

lexicon of what we are talking about. 

1st sentence can stand on its own -- precise identifier. Nested into this is a paragraph that identifies the scope, what it contains (this paragraph should be able to stand on its own)
  - basecamp and github integration
## be generous in hooks and pointers 