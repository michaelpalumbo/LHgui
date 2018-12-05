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
const lodash = require('lodash')

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

let sessionId = 0;
let sessions = [];
// list which clients are editing a particular file:
let filesOpen = [];

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

var find = require('list-files');
 


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
  
  session.socket.send(JSON.stringify({
    session: session.id,
    date: Date.now(),
    type: "filesInUse",
    value: filesOpen,
    // filesOpen: filesOpen
  }));
  // session.id.send('source',sourceCode)
  // send_all_clients('source',sourceCode)
  // console.log(sourceCode)

  // function sendSource(ast, session) {
    // session.socket.send(JSON.stringify({
    //   session: session.id,
    //   date: Date.now(),
    //   type: "source",
    //   value: sourceCode
    // }));
  // }

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

    case "freeFilename":
    console.log(filesOpen)
    lodash.pull(filesOpen, msg.filename)
    console.log(filesOpen)
    send_all_clients(JSON.stringify({
      session: session.id,
      date: Date.now(),
      type: "filesInUse",
      value: filesOpen,
      // filesOpen: filesOpen
    }))

    case "update":
      console.log(msg.message, msg.sourceCode)
      fs.writeFileSync(script, msg.sourceCode)
    break;

    case "getFile":
      console.log(msg.filename)
      //console.log(SessionID)
      // check if file is currently in use by another editor:
      if (lodash.some(filesOpen, msg.filename)

      ) {
        //In the array!
        console.log('in the array')
        // lodash.chain(filesOpen)
        // .find({id: sessionId})
        // .merge({file: msg.filename});
        // console.log(filesOpen)

    } else {
        console.log('Not in the array')

        filesOpen.push(msg.filename)
        // lodash.chain(filesOpen)
        // .find({id: sessionId})
        // .merge({file: msg.filename});
        console.log(filesOpen)
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
}

