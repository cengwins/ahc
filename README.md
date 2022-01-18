# Introduction to the Ad Hoc Computing (AHC) Framework

Communication engineers are specialised in digital communications and networking technologies, whereas computer engineers or application developers are mostly specialised in software engineering with no or minimal background in the communication domain. With the introduction of virtualisation and softwarization, networks have become programmable that requires knowledge from both telecommunication and computer engineering domains. We have to fill the gap between these two domains to address the challenges of future networks. The main objective of the AHC project is to develop a distributed computing and learning environment on wireless networks employing software-defined radios. There are many simulators, emulators, and test-beds for researching networks or event-driven concurrent programming tools of distributed algorithms. However, there is a need for a tool that helps researchers integrate distributed algorithms considering the specifics of wireless networks. The tool has to incorporate wireless channel characteristics, packet collisions, contention-based channel access, forward- and backward-error correction, topology management, multi-hopping, or end-to-end reliable data transport and many other issues related to wireless communication and networking. 

The overall goal of the AHC project is to develop an open-source education and research software framework that facilitates the development of distributed algorithms on wireless networks considering the impairments of wireless channels. The framework will be used as a learning and prompt-prototyping tool. 

## Objectives
The specific objectives are
- Creating web-based education tools for teaching and learning distributed systems, networks, and communication,
- Abstraction of the intricate details of the digital communication discipline from networking or distributed computing domains,
- Creating easy-to-understand and accessible educational materials about wireless networks,
- Providing hands-on opportunities for learning these technologies, inside of the classroom and out,
- Facilitating a framework to invent new technologies,
- Improving existing open-source digital communications technologies,
- Creating a remote simulation environment by using web-based tools for getting more realistic, real-world experiment results,
- Creating simulation configurations dynamically so that users will be able to run simulations by meeting specific requirements of projects. 

## Users

The users of the AHC framework will be students, teachers, researchers and engineers working in the fields of digital communication, networking or distributed computing. The developed framework will be available to all these user groups as open-source software. 

# Design

In this section, we present the details of the ad hoc computing library (AHC) library and algorithms thereof following an asynchronous event-driven composition model.  The AHC library is being implemented in Python language, and the software is provided as open-source at [https://github.com/cengwins/ahc](https://github.com/cengwins/ahc).  The basic abstraction of AHC is a component, which is a single-threaded automaton. In other words, a component is a single-threaded process implemented in python where the thread waits on a queue for accepting input events from other components. Each component has a name and an instance number. The name and the instance number together uniquely represent each component instance. A component is an event-driven active process that waits for an input event. From this perspective, a component is an automaton. 

Each component has a separate eventhandlers dictionary (hash table) to which the event handlers are added on the initialization of the component. The component model automatically adds the "init" event to the eventhandlers dictionary. Note that the name of the event is "init" and the function that will handle the "init" event is onInit. The constructor of the component model executes the following.
- initializes the eventhandlers dictionary. This dictionary allows us to develop generic component models and automata. 
- adds the default events (initialize, messagefromtop, messagefrompeer) to the event handlers. After all the components are created and initialized, the onInit function of all components will be triggered with the INIT event in a single shot. The default onInit implementation is a fake function. If the extended component does not implement it, the default onInit method will be called.
- creates an input queue. Each component has a single input queue that will be used by the connected components or the component itself to trigger events. 
- initializes the connectors that allow us to connect components for composing complex models. Although a developer may use other techniques for connecting components to each other, the default method for composition is to follow a stack architecture on which we will further elaborate in the sequel. 
- adds itself to the ComponentRegistry which is a singleton class that keeps track of all instantiated components. The ComponentRegistry can be used globally to find a component in the composition.
- finally creates the thread that will listen to the input queue for input events. The queuehandler function is going to handle the events and call the associated event handler. It is possible to extend the component model to further implement various queue handlers.
 
Although the number of threads that will listen to the queue is set to one by default, it can be changed by the developer; notice that the order of the events per component may change if more one than one thread is employed. If an event is inserted in the input queue of a component, the thread of the component is automatically triggered to fetch events from the queue on a first-come-first-served basis. Events are defined with a basic data structure.

An event is generated by a component that becomes the source of that event. The component reference is stored in the eventsource member of the Event class. The event member defines the event. Each component has to declare its component event type enumeration if events beyond the defaults will be used.

Eventhandlers keep the association between the event and its handler function. The eventhandlers dictionary has to be populated with component-specific events on the initialization of the component instance. Using the eventhandler dictionary, the queuehandler determines the member function which is going to be invoked by the thread that runs the component. Note that events are enumerations. Event creation time is stored in the time member. The content that will be carried from one component to another inside the event is the eventcontent member. Event contents are, in general, the messages the peering components exchange although any content is allowed in the implementation.

The queuehandler is a simple function that fetches the event ahead of the queue that is passed as a parameter to itself, gets the event name from the event object, associates the event with the event handler by a lookup in the eventhandlers dictionary, and then calls the event handler by passing the event as the parameter. The triggerevent function is used by components to put events into the input queue of a component. For any event evt, the handler is the function “onEvt” where the eventobj of class Event is the sole parameter.

Components are stacked to construct a complex component. Since we follow a stack hierarchy, every component will have a reference to zero or more components on top or bottom of itself. Components can be connected to other components at the same layer as peers. The references to other components are called connectors. Components send each other events through connectors. There is a many-to-many relationship among components. A component has three connectors by default: "UP", "DOWN", and "PEER".  The "UP" and "DOWN" connectors refer to the component that resides at the immediate higher or immediate lower layers, respectively. The "PEER" connector is used to communicate to other components at the same layer.  Any complex component can be implemented out of simpler components by following this composition mechanism without any limitation on the depth.

Components invoke each other using sendup, senddown, and sendpeer functions. When these functions are called, all of the components associated with the designated connector receive the event. If the component does not implement the associated event handler with the event, then the event is silently discarded for that component. Multiplexing is not employed; components are supposed to take actions by implementing the designated event or by implementing the multiplexing feature by some field defined in the eventcontent field. 

The topology of the to-be-experimented wireless network is generated using the Networkx Python package. In an experimentation model, there will be nodes that are connected over some channels. The DOWN connector of nodes is linked to the channels. Channels do not employ the default connector types. The unique identifiers (name concatenated with the instance number) are employed as connector names in channels. 

A topology may consist of one or more nodes (or components). To invoke the INIT event for all instantiated components, the start function of the Topology class has to be invoked. Then, the main thread has to loop forever. 

There are several ways for creating a topology. In general, NetworkX graph generation methods are used to create a graph that will be provided as an input parameter to the constructFromGraph function of the  Topology class. This is a very powerful method since the NetworkX package handles many graph generators. For each node, components of type nodetype are created and for each edge in the graph, a channel of type channeltype is created and the components are connected to that channel.

The eventcontent field of the Event class is a generic member. Anything can be provided as event content. However, in this project, we assume the wireless network model that will be experimented with is a packet switching network where a store-and-forward mechanism is employed. Although the typical approach of implementing separate physical addresses at the link layer and network-specific addresses at the network layer can be implemented over this design, we will generally use the componentinstancenumber as the unique address of a node. Inside a node, if a developer requires unique addressing of components, the unique identifier of components, that is component name and number together, can be used.

The generic message structure is a simple one. Messages have headers following the GenericMessageHeader class and payloads following the GenericMessagePayload class. Messages can be encapsulated using this structure. Messages can be multiplexed and demultiplexed using the messagetype field. In other words, create a message, put the other message in the payload, and tag this message with another type. This structure allows us to design generic networking stacks. The other fields of the header are self-descriptive. 

The Channel class is an extension of the component model. In other words, a channel is also a component that is significantly overwritten. The generic channel model has two additional event types: INCH and DLVR. As an extension of the component model, the constructor first calls the constructor of the super. Then, it adds the channel-specific event handlers. The channel model adds two additional queues to the input queue, namely, they are the input and the output queues. 

Channels have three pipeline stages. The messagefromtop event handler is the first pipeline stage. The inchannel event handler is the interim pipeline stage and the deliver event handler is the final (output) pipeline stage. All pipeline stages have separate queues with separate threads; a typical channel has three threads. Messages that are transmitted over channels can be, among others, dropped, replicated, modified,  or delayed. Such phenomena can be incorporated into extended channel models using these three pipeline stages. A developer may revolve an event over the same pipeline stage several times if required. The default deliver event handler, delivers the event that carries a message to all of the components that are connected to the channel. In short, the default channel model is a broadcast channel with no losses or duplicates.

Although the order of the messages generated by the same component can be preserved, the order of messages generated by different components may change since the pipeline stages are handled by separate threads that depend on the process scheduling of the employed operating system.

As the channel specific-event handlers propagate the event to the subsequent pipeline stage, they keep the eventsource intact. We do not let channels put their references as the eventsource, to make channels transparent to the components.  A developer has to employ the same approach when the channel models are extended. Furthermore, the triggerevent function puts the events into the input queue by default. Since channels have multiple queues, we do not invoke the triggerevent function. The events are inserted into the queues directly. 

As we have already described, the lowest-layer component's down connector is connected to the node model and the down connector of the node model is connected to a channel. In the reverse direction, the channels have separate connector types for all components that are connected to themselves and those connectors are references to the unique identifier of the connected component.




<!-- CONTACT -->
## Contact

Ertan Onur - [@ertan10r](https://twitter.com/Ertan10r) - eronur@metu.edu.tr
