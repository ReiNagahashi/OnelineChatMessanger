# Overview
This project implements real-time chat using both UDP and TCP communication.

1. Message transmission utilizes UDP, allowing for quick and simple implementation.
   - Since UDP is connectionless, the system tracks the time of the last message sent by each client and automatically exits them from the chat room if they exceed a certain time limit.
2. Chat rooms for specific users are implemented using TCP communication.
3. Users have the option to set a password when creating a chat room. This requires other users to input the password when joining the chat room.

## Key Points in this Project
1. Sockets are manipulated in non-blocking mode to concurrently receive requests from clients using both TCP and UDP socket types (specifically using the Python select library).
2. Clients can select multiple functionalities, such as messaging, creating chat rooms, and joining chat rooms, through commands on the CLI.
