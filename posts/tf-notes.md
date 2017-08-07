
## Concepts
* tensor
* tensor handle
* function library
* partial run
* TensorArray

    Class wrapping dynamic-sized, per-time-step, write-once Tensor arrays.
## Qestions
* What is the different between new api and old api?

* Why GraphDef contains a FunctionDefLibrary?
  It's experimental?

* How to generate debug version

	Add "--copt=-g" to bazel build options

    ```
    bazel build --config=opt --copt=-g //tensorflow/tools/pip\_package:build\_pip\_package
    ```

* tensorflow's runtime architecture

    * Single machine
    * Cluster


## Create Session
* Preparations
  * Search gpu device
  * many threads are created
* Code:
  * Python part <br>
    class diagram: SessionInterface <- BaseSession <- Session

    BaseSession.__init__:
    * prepare graph, config, target, and call capi TF_NewSession.<br>
      A target is a string, specifies a device, none for local machine,
      "grpc://" started string for GRPC device.

  * Core part
    * files <br>
        core/public/session.h<br>
        core/common_runtime/session.cc<br>
    * TF_NewSession (capi.cc)
        * call NewSession (session.cc)
          * get session factory

            session factory manager manages many session factories,
            and they are compared to options of NewSession call
            (if target is empty, return directSessionFactory,
            if starts with grpc://, return GRPCSessionFactory)

            if multiple factories are found, throws an error.

            for local machine, returns DirectSessionFactory
            for grpc node, returns GRPCSessionFactory

          * DirectSessionFactory->newSession
            * devices = DeviceFactory::AddDevices <br>
              prepare devices set.
            * newDirectionSession(optins, devices) <br>
              create thread pool <br>
              set client device

* Questions:
    * How many factories are there in tensorflow? <br>
        GRPCSessionFactory <br>
        DirectSessionFactory <br>

    * How are these factories registered?
        A: they use global variable's constructor to register itself.

    * What is a tensorflow execution engine?

    * given a CAPI function name, what is the internal corresponding class/methods?
        find them in capi.cc


## Session.Run()
* python part
  * BaseSession.Run()
    * serailize run_options(input), prepare run_metadata(output).
    
        it seems that data communication between core and python are mainly by 
        proto-buffers, not by direct c/c++ structures, besides some basic data structures.
    
    * call self._run
        * Validate and process feed_dict.
        * create handler to process fetches. (_FetchHandler)
        
              Given a graph, a user-provided structure for fetches, and a feed dict, this
              class takes care of generating a list of tensor names to fetch and op names
              to run for a low level `run()` call.
            
              Given the results of the low level run call, this class can also rebuild a
              result structure matching the user-provided structure for fetches, but
              containing the corresponding results.
              
            A client may want different structures of many tensors, and maybe some of them 
            are duplicated, but the core needs only a list of unique tensors, 
            fetch handler translate structures between user's and core's.
          
        * self._update_with_movers
        
            some fed tensor may be incompatible with the device, movers move tensors to compatible 
            devices. this step is only to tensors in feed_dicts. (Q: It means that a feed tensor can 
            have it's device specified?)
            
        * self._do_run
            * extend_graph
              serialize graph, transmit it to core via TF_ExtendGraph
            * call TF_Run<br>
              this turns to core part.
        * build results(fetches)

    * parse run_metadata returned from core.
    * do some cleaning stuff
* core(c/c++) part
    * TF_ExtendGraph
        parse serialized string to GraphDef, 
    * TF_Run
    
## Device Management
## SessionFactory management
## Thread pool management
## Ops management