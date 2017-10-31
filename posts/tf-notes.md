
## Concepts
* tensor
* tensor handle
* function library<br>
  user defined functions by building a sub-graph?

* Partial run<br>
  it's just running part of the whole graph
  
* TensorArray
* Device<br>
  name scheme: /job: /task: /device: ..
* Executor<br>
  the relationship of executor and thread
* Task
* Job


    Class wrapping dynamic-sized, per-time-step, write-once Tensor arrays.
## Qestions

* What is the different between new api and old api?
* why tf starts so many threads?<br>
  gpu manager starts 2 threads.(gpu_event_mgr.cc)

* Does python client interact with C core at graph building phase?

* Why GraphDef contains a FunctionDefLibrary?
  It's experimental?

* How to generate debug version

	Add "--copt=-g" to bazel build options

    ```
    bazel build --config=opt --copt=-g //tensorflow/tools/pip\_package:build\_pip\_package
    ```

* how to open TF's log<br>
  use environment variable. set TF_CPP_MIN_VLOG_LEVEL=4<br>
  4 is the max value you can set. and TF use a strange mechanism, log print when
  the log level is less than TF_CPP_MIN_VLOG_LEVEL, otherwise it wont print.


* how to pass session config to tf.Session()?<br>
    ```
    config = tf.ConfigProto()
    config.graph_options.rewrite_options.optimize_tensor_layout=True
    config.graph_options.rewrite_options.disable_model_pruning=False
    s=tf.Session(config=config)
    ```
* how to pass options to TF's run()<br>
    ```
    options = tf.RunOptions()
    options.trace_level = tf.RunOptions.FULL_TRACE
    options.output_partition_graphs = True
    metadata = tf.RunMetadata()
    s.run(d, options=options, run_metadata=metadata)
    ```
* tensorflow's runtime architecture

    * Single machine
    * Cluster
* What's the difference between OP and OPKernel?<br>
    A: Op is operation (like a declaration), OP Kernel is one implementation of Op. 
    See doc 'extend/adding_an_op.md'.
* Why is there a sink node and a source node in a graph?
  when a graph is newed, a source(kSourceId=0) node and a sink(kSinkId=1)  node are created, 
  and a edge is added between them. (Graph::Graph). ids of these two nodes are 
  constants(0 and 1).
  
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

    * How are these factories registered?<br>
        A: they use global variable's constructor to register itself.

    * What is a tensorflow execution engine?

    * given a CAPI function name, what is the internal corresponding class/methods?<br>
        find them in capi.cc
        
    * why a direct session creates more threads than the number of cpu cores?<br>
    search online, and it's said the googlers tested different configs, and the current
    number is believed the best most efficient.


## Session.Run()
* Questions

    * A fetch can be an Operation, when would this be the case? see _FetchHandler.__init\__()
    * How is a graph be partitioned?
    * How does the cost model work?

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
        code: SimpleGraphExecutionState::MakeForBaseGraph(), ( DirectSession::MaybeInitializeExecutionState)<br>
        a new SimpleGraphExecutionState is created, 
        default attrs are attached (AddDefaultAttrsToGraphDef),<br>
        and graph is initialized (InitBaseGraph)        
            - PRE_PLACEMENT optimization, in this opt phase only ParallelConcat is removed. 
            - a SimplePlacer obj is used to assign nodes to devices
            - POST_PLACEMENT optimization
        

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
        - get thread pool<br>
          is this thread pool related to multithreadpool device?<br>
          this thread pool is created directly, has nothing to do with the multi-thread-device.
        - get executors (DirectSession::GetOrCreateExecutors)
            - CreateGraphs (DirectSession::CreateGraphs)
              - execution_state->BuildGraph (SimpleGraphExecutionState::BuildGraph)<br>
                graph is stored in execution_state.
                - OptimizeGraph<br>
                  meta optimizatoin. grappler::RunMetaOptimizer
                - RewriteGraphForExecution<br>
                (mainly for control flow?)<br>
                subgraphs needing to be run are extracted here.
                - optimize again (POST_REWRITE_FOR_EXEC)

              - Partition the graph across devices.
                - build memory & device type info for each node (graph_partition.cc)<br>
                    memories are classified as device memory and host memory. device type
                    is just a string, cpu or gpu or empty. device type is parsed
                    from assigned device full name.

                    Q: when is device assigned to each node?

                    stateful node's placement can't be changed once placed. If execution_state's placement
                    has no conflict with direct_session's,

                    Q: when is a same memory send/recv needed for a edge? (function: NeedSameDeviceSendRecv)<br>
                    A: src and dst nodes are in same device other than cpu, and their memory types
                    are different. but, when does this happen? two nodes in gpu need to send/recv?
                    
                - nodes are partitioned according to the placed device, send/recv nodes are added if needed.
                duplicated send/recv pairs are merged.
                
                graph are partitioned into a set of GraphDef.
                
               - optimize each partition

            - optimize graph
            - create one executor for each graph partition<br>
              NewLocalExecutor
            - save this new (key, executorAndKey) pair.
                        
            direct session maintains a <key, executor> map, the key is a string, contains inputs
            /outpus/targets and other info. when an executor is wanted, this map is first searched, if 
            find none, new executor is created and added into the map. To make the 
            search faster, a cached key is used, in which case the inputs/outputs str are not sorted.
            if the cache misses, another ordinary key, which contains ordered inputs/outputs, is used.
            (of course slower because of sorting)

            Executors here are just logical entities, they don't actually
            execute the computations, but prepare envrionments, parameters and
            pass these info to thread-pool, which prepares more things and delegate
            the task to devices. Executors run in main thread, operate in sub-graph(partition) level,
            thread pool run in non-main threads, operate in node/edge level, devices do the exact computation.
            
        - prepare runtime environment
            - create a call frame
            - create a RunState
            - create executor barrier
            - prepare args (Executor::Args)
        - put all executors to work <br>
            all executors use the same args.<br>
            thread pool is given to executor by args. executor calls pool->schedule
            if new task is to be executed, the very task functions is an arg to schedule.
            executor maintains a ready task list, after all dependent nodes finished the node 
            is put into ready list. An empty ready list means all task done.<br>
            Q: note that the thread-pool is used to run the task. when is GPU device be used? and how?
            who manages the threads of the pool? is it possible that a kernel uses multiple threads
            simultaneously? does executor have the knowledge of the number of threads of the pool?
            
            code: ExecutorState::Process<br>
            when the executors are created(GetOrCreateExecutors), each graph partition is bond
            with one executor, and a device is specified there. When a kernel is created, the device's
            computeAsync method is invoked with the kernel, which is done by a thread of the pool.
            
        - wait for executors to finish.<br>
          wait is implemented by condition variable (on posix system).
        - outputs processing <br>
        - update cost model <br>
        - output partition graph <br>





## Graph optimization
    
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

* eigen
    * SimpleThreadPoolTempl<br>
    when thread pool is created, all threads are started with the entry WorkerLoop, WorkerLoop
    wait for notifications and when waked up will start executing new task.

## miscs
* tf code usually returns a status code, function outputs are carried
in output parameters. a const ref (const &) is input para, an address(* arg)
is normally output para.

* memory management of tf core (c++ codes)
