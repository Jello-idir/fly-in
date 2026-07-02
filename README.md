*This project has been created as part of the 42 curriculum by aait-idi*

<h1 style="
color: #FFFFFF;
font-family: 'DepartureMono Nerd font';
font-size: 50px;
font-weight: 800">
FLY-iN
</h1>

<img
src="docs/fly-in.png"
/>

<h2 style="
color: #FFFFFF;
font-size: 24px;
font-weight: 800">
Description
</h2>

the project - as you read in the above section - is about navigating multiple drones through connected hubs while respecting hubs max drone capacity and connections max link capacities as efficent as possible, don't worry if you got confused already :] ill explain everything in details.

<p1 style="
color: #FFFFFF;
font-weight: bold">
Quick Overview:
</p1>
<p1 style="color: #ffffff; font-family: 'DepartureMono Nerd font';">
you provide a map file with the number of drones, hubs and connections between them and the program will display a window with a visual representation of the hubs and connections, then it will start moving the drones from the start hub to the end hub while respecting the max capacities of hubs and connections.
<p2>

---

# Resources

in this section, I will explain the main components of this project and their purpose, then I'll talk about how to run it and how to use it.

`-hub.`\
<img
src="docs/hub.png"
width="100"
/>

    a hub is a place where drones can land and take off, it has a maximum capacity of drones it can hold at any given time, and it can be connected to other hubs through links.`
---

`-drone.`\
<img
src="docs/drone.png"
width="100"
/>

    a drone is a flying vehicle that can move between hubs, it has a unique identifier and a color.

---

`-link.`\
<img
src="docs/connection.png"
width="200"
/>

    a link is a connection between two hubs, it has a maximum capacity of drones that can travel through it at any given time.

---

`-config.toml.`\
<img
src="docs/config_file.png"
/>

    config file: this is just a normal config.toml file at the root of this project, it configurations how the displayed window will look, more details below.

---

`-map_file.`\
<img
src="docs/map_file.png"
/>

    map file: also at the root and it's called "put_your_map_here.txt", this is where you put the number of drones and hub names, location, color and other metadata, read docs/map_file.md for syntax and more details.

---


# Instructions section containing any relevant information about compilation installation, and or execution.


# Algorithm choice and implementation strategy

# documentation for my visual representation and features and how they enhance user experience
