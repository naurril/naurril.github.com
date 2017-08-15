
## Concepts
* tensor
* tensor handle
* function library
* Partial run
* TensorArray
* Device
* Executor
* Task
* Job


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
* What's the difference between OP and OPKernel?<br>
    A: Op is operation (like a declaration), OP Kernel is one implementation of Op. 
    See doc 'extend/adding_an_op.md'.
    
* How is an OP be invoked?
* The GraphDef is just a list of strings (see graph.proto, node_def.proto), ops and tensors are all
referred to by name (string type), then the problem is, how are those
tensors not specified by feed dict be transferred to core? e.g. constant 
tensors. <br>
    A: constant tensor is also serialized to string, as an attr 'value' of the const ops. example
    
    ```
    node {
      name: "Const"
      op: "Const"
      attr {
        key: "dtype"
        value {
          type: DT_INT32
        }
      }
      attr {
        key: "value"
        value {
          tensor {
            dtype: DT_INT32
            tensor_shape {
            }
            int_val: 1
          }
        }
      }
    }
    node {
      name: "Const_1"
      op: "Const"
      attr {
        key: "dtype"
        value {
          type: DT_INT32
        }
      }
      attr {
        key: "value"
        value {
          tensor {
            dtype: DT_INT32
            tensor_shape {
            }
            int_val: 2
          }
        }
      }
    }
    node {
      name: "add"
      op: "Add"
      input: "Const"
      input: "Const_1"
      attr {
        key: "T"
        value {
          type: DT_INT32
        }
      }
    }
    versions {
      producer: 24
    }
    ```

## module loading

when you import tensorflow in python, what happend?

1) session factories are registered<br>
2) device factories are registerd.<br>
3) ops are registered<br>

they all use the same registration mechanism: global variable's constructor.

## Create Session

devices are searched (GPU or other cards), a thread pool is created for local machine.
but more threads than the cpu cores are created, why?

* Code:
  * Python part <br>
    class diagram: SessionInterface <- BaseSession <- Session

    BaseSession.__init\__:
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
        
    * why a direct session creates more threads than the number of cpu cores?<br>
    search online, and it's said the googlers tested different configs, and the current
    number is believed the best most efficient.


## Session.Run()
* Questions

    * A fetch can be an Operation, when would this be the case? see _FetchHandler.__init\__()
    
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
            have its device specified?)
            
        * self._do_run
            * extend_graph
              serialize graph, transmit it to core via TF_ExtendGraph
            * call TF_Run<br>
              this turns to core part.
              
              note there are 2 steps, but 1 step could be enough. the comments says that if 
              new api is used, the extend-graph call is not needed.
        * build results(fetches)

    * parse run_metadata returned from core.
    * do some cleaning stuff
* core(c/c++) part
    * TF_ExtendGraph <br>
        1) parse serialized string to GraphDef, 
        2) initialize execution state. 
        code: SimpleGraphExecutionState::MakeForBaseGraph().
        the execution state will be needed at session->Run.
        this does no more than saving graph, devices, options, etc. if it's the first time
        a graph is extended. But if the session is initialized before, the graph need be 
        extended really (see SimpleGraphExecutionState::Extend), in which case, conflicts are 
        checked, new nodes are added, options, func_libs, versions are merged.
        
        It looks that the capi is rather strict on all incoming requests. outsiders are not 
        trusted generally.
        
        new execution stat are created, instead of directly modifying the old one.
        
    * TF_Run <br>
        translate input/output parameters to c++ structures, call TF_RunHelper.
    * TF_RunHelper <br>
        parse run options from buffer (buffer is owned by python)<br>
        session->Run()<br>
        serialize run-meta-data<br>
        write outputs back.<br>
    * DirectSession->Run<br>
        - get thread pool
        - get executors (DirectSession::GetOrCreateExecutors)
            - CreateGraphs (DirectSession::CreateGraphs)
              - Partition the graph across devices.
            - optimize graph
            
            direct session maintains a <key, executor> map, the key is a string, contains inputs
            /outpus/targets and other info. when an executor is wanted, this map is first searched, if 
            find none, new executor is created and added into the map. To make the 
            search faster, a cached key is used, in which case the inputs/outputs str are not sorted.
            if the cache misses, another ordinary key, which contains ordered inputs/outputs, is used.
            (of course slower because of sorting)
            
        - prepare runtime environment
            - create a call frame
            - create a RunState
            - create executor barrier
            - prepare args (Executor::Args)
        - put all executors to work <br>
        - wait for executors to finish. wait is implemented by condition variable (on posix system). <br>
        - outputs processing <br>
        - update cost model <br>
        - output partition graph <br>






    
## Device Management
## SessionFactory management
## Thread pool management
## Ops management

## some c++ libs used in TF
* c++ std
    * std::unique_ptr
    * std::initializer_list
    * std::unordered_map
    * std::move
    * std::pair
    * std::swap
    * std::vector
    * std::set_difference
    * std::set_union
    * std::inserter
* gtl
    * gtl::ArraySlice
