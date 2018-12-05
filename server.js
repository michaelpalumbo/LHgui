//Michael: next thing TODO: see near bottom of document for case "code":
const express = require('express');
const WebSocket = require('ws');

const http = require('http');
const url = require('url');
const fs = require("fs");
const path = require("path");
const os = require("os");
const { exec, execSync, spawn, spawnSync, fork } = require('child_process')
const terminal = require("web-terminal");
const ip = require('ip')
const shell = require('vorpal')();

//process.chdir(process.argv[2] || ".");
const project_path = path.join(__dirname + '../../17540-Luddy-Hall/Master Laptop/');
const server_path = __dirname;
const client_path = path.join(server_path, "client");
console.log("project_path", project_path);
console.log("server_path", server_path);
console.log("client_path", client_path);

var script = path.join(project_path, 'LuddyLaptopMaster.py')

// global for python script process ID
var MasterLaptopPID
console.log('=*=*=*=*=*=\nThis machine\'s public IP is ' + ip.address() + '\n*=*=*=*=*=*=')
/*
switch (process.argv[2]){
  case "run":

        const masterLaptop = spawn('python3', [script]);
        const MasterLaptopPID = masterLaptop.pid
        console.log('\niperf pid', MasterLaptopPID)
        console.log('\n=*=*=*=*=*=*=*=*=*=*=*=*=*=\nIMPORTANT: \nplease type "end" + Enter, instead of "crtl-c" to exit this script!\n=*=*=*=*=*=*=*=*=*=*=*=*=*=\n' )
        // use this to exit the script using 'end'.
        shell
        .command('quit', 'Outputs "closing server session".')
        .action(function(args, callback) {
            // ensure LuddyLaptopMaster.py stops running in background
            exec('kill ' + MasterLaptopPID)
            // exit script
            console.log(`exiting... wait a few seconds\n\nstopping pid ${MasterLaptopPID}`);
            setTimeout(function(){
            console.log(`\n\npid kill ${MasterLaptopPID} complete\n`);
            process.exit()
        }, 2000);

        });
        // show masterLaptop shell cmd
        shell
        .delimiter('masterLaptop$')
        .show();

        shell
        .command('stop', 'Outputs "stopping luddyLaptopMaster.py".')
        .action(function(args, callback) {
            // ensure LuddyLaptopMaster.py stops running in background
            exec('kill ' + MasterLaptopPID)
            // exit script
            console.log(`exiting... wait a few seconds\n\nstopping pid ${MasterLaptopPID}`);
            setTimeout(function(){
            console.log(`\n\npid kill ${MasterLaptopPID} complete\n`);
        }, 2000);

        });
        // show masterLaptop shell cmd
        shell
        .delimiter('masterLaptop$')
        .show();

        
        masterLaptop.stdout.on('data', (data) => {
            console.log(`stdout: ${data}`);
        });
      
        masterLaptop.stderr.on('data', (data) => {
            console.log(`stderr: ${data}`);
        
        });
        
        masterLaptop.on('close', (code) => {
            console.log(`child process exited with code ${code}`);
        });
  break;

  default: console.log('\n\nserver started without running LuddyLaptopMaster.py\n\n')
}

*/

        // console.log('\n=*=*=*=*=*=*=*=*=*=*=*=*=*=\nIMPORTANT: \nplease type "end" + Enter, instead of "crtl-c" to exit this script!\n=*=*=*=*=*=*=*=*=*=*=*=*=*=\n' )
        // // use this to exit the script using 'end'.
        // shell
        // .command('quit', 'Outputs "closing server session".')
        // .action(function(args, callback) {
        //     // ensure LuddyLaptopMaster.py stops running in background
        //     exec('kill ' + MasterLaptopPID)
        //     // exit script
        //     console.log(`exiting... wait a few seconds\n\nstopping pid ${MasterLaptopPID}`);
        //     setTimeout(function(){
        //     console.log(`\n\npid kill ${MasterLaptopPID} complete\n`);
        //     process.exit()
        // }, 2000);

        // });
        // // show masterLaptop shell cmd
        // shell
        // .delimiter('masterLaptop$')
        // .show();

        // shell
        // .command('stop', 'Outputs "stopping luddyLaptopMaster.py".')
        // .action(function(args, callback) {
        //     // ensure LuddyLaptopMaster.py stops running in background
        //     exec('kill ' + MasterLaptopPID)
        //     // exit script
        //     console.log(`exiting... wait a few seconds\n\nstopping pid ${MasterLaptopPID}`);
        //     setTimeout(function(){
        //     console.log(`\n\npid kill ${MasterLaptopPID} complete\n`);
        // }, 2000);

        // });

        // // show masterLaptop shell cmd
        // shell
        // .delimiter('masterLaptop$')
        // .show();

        // shell
        // .command('run', 'Outputs "starting luddyLaptopMaster.py".')
        // .action(function(args, callback) {
        //     // ensure LuddyLaptopMaster.py stops running in background
        //     // exec('kill ' + MasterLaptopPID)
        //     // exit script

        //   const masterLaptop = spawn('python3', [script]);
        //   const MasterLaptopPID = masterLaptop.pid
        //   console.log('\python script pid', MasterLaptopPID)
          
        //   masterLaptop.stdout.on('data', (data) => {
        //       console.log(`stdout: ${data}`);
        //   });
        
        //   masterLaptop.stderr.on('data', (data) => {
        //     console.log(`stderr: ${data}`);
        //       // show masterLaptop shell cmd
        //     shell
        //     .delimiter('masterLaptop$')
        //     .show();
            
        //     }), 1000;
              
        //   masterLaptop.on('close', (code) => {
        //     console.log(`child process exited with code ${code}`);
        //   });                  

        //   masterLaptop.on('close', (code) => {
        //     console.log(`child process exited with code ${code}`);
        //   });

        //   });
        // // show masterLaptop shell cmd
        // shell
        // .delimiter('masterLaptop$')
        // .show();

var sourceFile = 'LuddyLaptopMaster.py'

var sourceCode = fs.readFileSync(path.join(project_path, sourceFile), 'utf-8')
//console.log(sourceCode)
console.log('source code from ', sourceFile, ' loaded!')
 sourceCode = JSON.stringify(sourceCode)
// console.log(JSON.stringify(sourceCode))


let sessionId = 0;
let sessions = [];

const app = express();
app.use(express.static(client_path))
app.get('/', function(req, res) {
	res.sendFile(path.join(client_path, 'index.html'));
});
//app.get('*', function(req, res) { console.log(req); });
const server = http.createServer(app);
// add a websocket service to the http server:
const wss = new WebSocket.Server({ server });

// send a (string) message to all connected clients:
function send_all_clients(msg) {
	wss.clients.forEach(function each(client) {
		client.send(msg);
	});
}

// whenever a client connects to this websocket:
wss.on('connection', function(ws, req) {
    // it defines a new session:
	let session = {
		id: sessionId++,
		socket: ws,
	};
	sessions[session.id] = session;
	console.log("server received a connection, new session " + session.id);
  console.log("server has "+wss.clients.size+" connected clients");
  
  // session.id.send('source',sourceCode)
  // send_all_clients('source',sourceCode)
  // console.log(sourceCode)

  // function sendSource(ast, session) {
    session.socket.send(JSON.stringify({
      session: session.id,
      date: Date.now(),
      type: "source",
      value: sourceCode
    }));
  // }
	
	const location = url.parse(req.url, true);
	// You might use location.query.access_token to authenticate or share sessions
	// or req.headers.cookie (see http://stackoverflow.com/a/16395220/151312)

	
	ws.on('error', function (e) {
		if (e.message === "read ECONNRESET") {
			// ignore this, client will still emit close event
		} else {
			console.error("websocket error: ", e.message);
		}
	});

	// what to do if client disconnects?
	ws.on('close', function(connection) {
		console.log("session", session.id, "connection closed");
		delete sessions[session.id];
	});
	
	// respond to any messages from the client:
	ws.on('message', function(e) {
		//console.log(e)
		if(e instanceof Buffer) {
			// get an arraybuffer from the message:
			const ab = e.buffer.slice(e.byteOffset,e.byteOffset+e.byteLength);
			console.log("session", session.id, "received arraybuffer", ab);
			// as float32s:
			console.log(new Float32Array(ab));
		} else {
			// get JSON from the message:
			try {
				let msg = JSON.parse(e);
				console.log("session", session.id, "received JSON", msg);
				handleMessage(msg, session);

			} catch (e) {
				console.log('bad JSON: ', e);
			}
		}
	});

	// // Example sending binary:
	// const array = new Float32Array(5);
	// for (var i = 0; i < array.length; ++i) {
	// 	array[i] = i / 2;
	// }
	// ws.send(array);
});

server.listen(8080, function() {
	console.log('server listening on %d', server.address().port);
});

// HTTP SERVER for Terminal:
var terminalApp = http.createServer(function (req, res) {
  res.writeHead(200, {"Content-Type": "text/plain"});
  res.end("Hello World\n");
});

// terminalApp.listen(1337);
// console.log("Server running at http://127.0.0.1:1337/");

terminal(terminalApp);


///////////////////// APP LOGIC /////////////////////


function handleMessage(msg, session) {
	
	switch (msg.type) {

    case "update":
      console.log(msg.message, msg.sourceCode)
      fs.writeFileSync(script, msg.sourceCode)
    break
		// case "get_source": {
		// 	send_all_clients('source?',sourceCode)
		// }
		// break;
		
	}
}