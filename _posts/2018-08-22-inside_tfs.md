---
layout: post
title: "Tensorflow Serving的原理和代码实现"
date: 2018-08-22
categories: howtos
commentIssueId: 1
---


本文介绍Tensorflow Serving的原理和代码实现, 并提供简要的代码阅读指导. 

# 如何serve一个模型

具体的步骤可以参考[官方文档](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/g3doc/serving_basic.md).  主要包括两个部分：
1. 导出模型
1. 启动服务
   
需要说明的是导出模型部分. 如果要把我们训练的模型拿来提供服务, 除了模型本身外, 还需要一些额外的信息, 比如模型的名称, 输入、输出对应的tensor信息, 方法名, 这些东西可以让TFS进行请求数据的格式检查以及目标模型查找. 这就是模型导出的作用. 直接拿一个checkpoint文件之类的是不能用的. TF使用[SavedModel](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/saved_model/README.md)格式导出模型, 并提供了相关的工具(tf.saved_model.builder.SavedModelBuilder). 

# TFS的功能
- 支持多种模型服务策略,比如用最新版本/所有版本/指定版本, 以及动态策略更新、模型的增删等
- 自动加载/卸载模型
- Batching
- 多种平台支持(非TF平台)


# TFS的架构

![架构图](https://github.com/naurril/draft/blob/master/tf/tfs_arch.png)


本节简要介绍各模块的主要功能, 后续章节介绍他们相互之间是如何协作的. 

## Servable
Servable是对模型的抽象, 但是任何能够提供算法或者数据查询服务的实体都可以是Servable, 不一定是机器学习模型. 

在我们常用的场景下, Servable就是模型. 所以本文有时会混用模型和Servable. 


## ServerCore

整个服务系统的创建维护, 建立http rest server、grpc server和模型管理部分(AspiredVersionManager)之间的关系等. 

## AspiredVersionManager

模型管理的上层控制部分. 负责执行Source发出的模型管理指令. 一部分功能通过回调的方式由Source调用, 一部分由独立线程执行. 


## BasicManager
负责Servable的管理, 包括加载、卸载、状态查询、资源跟踪等, 对外提供如下接口操作Servable
- ManageServable
- LoadServable
- UnloadServable
- StopManagerServable

另外提供接口查询servableHandle(GetUntypedServableHandle), 也就是加载好的模型,供http rest或者grpc server调用进行推理. 

所有受管理的servable都放在ManagedMap里面, 已经正常加载的servable同时也放在ServingMap里进行管理, 提供查询接口. 

## LoaderHarness

LoaderHarness对Loader提供状态跟踪, ServingMap和ManagedMap里面保存的都是LoaderHarness对象,只有通过LoaderHarness才能访问Loader的接口. 

## Loader
Loader对Servable的生命周期进行控制, 包括load/unload接口,资源预估接口等. 加载之后的Servable也存在Loader里面. 

## Adapter

Adapter是为了将Source(比如文件系统)转换成Loader而引入的抽象, 这样server core的实现和具体的平台解耦. 

## SourceRouter
Adapter是平台相关的, 每个平台一个Adapter, 但是Source是和Servable相关的, 这样在Adapter和Source之间存在一对多的关系, Router负责维护这些对应关系. 

## Source
Source是对Servable的来源(Source)的抽象, 比如模型文件是某个模型的Source. Source监控外部的资源（如文件系统）, 发现新的模型版本, 并通知Target. 

## Target
Target是和Source对应的抽象概念, AspiredVersionManager、Router都是Target. 


# 启动过程
TFS启动的全部参数可以参考[main.c](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/model_servers/main.cc).  主要的参数包括服务端口（gprc和http rest端口）和模型配置. 其中模型配置可以直接指定（名称（model_name）、路径（model_base_path）等）, 也可以使用文件指定（model_config_file,格式参考[model_server_config.proto](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/config/model_server_config.proto)）. 如果只启动单个模型的服务可以使用参数指定, 如果是多个模型必须使用文件. 其他的参数可以使用默认值. 

启动过程主要是创建ServerCore对象, 并启动grpc server和http server. 

ServerCore对象可以认为是系统中枢, 模型的维护, 服务请求的处理都是由他完成. ServerCore通过BasicManager管理所有的model(多版本号), 并查处模型已经提供预测、分类、回归请求. 

ServerCore启动的时候创建AspiredVersionManager, AspiredVersionManager会启动定时任务(线程), 用于处理AspiredVersionRequest消息, 其实就是模型的加载、卸载. 

启动的时候ServerCore还会根据模型配置创建文件系统扫描任务, 定时扫描模型文件目录并进行相应的处理


http rest服务启动后, 会监听http post请求, 将请求（json）转换成protobuf格式的消息, 通过serverCore查找对应的模型版本, 获取对应的已加载的模型, 进行运算并返回结果. 

rgpc服务与 http rest服务类似（待补充),不过目前看起来是Sync方式进行处理. 

# 模型维护

## 文件系统扫描
Source是TFS定义的对未加载模型对象的抽象, 目前实现了两种Source, 一种是StaticStoragePathSource,一种是FileSystemStoragePathSource. 前者是简单的静态的模型文件存储系统, 仅仅在启动时触发模型的加载, 没有其他动作. 后者是动态的Source, 能监测存储系统的变化并发出通知. 

TFS实现Source时将模块职责划分的很清晰, Source的职责就是监测变化, 如何处理则由Source的用户决定, 所以Source有一个接口SetAspiredVersionsCallback, 可以设置回调函数用于通知AspiredVersion的变化. Source在变化的时候就会调用设置的回调函数. 


作为Source的对等对象, 系统也定义了Target, 有接口GetAspiredVersionsCallback, 用于获取处理AspiredVersions的回调接口, 然后我们就可以将Target和Source连起来了. 

```
template <typename T>
void ConnectSourceToTarget(Source<T>* source, Target<T>* target) {
  source->SetAspiredVersionsCallback(target->GetAspiredVersionsCallback());
}
```

Source和ServerCore的关系是这样的

```
Source --> Router --> Adapter --> AspiredVersionManager
```

上述连接关系里面, Router和Adapter既是Source又是Target, AspiredVersionManager是Target. 但是Router没有实现Source接口, 而是要求在创建Router对象时直接将Adapter作为参数, 这样实现主要目的是创建一对多的关系. 

系统根据所支持平台的个数（tensorflow算是一种平台）创建Adapter, 一种平台对应一个Adapter, 负责创建模型加载器Loader. 对于tensorflow平台, 对应的adapter是[SavedModelBundleSourceAdapter](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/servables/tensorflow/saved_model_bundle_source_adapter.h).

Router负责根据模型名称查找对应的平台([model_config](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/config/model_server_config.proto)里面有指定平台名称), 从而定位到对应的Adapter. 

这些连接关系是在系统启动, 或者更新model-config的时候建立的. 


默认配置下, FileSystemStoragePathSource为Source的实例, SavedModelBundleSourceAdapter为Adapter的实例, DynamicSourceRouter为Router的实例. 

1. FileSystemStoragePathSource有自己单独的工作线程, 周期查询文件系统, 发现每个模型的版本, 根据指定的servable_version_policy([model_config](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/config/model_server_config.proto)), 创建ServableData(模型名, 版本号, 路径),  传给Router
2. Router根据路由找到对应的adapter, 传给Adataper
3. Adapter将ServableData(模型名,  版本号, 路径)转换成ServableData(模型名, 版本, Loader), 传给AspiredVersionManager
4. AspiredVersionManager将这些信息存到pending_aspired_versions_requests_, 等待另外一个工作线程(AspiredVersionsManager_ManageState_Thread)处理

上述消息传递的方式是依次调用下游的SetAspiredVersions函数. 


## 模型加载/卸载

上节提到的工作线程ManageState_Thread是在AspiredVersionsManager创建的时候启动的定时线程, 负责处理pending_aspired_versions_requests_里面的ServableData. 

```
manage_state_thread_.reset(new PeriodicFunction(
        [this]() {
          this->FlushServables();
          this->HandlePendingAspiredVersionsRequests();
          this->InvokePolicyAndExecuteAction();
        },
        manage_state_interval_micros));
```

该线程的工作分3部分, 如上述代码所示

1. FlushServables主要目的是将异常状态的模型清理掉, 或者停止加载. 
   
1. HandlePendingAspiredVersionsRequests取出每个模型的信息分别处理, 如果发现当前要加载的模型版本已经存在, 需要等待之前的模型完成服务并退出, 这叫re-aspired version. 如果不是这种情况, 计算需要加载的模型和需要卸载的模型, 将新加载的模型管理起来（加到管理列表）,将需要卸载的模型打上标记并停止其加载. 
   
1. InvokePolicyAndExecuteAction每次只会执行一个模型的一个动作（load/unload). 具体方法是每个模型根据aspired_version_policy（AvailabilityPreservingPolicy/ResourcePreservingPolicy）选择一个动作, 然后所有模型的选择动作放在一起排序, unload优先load, 决定处理哪一个模型. 执行动作的时候, 会调用Loader的相应函数, 并设置相关的状态(参考模型状态管理). 

可以看出ManageState_Thread并不是一股脑的进行模型的加载、卸载等操作, 而是兼顾了资源占用、服务可用性、系统负荷的, 考虑周到. 

## 模型管理
AspiredVersionManager的成员BasicManager负责模型管理, 把一个模型版本加入到BasicManager里面就叫管理一个模型(manager a model). BasicManager通过LoaderHarness间接管理模型, LoaderHarness管理一个模型的生命周期, 持有模型的Loader对象, 在合适的时候调用Loader的Load/Unload完成状态迁移. 

LoaderHarness有自己的[状态](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/core/loader_harness.h)记录, 每次执行动作时都会进行状态迁移. 

进行模型状态管理的同时, BasicManager还会将模型的[服务状态](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/core/servable_state.h)发布到EventBus(servable_event_bus_), 便于其他模块对这些状态变化进行订阅. 

## 快速模型加载
首次启动的时候, 采用快速加载模式, 实现方法是临时增加模型加载线程（4倍可用cpu个数）. 完成加载后恢复线程数. 
[代码](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/model_servers/server_core.h)
```
    // The number of load threads used to load the initial set of models at
    // server startup. This is set high to load up the initial set of models
    // fast, after this the server uses num_load_threads.
    int32 num_initial_load_threads = 4.0 * port::NumSchedulableCPUs();
```

## Aspired version policy

AspiredVersionPolicy是用来决定一个模型的多个版本谁先处理, [AvailabilityPreservingPolicy](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/core/availability_preserving_policy.h)的目标是保证服务可用, 会临时牺牲一些资源, 而
[ResourcePreservingPolicy](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/core/resource_preserving_policy.h)是优先保证占用更少的资源, 可能会牺牲服务可用性. 

代码里面的注释提供了很好的解释, 可参考. 

## Servable Version Policy
[ServableVersionPolicy](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/sources/storage_path/file_system_storage_path_source.proto)
定义了模型的多个版本如何进行选择. 注意和Aspired Version Policy的关系, 一个是如何选择版本, 一个是选择了版本后, 如何选择执行先后顺序. 

目前提供3种方式：
 - all      所有的版本
 - latest   最新的N个版本
 - specific 一个或一些指定的版本号

## 模型配置动态更新

tfs的main默认并没有提供模型配置文件的动态更新, 但是调用```ServerCore::ReloadConfig(const ModelServerConfig& new_config)```就可以完成更新. 可以自己包装该接口在合适的时间进行调用. 

动态更新可以增加、删除模型, 修改版本策略（比如从最新版本到指定某版本）等. 

动态更新的实现也不复杂, 更新Router的路由策略, 更新Source就可以了. 代码实现可以参考```ServerCore::AddModelsViaModelConfigList```

TFS目前还不支持动态增加平台. 



# Batching
Batching是提高服务性能的一个有效办法, 最简单的batching就是把多个单独请求打包到一起, 由TF Session一次运算得出结果. 

Batching的参数参考
[session_bundle_config](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/servables/tensorflow/session_bundle_config.proto)

Batching的实现就是在普通的Tensorflow Session之外包装一个BatchingSession，负责缓存、调度. 参考代码```SavedModelBundleFactory::Create```. Batching分两个部分实现，BatchScheduler和BatchingSession.

BatchingSession对外提供Run和ListDevices接口. 有Run请求的时候, 将请求打包成一个BatchTask，交给BatchScheduler去处理，并等待处理结束，取出结果返回.

BatchScheduler是一个底层的调度器，拥有自己的线程池, 负责将多个BatchTask合并处理. 

[代码](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/batching/batching_session.h)

# Model Warmup

模型加载后，如果需要Warmup，从模型文件目录中取出预先存好的请求数据，调用模型进行推理，如此可以将模型"热身"，避免首次处理服务请求时时延过大。

# 配置

## 平台配置
参考[platform_config.proto](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/config/platform_config.proto), 
[session_bundle_config](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/servables/tensorflow/session_bundle_config.proto), 
主要包括如下配置:
- 平台名, 如tensorflow
- 平台配置
   - sessoin target
     
     如果需要使用分布式TF服务器, 可以在这里指定. 默认情况下使用本地Session(DirectSession)
   - Session 参数
- Batching参数

## 模型配置
参考[model_server_config.proto](https://github.com/tensorflow/serving/blob/master/tensorflow_serving/config/model_server_config.proto)
主要包括:
- 模型名
- 模型根路径
- 平台名
- 版本策略


# 与Tensorflow的关系
TFS对TF是源代码级别的依赖, 两者的版本号保持一致, TFS在加载模型、执行推理的过程中, 都是调用TF的库. TFS使用的很多基本构件, 比如多线程库/BatchScheduler, 都是直接使用TF的代码. 

# 性能
TFS在如下方面做出了性能提升的设计：
- Batching
- Fast Model Loading
- Model Warmup
- Availability/Resource Proserving Policy
