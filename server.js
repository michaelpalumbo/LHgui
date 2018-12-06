//Michael: next thing TODO: see near bottom of document for case "code":
const express = require('express');
const WebSocket = require('ws');
const http = require('http');
const url = require('url');
const fs = require("fs");
const path = require("path");
const os = require("os")
// const { exec, execSync, spawn, spawnSync, fork } = require('child_process')
const terminal = require("web-terminal");
const ip = require('ip')
// const shell = require('vorpal')();
const lodash = require('lodash')
var find = require('list-files');
var cpuu = require('cputilization');
var vitals = require('vitals');




const project_path = path.join(__dirname + '../../17540-Luddy-Hall/Master Laptop/');
const server_path = __dirname;
const client_path = path.join(server_path, "client");
console.log("project_path", project_path);
console.log("server_path", server_path);
console.log("client_path", client_path);

// var script = path.join(project_path, 'LuddyLaptopMaster.py')

// global for python script process ID
var MasterLaptopPID
console.log('=*=*=*=*=*=\nThis machine\'s public IP is ' + ip.address() + '\n*=*=*=*=*=*=')

let sessionId = 0;
let sessions = [];
// list which clients are editing a particular file:
let filesOpen = [];
let sessionData = {};

const app = express();
app.use(express.static(client_path))
app.get('/', function(req, res) {
	res.sendFile(path.join(client_path, 'index.html'));
});
//app.get('*', function(req, res) { console.log(req); });
const server = http.createServer(app);
// add a websocket service to the http server:
const wss = new WebSocket.Server({ server });


//////////////// file browser ///////////////////
//  exec('node ' + __dirname + '/node_modules/file-browser/index.js -p 8089', {cwp: '../../17540-Luddy-Hall'})


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
  console.log(sessionData)
	console.log("server received a connection, new session " + session.id);
  console.log("server has "+wss.clients.size+" connected clients");
  session.socket.send(JSON.stringify({
    session: session.id,
    date: Date.now(),
    type: "filesInUse",
    value: filesOpen,
    // filesOpen: filesOpen
  }));

  find(function(result) {
    // console.log(result);
    //=> './dirname/a.js'
    //=> './dirname/b.js'
    session.socket.send(JSON.stringify({
      session: session.id,
      date: Date.now(),
      type: "files",
      value: result
    }));
}, {
    dir: '../17540-Luddy-Hall',
    // name: 'js'
    exclude: '*.git*'
});
	
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
    // update the filesOpen array
    // lodash.pull(filesOpen, sessionFilename)
    delete sessionData[session.id];
    delete sessions[session.id];
    // console.log(Object.values(sessionData));

    filesOpen = [];
    for (var k in sessionData) { 
      filesOpen.push(sessionData[k]);
  }
    send_all_clients(JSON.stringify({
      session: session.id,
      date: Date.now(),
      type: "filesInUse",
      value: filesOpen,
      sessionData: sessionData
    }))
    console.log(sessionData)
    console.log('\n\n\nnum sessions = ' + wss.clients.size)

    if (wss.clients.size === 0){
      //clean up filesOpen list if all clients close...
      filesOpen = [];
    }
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

terminal(terminalApp);


///////////////////// APP LOGIC /////////////////////


function handleMessage(msg, session) {
	
	switch (msg.type) {

    case "userName":
    // sessionData[msg.userName] = session.id
    break;
    case "freeFilename":
    console.log("\n\nnum sessions: " + wss.clients.size)
    console.log(filesOpen)
    lodash.pull(filesOpen, msg.filename)
    console.log(filesOpen)
    send_all_clients(JSON.stringify({
      session: session.id,
      date: Date.now(),
      type: "filesInUse",
      value: filesOpen,
    }))

    break;

    case "update":
      fs.writeFileSync(msg.filename, msg.sourceCode)
      console.log('\n\n',msg.fileName, ' WRITTEN')
      console.log('if git gets integrated, use this: ' + msg.message)
    break;

    case "getFile":
      console.log(msg.filename)
      //console.log(SessionID)
      // check if file is currently in use by another editor:
      if (lodash.some(filesOpen, msg.filename)) {
        // if currently in use don't add it again to the array...
    } else {
        // if not in use, add filename to array
        filesOpen.push(msg.filename)
        sessionData[session.id] = msg.filename;
        console.log(sessionData)
    }     
      
      sourceCode = fs.readFileSync(path.join(msg.filename), 'utf-8')
      //console.log(sourceCode)
      console.log('source code from ', msg.filename, ' loaded!')
      sourceCode = JSON.stringify(sourceCode)

      // function sendSource(ast, session) {
        session.socket.send(JSON.stringify({
          session: session.id,
          date: Date.now(),
          type: "source",
          value: sourceCode,
          // filesOpen: filesOpen
        }));

        // console.log('line229 send clients that: ' + filesOpen)
        send_all_clients(JSON.stringify({
          session: session.id,
          date: Date.now(),
          type: "filesInUse",
          value: filesOpen,
          // filesOpen: filesOpen
        }))
    break;

    case 'getFileReadOnly':

    console.log(msg.filename)
    //console.log(SessionID)
    // check if file is currently in use by another editor:
    
    sourceCode = fs.readFileSync(path.join(msg.filename), 'utf-8')
    //console.log(sourceCode)
    console.log('source code from ', msg.filename, ' loaded!')
    sourceCode = JSON.stringify(sourceCode)

    // function sendSource(ast, session) {
      session.socket.send(JSON.stringify({
        session: session.id,
        date: Date.now(),
        type: "sourceRead-Only",
        value: sourceCode,
        // filesOpen: filesOpen
      }));

      // session.socket.send(JSON.stringify({
      //   session: session.id,
      //   date: Date.now(),
      //   type: "filesInUse",
      //   value: filesOpen,
      //   // filesOpen: filesOpen
      // }));

    break;


  }
 
var sampler = cpuu({interval: 2000});
 
sampler.on('sample', function(sample) {
  cpuBusy = 100 * sample.percentageBusy()

  send_all_clients(JSON.stringify({
      date: Date.now(),
      type: "diagnostics",
      cpuBusy: cpuBusy,

      // filesOpen: filesOpen
    }))

});


}




