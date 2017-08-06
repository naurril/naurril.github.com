
## Concepts
    * tensor
    * tensor handle
    * function library
    * partial run
## Qestions
* What is the different between new api and old api?

* Why GraphDef contains a FunctionDefLibrary?
  It's experimental?

## Session.Run()
* python part
  * BaseSession.Run()
    * serailize run_options(input), prepare run_metadata(output).
    
        it seems that data communication between core and python are mainly by 
        proto-buffers, not by direct c/c++ structures, Besides some basic data structures.
    
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
            * call TF_Run
              
              this turns to core part.
        
        * build results(fetches)        
        
    * parse run_metadata returned from core.
    * do some cleaning stuff
 
* core(c/c++) part
    * TF_ExtendGraph
        parse serialized string to GraphDef, 
    * TF_Run
    