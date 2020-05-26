# Multiship
A multiplayer game in Python created using the pygame and socket modules.

# Copyright and License
This software was developed by Ewan Brinkman and is available under the GNU General Public License.

# How to Run
- Run the file called server.py first. You will need to be connected to your local internet for this to work. If it successfully starts, it will print out your local IP address, and the server will be running.
- Now, open up the file settings.py. There will be a bunch of variables. The first one should be called SERVER_IP. Replace the IP address already here with you local IP address (the one that printed out when server.py started.
- Now, you can start as many instances of client.py as you want. Make sure you choose a unique username every time you connect to the server. Also, it should automatically be set to connect to your local IP address if you replaced the IP address in settings.py in the previous step.
- When you want the client.py to quit, press the Escape key to exit. If you were connected to the server, press it a second time to quit the program.

# Creating a Standalone Application
On a Mac, run the file setupApp.py in the terminal using: python setup.py py2app